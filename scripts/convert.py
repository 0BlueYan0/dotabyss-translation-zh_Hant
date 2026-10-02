"""Convert the upstream zh_Hans translation files into zh_Hant.

Only string values are converted. Keys are the Japanese source strings the mod
matches against, so changing them would break every lookup.
"""

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

import opencc

SRC_LANG = "zh_Hans"
DST_LANG = "zh_Hant"
# manifest is rebuilt from the converted files, replacements holds hand-edited images.
SKIP_DIRS = {"manifest", "replacements"}


def read_tsv(path: Path) -> list[tuple[str, str]]:
    """Read `from<TAB>to<TAB>note` rows, skipping blank and # lines."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        rows.append((cols[0], cols[1]))
    return rows


def build_config(overrides: list[tuple[str, str]], workdir: Path) -> Path:
    """s2twp with the override table placed ahead of OpenCC's Taiwan phrase table.

    The stock s2twp swaps in computing vocabulary wherever the characters line up,
    e.g. 搬運行李 becomes 搬執行李. Entries in the override table win over the
    stock table for the same span, so a word mapped to itself is left alone.
    """
    share = Path(opencc.__file__).parent / "clib" / "share" / "opencc"

    def ocd2(name):
        return {"type": "ocd2", "file": str(share / name)}

    table = workdir / "overrides.txt"
    table.write_text("".join(f"{k}\t{v}\n" for k, v in overrides), encoding="utf-8")
    config = {
        "name": "s2twp with overrides",
        "segmentation": {"type": "mmseg", "dict": ocd2("STPhrases.ocd2")},
        "conversion_chain": [
            {"dict": {"type": "group", "dicts": [ocd2("STPhrases.ocd2"), ocd2("STCharacters.ocd2")]}},
            {"dict": {"type": "group", "dicts": [{"type": "text", "file": str(table)}, ocd2("TWPhrases.ocd2")]}},
            {"dict": ocd2("TWVariants.ocd2")},
        ],
    }
    path = workdir / "s2twp-overrides.json"
    path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    return path


class Converter:
    def __init__(self, config: Path, fixes: list[tuple[str, str]]):
        self.cc = opencc.OpenCC(str(config))
        # One pass, longest key first, so a longer row can shield a span from a
        # shorter one: 開口回覆 -> 開口回覆 keeps the reply while 回覆 -> 回復 fixes HP text.
        self.fixes = dict(fixes)
        keys = sorted(self.fixes, key=len, reverse=True)
        self.pattern = re.compile("|".join(map(re.escape, keys))) if keys else None

    def text(self, value: str) -> str:
        out = self.cc.convert(value)
        if self.pattern:
            out = self.pattern.sub(lambda m: self.fixes[m.group(0)], out)
        return out

    def tree(self, node):
        if isinstance(node, dict):
            return {k: self.tree(v) for k, v in node.items()}
        if isinstance(node, list):
            return [self.tree(v) for v in node]
        if isinstance(node, str):
            return self.text(node)
        return node


def indent_of(raw: str) -> int:
    lines = raw.split("\n", 2)
    if len(lines) < 2:
        return 4
    second = lines[1]
    return (len(second) - len(second.lstrip(" "))) or 4


def source_files(src: Path):
    for path in sorted(src.rglob(f"{SRC_LANG}.json")):
        if path.relative_to(src).parts[0] not in SKIP_DIRS:
            yield path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="upstream translations directory")
    parser.add_argument("--dst", default="translations")
    parser.add_argument("--overrides", default="overrides.tsv")
    parser.add_argument("--fixes", default="fixes.tsv")
    args = parser.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    workdir = Path(tempfile.mkdtemp())
    config = build_config(read_tsv(Path(args.overrides)), workdir)
    conv = Converter(config, read_tsv(Path(args.fixes)))

    wanted = set()
    for path in source_files(src):
        rel = path.relative_to(src).with_name(f"{DST_LANG}.json")
        wanted.add(rel)
        raw = path.read_text(encoding="utf-8")
        out = json.dumps(conv.tree(json.loads(raw)), ensure_ascii=False, indent=indent_of(raw))
        if raw.endswith("\n"):
            out += "\n"
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text(encoding="utf-8") != out:
            target.write_text(out, encoding="utf-8", newline="\n")

    # Drop files whose upstream source was removed.
    removed = 0
    for path in dst.rglob(f"{DST_LANG}.json"):
        rel = path.relative_to(dst)
        if rel.parts[0] in SKIP_DIRS or rel in wanted:
            continue
        path.unlink()
        removed += 1
        if path.parent != dst and not any(path.parent.iterdir()):
            path.parent.rmdir()

    # Images are copied once and then edited by hand, so never overwrite them.
    if not (dst / "replacements").exists() and (src / "replacements").exists():
        shutil.copytree(src / "replacements", dst / "replacements")

    print(f"converted {len(wanted)} files, removed {removed}")


if __name__ == "__main__":
    main()
