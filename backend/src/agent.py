# agent.py
# ======================================================
# 🎲 DAY 8: VOICE GAME MASTER — Pirate / Seafaring Mini-Arc 
# - LiveKit agent plumbing preserved (deepgram, murf, silero, MultilingualModel)
# - Tools: start_adventure, get_scene, player_action (with d20 checks), show_journal, restart_adventure, get_world_state)
# - Per-session userdata holds continuity (history / journal / inventory / named_npcs / choices_made)
# - DEV_SMOKE local simulator available (set DEV_SMOKE=1 in .env.local)
# ======================================================

import os
import json
import uuid
import random
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Annotated

from dotenv import load_dotenv
from pydantic import Field
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("day8_gamemaster_agent_pirate")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# -------------------------
# WORLD: Pirate / Seafaring mini-arc (original content, fan-inspired)
# -------------------------
WORLD = {
    "intro": {
        "title": "A Whisper from the Blue",
        "desc": (
            "You wake aboard a beached skiff on a crescent shore. Beyond the reef a tall ship's "
            "mast silhouettes against dawn. A crumpled map flutters at your feet — its ink shows "
            "an 'X' on a nearby isle called Gull's Haven. From the treeline, gulls cry like a warning."
        ),
        "choices": {
            "read_map": {
                "desc": "Unfold and read the crumpled map.",
                "result_scene": "map",
            },
            "head_to_ship": {
                "desc": "Follow tracks toward the tall mast beyond the reef.",
                "result_scene": "ship",
            },
            "explore_shore": {
                "desc": "Search the sand and nearby tide pools.",
                "result_scene": "tidepools",
            },
        },
    },
    "map": {
        "title": "Weathered Chart",
        "desc": (
            "The map is old but clear: a small isle ringed by jagged rocks, an icon of a carved gate, "
            "and a note in a hurried hand: 'When the gulls hush, the gate wakes.' A faint smear of salt water "
            "carries the smell of ship smoke."
        ),
        "choices": {
            "tuck_map": {
                "desc": "Tuck the map into your sash — it might be useful.",
                "result_scene": "ship_approach",
                "effects": {"add_journal": "Found weathered map to Gull's Haven."},
            },
            "leave_map": {
                "desc": "Leave it — perhaps the map belongs to someone else.",
                "result_scene": "intro",
            },
        },
    },
    "ship": {
        "title": "The Lone Brig",
        "desc": (
            "You creep forward and spy a small brig anchored off the reef, hull half-hid by foam. "
            "Aboard, crates are stacked and a single lantern swings. The deck looks recently used."
        ),
        "choices": {
            "board_quiet": {
                "desc": "Climb quietly and search the brig.",
                "result_scene": "brig_search",
            },
            "shout_hail": {
                "desc": "Call out to see if anyone's aboard.",
                "result_scene": "brig_alert",
            },
            "retreat": {
                "desc": "Step back and return to the shore.",
                "result_scene": "intro",
            },
        },
    },
    "tidepools": {
        "title": "Tidepools and Trinkets",
        "desc": (
            "Among broken shells and driftwood you find a salt-stiff locket and a scrap of a sailor's log: '—last seen near Gull's Gate'."
        ),
        "choices": {
            "take_locket": {
                "desc": "Take the locket and keep the log scrap.",
                "result_scene": "ship_approach",
                "effects": {"add_inventory": "salt_locket", "add_journal": "Found sailor's log scrap referencing Gull's Gate."},
            },
            "leave": {
                "desc": "Leave the finds and move on.",
                "result_scene": "intro",
            },
        },
    },
    "ship_approach": {
        "title": "Approaching the Brig",
        "desc": (
            "You slip toward the brig. The smell of rope and tar is strong. A coiled rope hangs ready — like someone expected to sail soon."
        ),
        "choices": {
            "board": {
                "desc": "Use the rope to board the brig quietly.",
                "result_scene": "brig_search",
            },
            "circle_and_watch": {
                "desc": "Circle the brig from a distance and listen.",
                "result_scene": "brig_listen",
            },
            "return_shore": {
                "desc": "Return to the shore to reconsider.",
                "result_scene": "intro",
            },
        },
    },
    "brig_search": {
        "title": "Crates and Echoes",
        "desc": (
            "Below deck you find crates stamped with a merchant pact and a locked chest with a carved keyhole shaped like a gull."
        ),
        "choices": {
            "pick_lock": {
                "desc": "Attempt to pick the lock.",
                "result_scene": "lock_attempt",
            },
            "carry_chest": {
                "desc": "Try to haul the chest ashore.",
                "result_scene": "haul_attempt",
            },
            "leave_chest": {
                "desc": "Close the chest and leave quietly.",
                "result_scene": "ship_approach",
            },
        },
    },
    "brig_alert": {
        "title": "Lanterns Flare",
        "desc": (
            "Your shout echoes. Lanterns flare and a voice calls below deck, 'Who's there?' Footsteps thump up the ladder."
        ),
        "choices": {
            "pose_as_sailor": {
                "desc": "Claim to be a lost sailor in need of help.",
                "result_scene": "parley",
            },
            "flee": {
                "desc": "Drop back to the shore and hide.",
                "result_scene": "intro",
            },
        },
    },
    "brig_listen": {
        "title": "Listening to Tides",
        "desc": (
            "From behind a bale you hear a hushed argument — someone mentions Gull's Haven and a 'gate' that 'mustn't open.'"
        ),
        "choices": {
            "eavesdrop": {
                "desc": "Eavesdrop to learn more.",
                "result_scene": "learn_secret",
            },
            "sneak_away": {
                "desc": "Slip away before you're seen.",
                "result_scene": "intro",
            },
        },
    },
    "lock_attempt": {
        "title": "The Lock",
        "desc": (
            "The keyhole resists. Picking it could reveal what's inside — or set off an alarm of some kind."
        ),
        "choices": {
            "attempt_pick": {
                "desc": "Try to pick the lock (risky).",
                "result_scene": "pick_result",
            },
            "search_elsewhere": {
                "desc": "Search for clues elsewhere on the brig.",
                "result_scene": "brig_search",
            },
            "leave": {
                "desc": "Leave it and return to deck.",
                "result_scene": "ship_approach",
            },
        },
    },
    "haul_attempt": {
        "title": "Heavy Burden",
        "desc": (
            "The chest is heavier than it looks; hauling it out will take strength and time — and might draw attention."
        ),
        "choices": {
            "heave": {
                "desc": "Heave the chest toward the shore (risky).",
                "result_scene": "heave_result",
            },
            "abandon": {
                "desc": "Abandon the effort and search below.",
                "result_scene": "brig_search",
            },
        },
    },
    "parley": {
        "title": "Parley on the Deck",
        "desc": (
            "A grizzled sailor peers out. He squints at you, then asks 'What business have you with the brig?'"
        ),
        "choices": {
            "tell_truth": {
                "desc": "Tell the truth about finding the skiff.",
                "result_scene": "parley_trust",
            },
            "lie": {
                "desc": "Lie and say you're crew of a nearby trader.",
                "result_scene": "parley_lie",
            },
        },
    },
    "learn_secret": {
        "title": "A Dark Bargain",
        "desc": (
            "You catch a phrase: '—the gate awakens at low tide. If the navy learns, they'll take the relic.' It sounds like trouble."
        ),
        "choices": {
            "seek_gulls_haven": {
                "desc": "Decide to go to Gull's Haven before the navy.",
                "result_scene": "sail_to_isle",
                "effects": {"add_journal": "Heard talk of Gull's Haven and a gate that wakes at low tide."},
            },
            "retreat_quiet": {
                "desc": "Retreat quietly for now.",
                "result_scene": "intro",
            },
        },
    },
    "pick_result": {
        "title": "The Pick",
        "desc": (
            "If you pick the lock you might open the chest — success could bring loot or a clue; failure could sound alarms."
        ),
        "choices": {
            "open_chest": {
                "desc": "Open the chest (if unlocked).",
                "result_scene": "chest_open",
            },
            "leave": {
                "desc": "Leave the chest and slip back up.",
                "result_scene": "ship_approach",
            },
        },
    },
    "heave_result": {
        "title": "Strain and Shout",
        "desc": (
            "You strain with the chest. Muscles burn — a sudden shout from ashore warns that someone approaches from the sandbar."
        ),
        "choices": {
            "run_with_chest": {
                "desc": "Run with the chest across the sand (risky).",
                "result_scene": "escape_attempt",
            },
            "drop_and_hide": {
                "desc": "Drop the chest and hide.",
                "result_scene": "hide_result",
            },
        },
    },
    "chest_open": {
        "title": "Inside the Chest",
        "desc": (
            "Inside is a small, sea-glass idol and a folded note: 'Return what was taken and the tides will sing.' A carved gull tooth dangles in a velvet pouch."
        ),
        "choices": {
            "take_idol": {
                "desc": "Take the sea-glass idol and pouch.",
                "result_scene": "isle_choice",
                "effects": {"add_inventory": "sea_glass_idol", "add_journal": "Found idol and note: 'Return what was taken.'"},
            },
            "leave_it": {
                "desc": "Leave the chest as it is.",
                "result_scene": "ship_approach",
            },
        },
    },
    "sail_to_isle": {
        "title": "Course for Gull's Haven",
        "desc": (
            "You find a skiff and push out. Wind and current favor you. Gull's Haven rises from mist — a narrow gate of carved stone stands on the shore."
        ),
        "choices": {
            "approach_gate": {
                "desc": "Step toward the carved gate.",
                "result_scene": "gate",
            },
            "circle_coast": {
                "desc": "Circle the island and look for a safe landing.",
                "result_scene": "coast_search",
            },
        },
    },
    "gate": {
        "title": "The Carved Gate",
        "desc": (
            "The gate hums faintly. Tide pulls at the sand like fingers. The gulls fall silent as if listening."
        ),
        "choices": {
            "offer_idol": {
                "desc": "Offer the idol or speak truth (if you have it).",
                "result_scene": "offer_result",
            },
            "probe_gate": {
                "desc": "Try to force the gate open (risky).",
                "result_scene": "force_result",
            },
            "retreat": {
                "desc": "Retreat to consider.",
                "result_scene": "sail_to_isle",
            },
        },
    },
    "offer_result": {
        "title": "Tide's Answer",
        "desc": (
            "If you offer the idol with truth, the gate may yield. If you bluff, the gate may remain closed — or worse."
        ),
        "choices": {
            "truth": {
                "desc": "Offer truth and the idol.",
                "result_scene": "resolve_good",
                "effects": {"add_journal": "Offered the idol truthfully at the gate."},
            },
            "bluff": {
                "desc": "Bluff or force the offering.",
                "result_scene": "resolve_mixed",
            },
        },
    },
    "force_result": {
        "title": "Forcing the Gate",
        "desc": (
            "Forcing the gate is dangerous — the tide fights back, and a shape moves beneath the water."
        ),
        "choices": {
            "push": {
                "desc": "Push hard to force the gate (risky).",
                "result_scene": "fight_sea",
            },
            "step_back": {
                "desc": "Step back and rethink.",
                "result_scene": "sail_to_isle",
            },
        },
    },
    "resolve_good": {
        "title": "A Gentle Reprieve",
        "desc": (
            "The gate opens with a sigh of seawind. Inside you find a small cove and a grateful whisper from the deep — a minor peace returns."
        ),
        "choices": {
            "take_rest": {
                "desc": "Rest in the cove and tend to wounds.",
                "result_scene": "intro",
            },
            "seek_more": {
                "desc": "Search the island for more secrets.",
                "result_scene": "coast_search",
            },
        },
    },
    "resolve_mixed": {
        "title": "Storm-Touched",
        "desc": (
            "The gate shifts but releases a spout of briny wind that chills the bones. You feel the island watch you."
        ),
        "choices": {
            "press_on": {
                "desc": "Press further into the grove.",
                "result_scene": "coast_search",
            },
            "withdraw": {
                "desc": "Withdraw to your skiff.",
                "result_scene": "sail_to_isle",
            },
        },
    },
    "fight_sea": {
        "title": "Tide and Teeth",
        "desc": (
            "Something beneath the waves lashes out — a hulking maw of barnacled teeth. You must react."
        ),
        "choices": {
            "fight": {
                "desc": "Stand and fight the sea shape (risky).",
                "result_scene": "fight_end",
            },
            "flee": {
                "desc": "Flee to the skiff and row away.",
                "result_scene": "intro",
            },
        },
    },
    "fight_end": {
        "title": "After the Clash",
        "desc": (
            "You survive the clash and wash ashore exhausted. A small carved token lies in the sand — perhaps the relic the island wanted."
        ),
        "choices": {
            "take_token": {
                "desc": "Take the carved token and keep its lesson.",
                "result_scene": "reward",
                "effects": {"add_inventory": "carved_token", "add_journal": "Recovered carved token after sea clash."},
            },
            "leave": {
                "desc": "Leave the token and tend to yourself.",
                "result_scene": "intro",
            },
        },
    },
    "isle_choice": {
        "title": "Decision at the Isle",
        "desc": (
            "With the idol in hand you must choose: return it at the gate or hide it for profit. The gulls watch."
        ),
        "choices": {
            "return_idol": {
                "desc": "Return the idol at the gate (truth).",
                "result_scene": "resolve_good",
            },
            "sell_idol": {
                "desc": "Keep and sell the idol for coin.",
                "result_scene": "resolve_mixed",
            },
        },
    },
    "coast_search": {
        "title": "Coastline Secrets",
        "desc": (
            "You walk where tidewater carved hollows; old footprints and a half-buried oar show others were here recently."
        ),
        "choices": {
            "follow_tracks": {
                "desc": "Follow the tracks inland.",
                "result_scene": "gate",
            },
            "return_skiff": {
                "desc": "Return to your skiff and consider leaving.",
                "result_scene": "intro",
            },
        },
    },
    "escape_attempt": {
        "title": "A Narrow Escape",
        "desc": (
            "You sprint with the chest. A cry rises — a patrol sees you but a sudden fog of salt gives you cover. You make it to the skiff breathless."
        ),
        "choices": {
            "row_away": {
                "desc": "Row away from the brig and head to Gull's Haven.",
                "result_scene": "sail_to_isle",
            },
            "hide": {
                "desc": "Hide until the coast clears.",
                "result_scene": "intro",
            },
        },
    },
    "hide_result": {
        "title": "Hiding in Shadow",
        "desc": (
            "You drop and press into shadow. The patrol passes by with a curse; you remain unseen."
        ),
        "choices": {
            "wait": {
                "desc": "Wait until it is safe.",
                "result_scene": "intro",
            },
            "sneak_off": {
                "desc": "Sneak off while they search elsewhere.",
                "result_scene": "sail_to_isle",
            },
        },
    },
    "reward": {
        "title": "A Pirate's Quiet Victory",
        "desc": (
            "The tide calms. You hold an object tied to the island's memory. Whether you return it or keep it, the sea remembers you now."
        ),
        "choices": {
            "end_session": {
                "desc": "End the session and let the sea carry the rest.",
                "result_scene": "intro",
            },
            "keep_exploring": {
                "desc": "Keep sailing for new horizons.",
                "result_scene": "intro",
            },
        },
    }
}

