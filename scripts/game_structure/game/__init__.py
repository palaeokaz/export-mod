from typing import Optional, TYPE_CHECKING, Any

import pygame
import ujson

from scripts.event_class import Single_Event
from scripts.housekeeping.datadir import get_save_dir

from scripts.game_structure import constants
from scripts.game_structure.screen_settings import toggle_fullscreen

from . import save_load, settings, switches

from .save_load import safe_save
from .settings import game_setting_get
from .switches import switch_get_value, Switch
from ...screens.enums import GameScreen
from ...cat.enums import CatGroup

pygame.init()

if TYPE_CHECKING:
    from scripts.clan import Clan


event_editing = False
max_name_length = 10

mediated = []  # Keep track of which couples have been mediated this moon.
just_died = []  # keeps track of which cats died this moon via die()

cur_events_list = []
ceremony_events_list = []
birth_death_events_list = []
relation_events_list = []
health_events_list = []
other_clans_events_list = []
misc_events_list = []
herb_events_list = []
freshkill_event_list = []

# Keeping track of various last screen for various purposes
last_screen_forupdate = GameScreen.START
last_screen_forProfile = GameScreen.LIST
last_list_forProfile = None

choose_cats = {}

"""cat_buttons = {
    'cat0': None,
    'cat1': None,
    'cat2': None,
    'cat3': None,
    'cat4': None,
    'cat5': None,
    'cat6': None,
    'cat7': None,
    'cat8': None,
    'cat9': None,
    'cat10': None,
    'cat11': None
}"""

patrol_cats = {}
patrolled = []

used_group_IDs: dict = {
    CatGroup.PLAYER_CLAN_ID: CatGroup.PLAYER_CLAN,
    CatGroup.STARCLAN_ID: CatGroup.STARCLAN,
    CatGroup.UNKNOWN_RESIDENCE_ID: CatGroup.UNKNOWN_RESIDENCE,
    CatGroup.DARK_FOREST_ID: CatGroup.DARK_FOREST,
}
"""Int IDs already in use. Key is the group ID, value is the group type."""

# store changing parts of the game that the user can toggle with buttons

all_screens = {}

debug_settings = {
    "showcoords": False,
    "showbounds": False,
    "visualdebugmode": False,
    "showfps": False,
}

# CLAN
clan: Optional["Clan"] = None
cat_class = None
with open(f"resources/prey_config.json", "r", encoding="utf-8") as read_file:
    prey_config = ujson.loads(read_file.read())

rpc = None

is_close_menu_open = False


current_screen = GameScreen.START
clicked = False
keyspressed = []
switch_screens = False

"""
To give us the deprecation warnings/errors
"""


def __getattr__(attr):
    import warnings

    if attr == "config":
        warnings.warn("Use constants.CONFIG instead", DeprecationWarning, 2)
        return constants.CONFIG
    elif attr == "switches":
        # unfortunately there's no way to let this one fix itself, so we have to CTD.
        warnings.warn(
            "Use get_switch(), set_switch(), or helpers instead", DeprecationWarning, 2
        )
        raise Exception(
            "game.switches has been deprecated; use get_switch(), set_switch(), or helpers instead. Unrecoverable."
        )
    elif attr == "settings":
        warnings.warn(
            "Use get_game_setting() and set_game_setting() or helpers instead. WILL CRASH if you try and use this anyway.",
            DeprecationWarning,
            2,
        )
        raise Exception(
            "game.settings has been deprecated, use get_game_setting() and set_game_setting() or helpers instead. Unrecoverable."
        )
    else:
        raise AttributeError(f"module '{__name__}' object has no attribute '{attr}'")


"""
DEPRECATED: use constants.CONFIG instead
"""
config: Any

"""
DEPRECATED: use get_switch(), set_switch(), or helpers instead - WILL CRASH if you try and use this anyway
"""
switches: Any

"""
DEPRECATED: use get_game_setting() and set_game_setting() or helpers instead.
WILL CRASH if you try and use this anyway.
"""
settings: Any

del read_file  # cleanup from load


def update_game():
    global current_screen, switch_screens, clicked, keyspressed

    if current_screen != switch_get_value(Switch.cur_screen):
        current_screen = switch_get_value(Switch.cur_screen)
        switch_screens = True
    clicked = False
    keyspressed = []


