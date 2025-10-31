# ClanGen - Export Moon Events

A fork of [ClanGen](https://github.com/ClanGenOfficial/clangen) with moon event export functionality. Updated to latest Development branch.

## What is this?
Ever spent three hours in ClanGen chaos only to realize you can’t remember why Mousepaw hates Flowertail or how your deputy survived getting hit by a monster three separate times? Yeah, same.
This mod quietly logs every moon’s drama into tidy little text files, so you don’t have to. It’s basically a secret diary for your Clan—except they have no idea they’re being documented.

Great for:
- Writing fanfic without scrambling for screenshots
- Actually remembering the plot when you start that comic
- Proving your deputy is, in fact, immortal
- Finally making sense of what happened last session

## Features

### Event Export System
- Per-clan toggle for independent control
- Events organized into 10 categories
  - patrols, ceremonies, births/deaths, health, relationships (positive/negative), other clans, miscellaneous, herbs, freshkill, name changes
- Complete patrol stories with intro and outcome combined
- Choice indicators show player decisions: [PROCEED], [ANTAGONIZE], or [DECLINED]
- Output to individual plain text files

### Optional Additions
- Full clan member information with personality, skills, family, and health info
- Moon statistics: births, deaths, joins, health summary

## Installation

1. Download or clone this repository
2. Install dependencies (see ClanGen documentation)
3. Run the game via the run.bat file
4. Enable export in Clan Settings

## How to Use

### Enable Exports
1. Launch the game and load a clan
2. Click **Clan Settings** (paw icon in menu)
3. Go to **General Settings**
4. Toggle **"Export events each moon"** to ON
5. (Optional) Enable **"Include full cat details"** and/or **"Include clan stats"**

### Find Your Exports
After each moon, your exports are saved to:
```
saves/<YourClanName>/event_logs/moon_XXXX.txt
```

## Modified Files

This fork modifies 7 game files:
- `resources/clansettings.json` - Export settings
- `resources/gamesettings.json` - Removed old global setting
- `resources/lang/en/settings.en.json` - UI text
- `scripts/events.py` - Export trigger
- `scripts/game_structure/game/__init__.py` - Export function
- `scripts/game_structure/windows.py` - Name change logging
- `scripts/events_module/patrol/patrol.py` - Patrol combination

## Version

**Moon Event Export Mod v1.2**
- Base Game: ClanGen development build (2024-2025)
- Last Updated: October 31, 2025

## Changelog

### v1.2
- Patrol intro and outcome combined
- Relationships split into positive/negative
- Experience displays as number and text
- Simplified formatting

### v1.1
- Per-clan settings instead of global
- Optional detailed cat roster
- Optional clan statistics
- Name change logging

### v1.0
- Basic event export

## Compatibility

**Incompatible with mods that modify:**
- `resources/clansettings.json`
- `resources/gamesettings.json`
- `resources/lang/en/settings.en.json`
- `scripts/events.py`
- `scripts/game_structure/game/__init__.py`
- `scripts/game_structure/windows.py`
- `scripts/events_module/patrol/patrol.py`

## Credits

Original game: [ClanGen](https://github.com/ClanGenOfficial/clangen) by the ClanGen development team

Moon Event Export Mod: Community contribution

License: Same as ClanGen