# -------------------------
# Per-session userdata
# -------------------------
@dataclass
class Userdata:
    player_name: Optional[str] = None
    current_scene: str = "intro"
    history: List[Dict[str, Any]] = field(default_factory=list)  # transitions
    journal: List[str] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    named_npcs: Dict[str, str] = field(default_factory=dict)
    choices_made: List[str] = field(default_factory=list)
    attributes: Dict[str, int] = field(default_factory=lambda: {"STR": 10, "DEX": 14, "INT": 11, "WIS": 13, "CHA": 9})
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# -------------------------
# Dice & check helpers
# -------------------------
def roll_d20() -> int:
    return random.randint(1, 20)

def attr_modifier(val: int) -> int:
    return (val - 10) // 2

def resolve_check(attr_val: int, modifier: int = 0, difficulty: int = 12) -> Dict[str, Any]:
    r = roll_d20()
    mod = attr_modifier(attr_val)
    total = r + mod + modifier
    if total >= difficulty + 4:
        tier = "Full success"
    elif total >= difficulty:
        tier = "Partial success"
    else:
        tier = "Fail"
    return {"roll": r, "attr_mod": mod, "modifier": modifier, "total": total, "tier": tier, "difficulty": difficulty}

ACTION_ATTR_MAP = {
    "sneak": "DEX", "stealth": "DEX", "hide": "DEX",
    "attack": "STR", "hit": "STR", "lift": "STR", "climb": "STR",
    "persuade": "CHA", "charm": "CHA", "intimidate": "CHA",
    "investigate": "INT", "search": "INT", "examine": "INT",
    "listen": "WIS", "notice": "WIS", "perceive": "WIS",
    "heal": "WIS", "cast": "INT", "spell": "INT"
}

