
# ======================================================
# 🏴‍☠️ ONE PIECE–STYLE VOICE IMPROV AGENT — Improv Battle: Grand Line Edition
# - LiveKit agent plumbing similar to agent_tushar.py
# - Persona: Over-the-top pirate/adventure host inspired by One Piece energy
# - DEV_SMOKE local simulator available (set DEV_SMOKE=1 in .env.local)
# ======================================================

import os
import json
import uuid
import logging
import random
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
logger = logging.getLogger("onepiece_improv_agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# -------------------------
# One Piece–style scenario seeds
# -------------------------
ONEPIECE_SCENARIOS = [
    "You are a rookie pirate who just ate a mysterious Devil Fruit that gives you the power to stretch like a rubber band — but it only works when you hiccup loudly.",
    "You are the ship's cook during a surprise sea-monster attack; your secret weapon is a curry that makes foes fall asleep from joy.",
    "You must convince the ship's swordsman to trade his blade for a pair of decorative chopsticks (very convincing sales pitch!).",
    "You're telepathically linked to a talking parrot who leaks the captain's embarrassing childhood secrets during a formal crew meeting.",
    "You found a treasure map that leads to a legendary 'Masala Island' where the currency is spice. Explain how you'll pay the toll.",
    "You are ship morale officer and must host an over-the-top recruitment chant that causes a visiting admiral to cry tears of laughter.",
    "A rival pirate challenges you to a duel but keeps apologizing in the middle — roleplay the awkward but epic duel.",
    "You are a navigator who misreads the stars; explain confidently why the ship is headed toward a floating tea stall instead of the Grand Line.",
]

# Dramatic reaction templates tuned for One Piece energy
ONEPIECE_REACTIONS_SUPPORTIVE = [
    "ZABIMARU! That was legendary — your spirit burned like a thousand suns!",
    "Ha-ha! That energy was pure pirate spirit — I felt the sea roar!",
    "Amazing! The commitment was as strong as a captain's vow. Incredible!",
]
ONEPIECE_REACTIONS_NEUTRAL = [
    "Not bad — you rode the wave well. Maybe add one louder laugh next time.",
    "Solid attempt. The concept was tasty like a good curry — could use more spice.",
    "Good flavor, but the punchline needed a longer drumroll. Try stretching the silence.",
]
ONEPIECE_REACTIONS_CRITICAL = [
    "Argh! You almost had it, but you cut the dramatic beat too soon. Let the moment breathe!",
    "Close — but the crew needed more conviction. Next time, shout the captain's name!",
    "That felt a bit safe for the Grand Line. Be bolder — be loud, be proud, be silly!",
]

# -------------------------
# Per-session Improv state
# -------------------------
@dataclass
class ImprovState:
    player_name: Optional[str] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    current_round: int = 0
    max_rounds: int = 3
    rounds: List[Dict[str, Any]] = field(default_factory=list)  # each: {"scenario": str, "transcript": str, "reaction": str}
    phase: str = "intro"  # "intro" | "awaiting_improv" | "reacting" | "done"
    history: List[Dict[str, Any]] = field(default_factory=list)

# -------------------------
# Helpers
# -------------------------
def sample_onepiece_scenario() -> str:
    return random.choice(ONEPIECE_SCENARIOS)

def pick_reaction_by_style(style: str) -> str:
    if style == "supportive":
        return random.choice(ONEPIECE_REACTIONS_SUPPORTIVE)
    if style == "neutral":
        return random.choice(ONEPIECE_REACTIONS_NEUTRAL)
    return random.choice(ONEPIECE_REACTIONS_CRITICAL)

def reaction_style_selector() -> str:
    r = random.random()
    if r < 0.4:
        return "supportive"
    if r < 0.8:
        return "neutral"
    return "critical"

# -------------------------
# Tools
# -------------------------
@function_tool
async def start_show(
    ctx: RunContext[ImprovState],
    player_name: Annotated[Optional[str], Field(description="Player's name (optional)", default=None)] = None,
    max_rounds: Annotated[int, Field(description="Number of rounds", default=3)] = 3,
) -> str:
    state = ctx.userdata
    if player_name:
        state.player_name = player_name
    state.max_rounds = max_rounds or 3
    state.current_round = 0
    state.rounds = []
    state.phase = "intro"
    state.history.append({"time": datetime.utcnow().isoformat() + "Z", "action": "start_show", "player_name": state.player_name})
    intro = (
        f"YA-HAA! Welcome to Improv Battle — Grand Line Edition! {state.player_name or 'Brave Soul'}, "
        f"we'll sail through {state.max_rounds} wild rounds. When I call the scene, throw yourself in character — be loud, be silly, be pirate! "
        "Say 'End scene' when you're done. Let the adventure begin!"
    )
    return intro

@function_tool
async def next_scenario(ctx: RunContext[ImprovState]) -> str:
    state = ctx.userdata
    if state.phase == "done":
        return "The voyage has ended. Say 'start show' to set sail again!"
    if state.current_round >= state.max_rounds:
        state.phase = "done"
        return "We've run out of rounds — I'll prepare the closing fanfare!"
    state.current_round += 1
    scenario = sample_onepiece_scenario()
    state.rounds.append({"scenario": scenario, "transcript": None, "reaction": None})
    state.phase = "awaiting_improv"
    state.history.append({"time": datetime.utcnow().isoformat() + "Z", "action": "next_scenario", "round": state.current_round})
    return f"Round {state.current_round}! {scenario} — Go on, show the crew what you've got. End the scene by saying 'End scene'."

@function_tool
async def react_to_improv(
    ctx: RunContext[ImprovState],
    transcript: Annotated[Optional[str], Field(description="Player's spoken lines (transcript)", default="")] = ""
) -> str:
    state = ctx.userdata
    if not state.rounds:
        return "No active round. Say 'next scenario' to begin your pirate challenge."
    current = state.rounds[-1]
    current["transcript"] = transcript or ""
    style = reaction_style_selector()
    if not transcript or len(transcript.strip()) == 0:
        reaction = "Silence on the deck? Argh — the Grand Line demands commitment! Try bellowing your lines next time."
    else:
        # small content-aware tweak: include a snippet sometimes
        snippet = " ".join(transcript.strip().split()[:6])
        base = pick_reaction_by_style(style)
        # occasionally reference the snippet for flavor
        if random.random() < 0.5:
            reaction = f"{base} (that bit: '{snippet}...')"
        else:
            reaction = base
    current["reaction"] = reaction
    state.phase = "reacting"
    state.history.append({"time": datetime.utcnow().isoformat() + "Z", "action": "react", "round": state.current_round})
    return reaction

@function_tool
async def end_show(ctx: RunContext[ImprovState]) -> str:
    state = ctx.userdata
    if state.phase == "done":
        return "The fanfare already played. Start another voyage when you're ready!"
    praises = []
    critiques = []
    for idx, rnd in enumerate(state.rounds, start=1):
        r = (rnd.get("reaction") or "").lower()
        if any(k in r for k in ("legend", "incredible", "brilliant", "loved")):
            praises.append(f"R{idx}")
        if any(k in r for k in ("silence", "quiet", "rushed", "safe")):
            critiques.append(f"R{idx}")
    notes = []
    if praises:
        notes.append(f"Your bravest moments: {', '.join(praises)}.")
    if critiques:
        notes.append(f"Work on projection/pacing in: {', '.join(critiques)}.")
    if not notes:
        notes.append("You showed true pirate heart — bold and adventurous!")
    highlights = " | ".join([f"R{i}: {r.get('reaction') or 'no reaction'}" for i, r in enumerate(state.rounds, start=1)])
    summary = (
        f"Ha-HAA! That's a wrap on the Grand Line, {state.player_name or 'Shipmate'}! {' '.join(notes)} "
        f"Highlights: {highlights} — Thank you for sailing with Improv Battle: Grand Line Edition!"
    )
    state.phase = "done"
    state.history.append({"time": datetime.utcnow().isoformat() + "Z", "action": "end_show"})
    return summary

@function_tool
async def get_state(ctx: RunContext[ImprovState]) -> str:
    s = ctx.userdata
    return json.dumps({
        "player_name": s.player_name,
        "session_id": s.session_id,
        "started_at": s.started_at,
        "current_round": s.current_round,
        "max_rounds": s.max_rounds,
        "rounds": s.rounds,
        "phase": s.phase,
        "recent_history": s.history[-10:],
    }, indent=2)

# -------------------------
# Host Agent (One Piece persona)
# -------------------------
class OnePieceHostAgent(Agent):
    def __init__(self):
        instructions = """
        You are the host of a TV improv show called 'Improv Battle — Grand Line Edition'.
        Persona: Over-the-top pirate/adventure energy inspired by shonen anime — dramatic, loud, playful.
        Keep lines short for TTS clarity. Use the provided tools (start_show, next_scenario, react_to_improv, end_show, get_state).
        Choose between supportive, neutral, and mildly critical reactions; be respectful and hilarious.
        """
        super().__init__(instructions=instructions,
                         tools=[start_show, next_scenario, react_to_improv, end_show, get_state])

# -------------------------
# Entrypoint & Prewarm
# -------------------------
def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
    except Exception:
        logger.warning("VAD prewarm failed; continuing without preloaded VAD.")

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info("🏴‍☠️ STARTING ONE PIECE–STYLE IMPROV AGENT (Grand Line Edition)")
    userdata = ImprovState()
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-marcus", style="Dramatic", text_pacing=True),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata.get("vad"),
        userdata=userdata,
    )
    await session.start(agent=OnePieceHostAgent(), room=ctx.room, room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    await ctx.connect()

# -------------------------
# DEV_SMOKE (local test)
# -------------------------
if __name__ == "__main__":
    if os.getenv("DEV_SMOKE"):
        import asyncio
        class DummyCtx:
            pass
        async def smoke():
            print("DEV_SMOKE: One Piece Improv tools smoke test.\n")
            ctx = DummyCtx()
            ctx.userdata = ImprovState()
            print("=== start_show (player_name='Luffy') ===")
            print(await start_show(ctx, player_name="Luffy", max_rounds=3), "\n")
            print("=== next_scenario (round 1) ===")
            print(await next_scenario(ctx), "\n")
            print("=== react_to_improv (empty transcript) ===")
            print(await react_to_improv(ctx, transcript=""), "\n")
            print("=== next_scenario (round 2) ===")
            print(await next_scenario(ctx), "\n")
            print("=== react_to_improv (with transcript) ===")
            print(await react_to_improv(ctx, transcript="I swing my rubber arm and accidentally hug the sea king, it giggles."), "\n")
            print("=== get_state ===")
            print(await get_state(ctx), "\n")
            print("=== end_show ===")
            print(await end_show(ctx), "\n")
            print("DEV_SMOKE done.")
        asyncio.run(smoke())
    else:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