def save_events():
    """
    Save current events list to events.json
    """
    events_list = []
    for event in cur_events_list:
        events_list.append(event.to_dict())
    safe_save(f"{get_save_dir()}/{clan.name}/events.json", events_list)


def export_current_moon_events():
    """
    Export all events for the current moon into a readable text file under the clan's event_logs folder.
    Includes patrol logs, ceremonies, interactions, herb logs, and freshkill logs organized by category.
    """
    if not clan:
        return

    from scripts.clan_package.settings import get_clan_setting
    from scripts.cat.cats import Cat
    from scripts.cat.enums import CatRank

    def clean_text(text):
        """Remove HTML/formatting tags from text."""
        import re
        text = re.sub(r'<[^>]+>', '', str(text))
        return text


    patrols = []
    ceremonies = []
    births_deaths = []
    health_events = []
    positive_relations = []
    negative_relations = []
    other_clan_events = []
    misc_events = []
    
    for event in cur_events_list:
        event_types = event.types if hasattr(event, 'types') and event.types else []
        event_text = event.text if hasattr(event, 'text') else str(event)
        event_text = clean_text(event_text)
        
        if "patrol" in event_types:
            patrols.append(event_text)
        elif "ceremony" in event_types:
            ceremonies.append(event_text)
        elif "birth_death" in event_types:
            births_deaths.append(event_text)
        elif "health" in event_types:
            health_events.append(event_text)
        elif "relation" in event_types:
            lower_text = event_text.lower()
            if "negative effect" in lower_text:
                negative_relations.append(event_text)
            elif "positive effect" in lower_text:
                positive_relations.append(event_text)
            else:
                positive_relations.append(event_text)
        elif "other_clans" in event_types:
            other_clan_events.append(event_text)
        else:
            misc_events.append(event_text)
    
    lines = []
    lines.append(f"╔═══════════════════════════════════════════════════════════════════════════════╗")
    lines.append(f"║  {clan.name}Clan - Moon {clan.age}")
    if hasattr(clan, "current_season"):
        lines.append(f"║  Season: {clan.current_season}")
    biome = str(clan.override_biome) if getattr(clan, "override_biome", None) else str(getattr(clan, "biome", ""))
    if biome:
        lines.append(f"║  Biome: {biome}")
    lines.append(f"╚═══════════════════════════════════════════════════════════════════════════════╝")
    lines.append("")
    
    if patrols:
        lines.append("─" * 80)
        lines.append("PATROLS")
        lines.append("─" * 80)
        for i, patrol in enumerate(patrols, 1):
            lines.append(f"  {i}. {patrol}")
            if i < len(patrols):
                lines.append("")
        lines.append("")
    
    if ceremonies:
        lines.append("─" * 80)
        lines.append("CEREMONIES")
        lines.append("─" * 80)
        for ceremony in ceremonies:
            lines.append(f"  • {ceremony}")
        lines.append("")
    
    if births_deaths:
        lines.append("─" * 80)
        lines.append("BIRTHS & DEATHS")
        lines.append("─" * 80)
        for event in births_deaths:
            lines.append(f"  • {event}")
        lines.append("")
    
    if health_events:
        lines.append("─" * 80)
        lines.append("HEALTH & INJURIES")
        lines.append("─" * 80)
        for event in health_events:
            lines.append(f"  • {event}")
        lines.append("")
    
    if positive_relations:
        lines.append("─" * 80)
        lines.append("RELATIONSHIPS - POSITIVE")
        lines.append("─" * 80)
        for event in positive_relations:
            lines.append(f"  • {event}")
        lines.append("")
    
    if negative_relations:
        lines.append("─" * 80)
        lines.append("RELATIONSHIPS - NEGATIVE")
        lines.append("─" * 80)
        for event in negative_relations:
            lines.append(f"  • {event}")
        lines.append("")
    
    if other_clan_events:
        lines.append("─" * 80)
        lines.append("OTHER CLANS")
        lines.append("─" * 80)
        for event in other_clan_events:
            lines.append(f"  • {event}")
        lines.append("")
    
    if misc_events:
        lines.append("─" * 80)
        lines.append("OTHER EVENTS")
        lines.append("─" * 80)
        for event in misc_events:
            lines.append(f"  • {event}")
        lines.append("")
    
    if herb_events_list:
        lines.append("─" * 80)
        lines.append("HERB GATHERING")
        lines.append("─" * 80)
        for herb in herb_events_list:
            lines.append(f"  • {clean_text(herb)}")
        lines.append("")
    
    if freshkill_event_list:
        lines.append("─" * 80)
        lines.append("FRESH-KILL PILE")
        lines.append("─" * 80)
        for prey in freshkill_event_list:
            lines.append(f"  • {clean_text(prey)}")
        lines.append("")
    
    try:
        if get_clan_setting("export cat details"):
            lines.append("")
            lines.append("─" * 80)
            lines.append("CLAN MEMBERS (DETAILED)")
            lines.append("─" * 80)
            lines.append("")
            
            living_cats = []
            for cat in Cat.all_cats.values():
                if not cat.status.alive_in_player_clan:
                    continue
                living_cats.append(cat)
            
            rank_order = {
                CatRank.LEADER: 0,
                CatRank.DEPUTY: 1,
                CatRank.MEDICINE_CAT: 2,
                CatRank.MEDIATOR: 3,
                CatRank.WARRIOR: 4,
                CatRank.APPRENTICE: 5,
                CatRank.MEDICINE_APPRENTICE: 6,
                CatRank.MEDIATOR_APPRENTICE: 7,
                CatRank.KITTEN: 8,
                CatRank.NEWBORN: 9,
                CatRank.ELDER: 10
            }
            living_cats.sort(key=lambda c: (rank_order.get(c.status.rank, 99), str(c.name)))
            
            for cat in living_cats:
                lines.append(f"{cat.name} ({cat.moons} moons) - {cat.status.rank.name.replace('_', ' ').upper()}")
                
                lines.append(f"  Gender: {cat.gender}")
                if hasattr(cat, 'genderalign') and cat.genderalign:
                    lines.append(f"  Gender Identity: {cat.genderalign}")
                
                if hasattr(cat, 'personality') and cat.personality:
                    lines.append(f"  Personality: {cat.personality.trait}")
                if hasattr(cat, 'skills') and cat.skills:
                    skill_str = cat.skills.skill_string() if hasattr(cat.skills, 'skill_string') else "Unknown"
                    lines.append(f"  Skill: {skill_str}")
                if hasattr(cat, 'experience') and cat.experience is not None and hasattr(cat, 'experience_level') and cat.experience_level:
                    lines.append(f"  Experience: {cat.experience} ({cat.experience_level})")
                elif hasattr(cat, 'experience') and cat.experience is not None:
                    lines.append(f"  Experience: {cat.experience}")
                elif hasattr(cat, 'experience_level') and cat.experience_level:
                    lines.append(f"  Experience: {cat.experience_level}")
                
                if cat.mate:
                    mate_names = []
                    for mate_id in cat.mate:
                        mate_cat = Cat.fetch_cat(mate_id)
                        if mate_cat:
                            mate_names.append(str(mate_cat.name))
                    if mate_names:
                        lines.append(f"  Mate(s): {', '.join(mate_names)}")
                
                parents = []
                if cat.parent1:
                    parent1 = Cat.fetch_cat(cat.parent1)
                    if parent1:
                        parents.append(str(parent1.name))
                if cat.parent2:
                    parent2 = Cat.fetch_cat(cat.parent2)
                    if parent2:
                        parents.append(str(parent2.name))
                if parents:
                    lines.append(f"  Parents: {' & '.join(parents)}")
                
                kittens_list = cat.get_children() if hasattr(cat, 'get_children') else []
                if kittens_list:
                    kitten_names = []
                    for kit_id in kittens_list:
                        kit = Cat.fetch_cat(kit_id)
                        if kit and not kit.dead:
                            kitten_names.append(str(kit.name))
                    if kitten_names:
                        lines.append(f"  Kittens: {', '.join(kitten_names[:5])}")
                        if len(kitten_names) > 5:
                            lines.append(f"    ... and {len(kitten_names) - 5} more")
                
                if cat.mentor:
                    mentor = Cat.fetch_cat(cat.mentor)
                    if mentor:
                        lines.append(f"  Mentor: {mentor.name}")
                if cat.apprentice:
                    app_names = []
                    for app_id in cat.apprentice:
                        app = Cat.fetch_cat(app_id)
                        if app:
                            app_names.append(str(app.name))
                    if app_names:
                        lines.append(f"  Apprentice(s): {', '.join(app_names)}")
                
                # Health
                health_issues = []
                if cat.injuries:
                    for injury in cat.injuries.values():
                        if hasattr(injury, 'name'):
                            health_issues.append(f"Injury: {injury.name}")
                if cat.illnesses:
                    for illness in cat.illnesses.values():
                        if hasattr(illness, 'name'):
                            health_issues.append(f"Illness: {illness.name}")
                if cat.permanent_condition:
                    for condition in cat.permanent_condition.values():
                        if hasattr(condition, 'name'):
                            health_issues.append(f"Condition: {condition.name}")
                
                if health_issues:
                    lines.append(f"  Health: {', '.join(health_issues)}")
                else:
                    lines.append("  Health: Healthy")
                
                lines.append("")
            
            lines.append(f"Total Clan Members: {len(living_cats)}")
            
        else:
            leaders = []
            deputies = []
            medicine_cats = []
            mediators = []
            warriors = []
            apprentices = []
            medicine_apprentices = []
            mediator_apprentices = []
            kittens = []
            elders = []
            
            for cat in Cat.all_cats.values():
                if not cat.status.alive_in_player_clan:
                    continue
                    
                cat_name = str(cat.name)
                cat_age = cat.moons
                
                if cat.status.rank == CatRank.LEADER:
                    leaders.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.DEPUTY:
                    deputies.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.MEDICINE_CAT:
                    medicine_cats.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.MEDIATOR:
                    mediators.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.WARRIOR:
                    warriors.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.APPRENTICE:
                    apprentices.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.MEDICINE_APPRENTICE:
                    medicine_apprentices.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.MEDIATOR_APPRENTICE:
                    mediator_apprentices.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank in (CatRank.KITTEN, CatRank.NEWBORN):
                    kittens.append(f"{cat_name} ({cat_age} moons)")
                elif cat.status.rank == CatRank.ELDER:
                    elders.append(f"{cat_name} ({cat_age} moons)")
            
            lines.append("CLAN MEMBERS")
            lines.append("─" * 80)
            lines.append("")
            if leaders:
                lines.append("Leader:")
                for cat in leaders:
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if deputies:
                lines.append("Deputy:")
                for cat in deputies:
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if medicine_cats:
                lines.append("Medicine Cats:")
                for cat in medicine_cats:
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if mediators:
                lines.append("Mediators:")
                for cat in mediators:
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if warriors:
                lines.append(f"Warriors ({len(warriors)}):")
                for cat in sorted(warriors):
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if apprentices:
                lines.append(f"Apprentices ({len(apprentices)}):")
                for cat in sorted(apprentices):
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if medicine_apprentices:
                lines.append("Medicine Cat Apprentices:")
                for cat in medicine_apprentices:
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if mediator_apprentices:
                lines.append("Mediator Apprentices:")
                for cat in mediator_apprentices:
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if kittens:
                lines.append(f"Kittens ({len(kittens)}):")
                for cat in sorted(kittens):
                    lines.append(f"  • {cat}")
                lines.append("")
            
            if elders:
                lines.append(f"Elders ({len(elders)}):")
                for cat in sorted(elders):
                    lines.append(f"  • {cat}")
                lines.append("")
            
            # Total count
            total_cats = len(leaders) + len(deputies) + len(medicine_cats) + len(mediators) + \
                         len(warriors) + len(apprentices) + len(medicine_apprentices) + \
                         len(mediator_apprentices) + len(kittens) + len(elders)
            lines.append(f"Total Clan Members: {total_cats}")
        
    except Exception as e:
        print(f"Error adding clan roster to export: {e}")
    
    if get_clan_setting("export clan stats"):
        try:
            lines.append("")
            lines.append("─" * 80)
            lines.append("CLAN STATISTICS")
            lines.append("─" * 80)
            lines.append("")
            
            births_count = len([e for e in births_deaths if "born" in e.lower() or "kit" in e.lower()])
            deaths_count = len([e for e in births_deaths if "died" in e.lower() or "death" in e.lower()])
            joins_count = len([e for e in misc_events if "joined" in e.lower() or "join" in e.lower()])
            
            lines.append("THIS MOON:")
            lines.append(f"  Births: {births_count}")
            lines.append(f"  Deaths: {deaths_count}")
            lines.append(f"  Joined: {joins_count}")
            lines.append("")
            
            healthy_count = 0
            injured_count = 0
            ill_count = 0
            permanent_conditions = 0
            
            for cat in Cat.all_cats.values():
                if not cat.status.alive_in_player_clan:
                    continue
                
                if cat.injuries:
                    injured_count += 1
                if cat.illnesses:
                    ill_count += 1
                if cat.permanent_condition:
                    permanent_conditions += 1
                if not cat.injuries and not cat.illnesses:
                    healthy_count += 1
            
            lines.append("HEALTH SUMMARY:")
            lines.append(f"  Healthy: {healthy_count}")
            lines.append(f"  Injured: {injured_count}")
            lines.append(f"  Ill: {ill_count}")
            lines.append(f"  Permanent Conditions: {permanent_conditions}")
            lines.append("")
        
        except Exception as e:
            print(f"Error adding clan statistics to export: {e}")
    
    out_dir = f"{get_save_dir()}/{clan.name}/event_logs"
    file_path = f"{out_dir}/moon_{clan.age:04d}.txt"
    
    try:
        import os
        os.makedirs(out_dir, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Failed to export moon events: {e}")


def add_faded_offspring_to_faded_cat(parent, offspring):
    """In order to siblings to work correctly, and not to lose relation info on fading, we have to keep track of
    both active and faded cat's faded offpsring. This will add a faded offspring to a faded parents file.
    """

    global clan

    path = f"{get_save_dir()}/{clan.name}/faded_cats/{parent}.json"

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as read_file:
            cat_info = ujson.loads(read_file.read())
    except:
        print("ERROR: loading faded cat")
        return False

    cat_info["faded_offspring"].append(offspring)

    safe_save(path, cat_info)

    return True


def load_events():
    """
    Load events from events.json and place into game.cur_events_list.
    """

    global clan

    clanname = clan.name
    events_path = f"{get_save_dir()}/{clanname}/events.json"
    events_list = []
    try:
        with open(events_path, "r", encoding="utf-8") as f:
            events_list = ujson.loads(f.read())
        for event_dict in events_list:
            event_obj = Single_Event.from_dict(event_dict, cat_class)
            if event_obj:
                cur_events_list.append(event_obj)
    except FileNotFoundError:
        pass


def get_config_value(*args):
    """Fetches a value from the config dictionary. Pass each key as a
    separate argument, in the same order you would access the dictionary.
    This function will apply war modifiers if the clan is currently at war."""

    global clan

    war_effected = {
        ("death_related", "leader_death_chance"): (
            "death_related",
            "war_death_modifier_leader",
        ),
        ("death_related", "classic_death_chance"): (
            "death_related",
            "war_death_modifier",
        ),
        ("death_related", "expanded_death_chance"): (
            "death_related",
            "war_death_modifier",
        ),
        ("death_related", "cruel season_death_chance"): (
            "death_related",
            "war_death_modifier",
        ),
        ("condition_related", "classic_injury_chance"): (
            "condition_related",
            "war_injury_modifier",
        ),
        ("condition_related", "expanded_injury_chance"): (
            "condition_related",
            "war_injury_modifier",
        ),
        ("condition_related", "cruel season_injury_chance"): (
            "condition_related",
            "war_injury_modifier",
        ),
    }

    # Get Value
    config_value = constants.CONFIG
    for key in args:
        config_value = config_value[key]

    # Apply war if needed
    if clan and clan.war.get("at_war", False) and args in war_effected:
        rel_change_type = switch_get_value(Switch.war_rel_change_type)
        # if the war was positively affected this moon, we don't apply war modifier
        # this way we only see increased death/injury when the war is going badly or is neutral
        if rel_change_type != "rel_up":
            # Grabs the modifier
            mod = constants.CONFIG
            for key in war_effected[args]:
                mod = mod[key]

            config_value -= mod

    return config_value


def get_free_group_ID(group_type: CatGroup) -> str:
    """
    Find the next free group ID, adds it to the used_group_ID dict, and then returns the ID.
    :param group_type: The CatGroup that the new group will be considered.
    """
    new_ID = str(int(list(used_group_IDs.keys())[-1]) + 1)
    used_group_IDs.update({new_ID: group_type})
    return new_ID


pygame.display.set_caption("Clan Generator")

toggle_fullscreen(
    fullscreen=game_setting_get("fullscreen"),
    show_confirm_dialog=False,
    ingame_switch=False,
)