def detect_risky_action(text: str) -> Optional[str]:
    t = (text or "").lower()
    for kw, attr in ACTION_ATTR_MAP.items():
        if kw in t:
            return attr
    if any(w in t for w in ["attempt", "try", "risk", "chance", "roll"]):
        return "DEX"
    return None

# -------------------------
# Scene helpers & effects
# -------------------------
def scene_text(scene_key: str, userdata: Userdata) -> str:
    scene = WORLD.get(scene_key)
    if not scene:
        return "You find only shadows. What do you do?"
    desc = f"{scene['desc']}\n\nChoices:\n"
    for cid, cmeta in scene.get("choices", {}).items():
        desc += f"- {cmeta['desc']} (say: {cid})\n"
    desc += "\nWhat do you do?"
    return desc

def apply_effects(effects: Dict[str, Any], userdata: Userdata):
    if not effects:
        return
    if "add_journal" in effects:
        userdata.journal.append(effects["add_journal"])
    if "add_inventory" in effects:
        userdata.inventory.append(effects["add_inventory"])

def summarize_transition(old_scene: str, action_key: str, result_scene: str, userdata: Userdata) -> str:
    entry = {"from": old_scene, "action": action_key, "to": result_scene, "time": datetime.utcnow().isoformat() + "Z"}
    userdata.history.append(entry)
    userdata.choices_made.append(action_key)
    return f"You chose '{action_key}'."

