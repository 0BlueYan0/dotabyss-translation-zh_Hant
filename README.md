# dotabyss-translation-zh_Hant

Traditional Chinese (Taiwan) translation files for Dot Abyss, converted from the Simplified Chinese translation at [anosu/dotabyss-translation](https://github.com/anosu/dotabyss-translation). Upstream changes are picked up within an hour.

## Use with AbyssMod (PC)

Set these two values in the [AbyssMod](https://github.com/anosu/AbyssMod) config, under `[Translation]`, then restart the game:

| Key | Value |
|---|---|
| `CDN` | `https://raw.githubusercontent.com/0BlueYan0/dotabyss-translation-zh_Hant/refs/heads/main/translations` |
| `Language` | `zh_Hant` |

## Wrong conversions

The text is converted with [OpenCC](https://github.com/BYVoid/OpenCC) (`s2twp`). Some words come out wrong in this game's context, for example 搬運行李 turning into 搬執行李. Corrections live in two tables:

- `overrides.tsv` keeps a word out of OpenCC's Taiwan vocabulary swap, or swaps it for a different word.
- `fixes.tsv` corrects the converted text directly. It catches character errors such as 不斷髮出 → 不斷發出.

Found another one? Open an issue with the wrong text and where it shows up in game, or send a pull request that adds a row.

The button images in `translations/replacements/` are maintained by hand and are not converted.

## Credits

All translations are by the contributors of [anosu/dotabyss-translation](https://github.com/anosu/dotabyss-translation). This repository only converts the script.