# -------------------------
# Fallback narrators (if LLM not configured)
# -------------------------
def fallback_gm_narration_with_roll(player_text: str, roll_info: Optional[Dict[str, Any]], userdata: Userdata) -> str:
    name = userdata.player_name or "You"
    intro = f"{name}, you said: \"{player_text}\".\n"
    if roll_info:
        tier = roll_info["tier"]
        roll_line = f"(Roll: {roll_info['roll']}  +{roll_info['attr_mod']} = {roll_info['total']} vs DC {roll_info['difficulty']})"
        if tier == "Full success":
            outcome = f"{roll_line} — You succeed brilliantly. Things go in your favor."
        elif tier == "Partial success":
            outcome = f"{roll_line} — You succeed, but with a complication."
        else:
            outcome = f"{roll_line} — You fail; consequences follow."
        body = outcome
    else:
        body = "You move forward; the world responds in small ways."
    return f"{intro}\n{body}\n\nWhat do you do?"

def fallback_gm_simple_intro(userdata: Userdata) -> str:
    name = userdata.player_name or "Traveler"
    intro = f"Greetings {name}. {WORLD.get('intro',{}).get('desc','You stand at the shore.')}\n\nWhat do you do?"
    return intro

# -------------------------
# Tools (function_tool)
# -------------------------
@function_tool
async def start_adventure(ctx: RunContext[Userdata], player_name: Annotated[Optional[str], Field(description="Player name", default=None)] = None) -> str:
    u = ctx.userdata
    if player_name:
        u.player_name = player_name
    u.current_scene = "intro"
    u.history = []
    u.journal = []
    u.inventory = []
    u.named_npcs = {}
    u.choices_made = []
    u.session_id = str(uuid.uuid4())[:8]
    u.started_at = datetime.utcnow().isoformat() + "Z"
    opening = fallback_gm_simple_intro(u)
    if not opening.strip().endswith("What do you do?"):
        opening = opening.strip() + "\n\nWhat do you do?"
    u.history.append({"from": None, "action": "start", "to": "intro", "time": datetime.utcnow().isoformat() + "Z"})
    return opening

@function_tool
async def get_scene(ctx: RunContext[Userdata]) -> str:
    u = ctx.userdata
    return scene_text(u.current_scene or "intro", u)

@function_tool
async def get_world_state(ctx: RunContext[Userdata]) -> str:
    u = ctx.userdata
    return json.dumps({
        "player_name": u.player_name,
        "current_scene": u.current_scene,
        "journal": u.journal,
        "inventory": u.inventory,
        "recent_history": u.history[-8:],
        "attributes": u.attributes
    }, indent=2)

@function_tool
async def player_action(ctx: RunContext[Userdata], action: Annotated[str, Field(description="Player spoken action or short code")]) -> str:
    u = ctx.userdata
    current = u.current_scene or "intro"
    scene = WORLD.get(current, {})
    text = (action or "").strip()
    if not text:
        return scene_text(current, u)

    # Try to resolve choice key exactly
    chosen_key = None
    if text.lower() in (scene.get("choices") or {}):
        chosen_key = text.lower()

    # Try simple matching on choice descriptions
    if not chosen_key:
        for cid, cmeta in (scene.get("choices") or {}).items():
            desc = cmeta.get("desc","").lower()
            if cid in text.lower() or any(word in text.lower() for word in desc.split()[:4]):
                chosen_key = cid
                break

    # Keyword scanning fallback
    if not chosen_key:
        for cid, cmeta in (scene.get("choices") or {}).items():
            for kw in cmeta.get("desc","").lower().split():
                if kw and kw in text.lower():
                    chosen_key = cid
                    break
            if chosen_key:
                break

    if not chosen_key:
        # Could not map: treat it as a free action — attempt risky check if likely
        attr = detect_risky_action(text)
        roll_info = None
        if attr:
            attr_val = u.attributes.get(attr, 10)
            difficulty = 12
            if any(w in text.lower() for w in ["hard", "dangerous", "guarded", "trap", "strong"]):
                difficulty += 2
            roll_info = resolve_check(attr_val, modifier=0, difficulty=difficulty)
            gm_reply = fallback_gm_narration_with_roll(text, roll_info, u)
            u.history.append({"from": current, "action": text, "to": current, "time": datetime.utcnow().isoformat() + "Z", "roll": roll_info})
            return gm_reply
        # else ask for clarification
        return "I didn't understand that. Try one of the visible choices or say a short phrase like 'inspect the box'.\n\n" + scene_text(current, u)

    # We have a chosen_key: apply choice
    choice_meta = scene["choices"].get(chosen_key, {})
    result_scene = choice_meta.get("result_scene", current)
    effects = choice_meta.get("effects", {})
    apply_effects(effects or {}, u)
    note = summarize_transition(current, chosen_key, result_scene, u)
    u.current_scene = result_scene
    persona = "The Game Master (soft, weathered voice) says:\n\n"
    next_text = scene_text(result_scene, u)
    reply = f"{persona}{note}\n\n{next_text}"
    if not reply.strip().endswith("What do you do?"):
        reply = reply.strip() + "\n\nWhat do you do?"
    u.history.append({"from": current, "action": chosen_key, "to": result_scene, "time": datetime.utcnow().isoformat() + "Z"})
    return reply

@function_tool
async def show_journal(ctx: RunContext[Userdata]) -> str:
    u = ctx.userdata
    lines = []
    lines.append(f"Session: {u.session_id} | Started: {u.started_at}")
    if u.player_name:
        lines.append(f"Player: {u.player_name}")
    lines.append("\nJournal:")
    if u.journal:
        for j in u.journal:
            lines.append(f"- {j}")
    else:
        lines.append("- (empty)")
    lines.append("\nInventory:")
    if u.inventory:
        for it in u.inventory:
            lines.append(f"- {it}")
    else:
        lines.append("- (empty)")
    lines.append("\nRecent actions:")
    for h in u.history[-6:]:
        lines.append(f"- {h.get('time')} | {h.get('from')} -> {h.get('to')} via {h.get('action')}")
    lines.append("\nWhat do you do?")
    return "\n".join(lines)

@function_tool
async def restart_adventure(ctx: RunContext[Userdata]) -> str:
    u = ctx.userdata
    u.current_scene = "intro"
    u.history = []
    u.journal = []
    u.inventory = []
    u.named_npcs = {}
    u.choices_made = []
    u.session_id = str(uuid.uuid4())[:8]
    u.started_at = datetime.utcnow().isoformat() + "Z"
    greeting = fallback_gm_simple_intro(u)
    if not greeting.strip().endswith("What do you do?"):
        greeting = greeting.strip() + "\n\nWhat do you do?"
    return greeting

# -------------------------
# Agent definition (pirate-themed instructions)
# -------------------------
class GameMasterAgent(Agent):
    def __init__(self):
        instructions = """
        You are 'Aurek', the Game Master (GM) for a voice-first, seafaring pirate adventure.
        Universe: High-seas pirate fantasy (islands, brigantines, reef traps, sea-spirits).
        Tone: Playful, adventurous, and slightly mysterious — keep it cinematic but easy to speak.
        Role: Narrate scenes vividly, remember the player's past choices, inventory, named places and small NPC details,
              and ALWAYS end messages with the question: 'What do you do?'
        Rules:
         - Use the provided tools (start_adventure, get_scene, player_action, show_journal, restart_adventure, get_world_state).
         - When a player's action is risky, expect the backend to run a d20 check and include the roll result; incorporate the result into the narration (Full success / Partial success / Fail).
         - Keep spoken replies short enough for natural TTS (2–4 short paragraphs), evocative but not overloaded.
         - Do not reference or impersonate copyrighted characters or direct franchise lines.
        """
        super().__init__(instructions=instructions, tools=[start_adventure, get_scene, player_action, show_journal, restart_adventure, get_world_state])

# -------------------------
# Entrypoint & prewarm
# -------------------------
def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
    except Exception:
        logger.warning("VAD prewarm failed; proceeding without preloaded VAD.")

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info("🚀 STARTING DAY 8 VOICE GAME MASTER — Pirate Mini-Arc")
    userdata = Userdata()
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-marcus", style="Conversational", text_pacing=True),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata.get("vad"),
        userdata=userdata,
    )
    await session.start(agent=GameMasterAgent(), room=ctx.room, room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    await ctx.connect()

# -------------------------
# DEV_SMOKE: quick local test (no LiveKit). Set DEV_SMOKE=1 in .env.local to run this on `python agent.py`.
# -------------------------
if __name__ == "__main__":
    if os.getenv("DEV_SMOKE"):
        import asyncio
        class DummyCtx:
            pass
        async def smoke():
            print("DEV_SMOKE: starting local simulation of Game Master agent tools.\n")
            ctx = DummyCtx()
            ctx.userdata = Userdata()
            print("=== start_adventure ===")
            print(await start_adventure(ctx, player_name="Tushar"), "\n")
            print("=== player_action: read_map ===")
            print(await player_action(ctx, "read_map"), "\n")
            print("=== player_action: tuck_map ===")
            print(await player_action(ctx, "tuck_map"), "\n")
            print("=== player_action: board ===")
            print(await player_action(ctx, "board"), "\n")
            print("=== show_journal ===")
            print(await show_journal(ctx), "\n")
            print("DEV_SMOKE done.")
        asyncio.run(smoke())
    else:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
