# ======================================================
# 🏦 DAY 6: BANK FRAUD ALERT AGENT
# 🛡️ "Global Bank" - Fraud Detection & Resolution
# 🚀 Features: Identity Verification, Database Lookup, Status Updates
# ======================================================

import logging
import json
import os
from datetime import datetime
from typing import Annotated, Optional, List
from dataclasses import dataclass, asdict

print("\n" + "🛡️" * 50)
print("🚀 BANK FRAUD AGENT BY Tushar - INITIALIZED")
print("📚 TASKS: Verify Identity -> Check Transaction -> Update DB")
print("🛡️" * 50 + "\n")

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

# 🔌 PLUGINS
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# ======================================================
# 💾 1. DATABASE SETUP (Mock Data)
# ======================================================

DB_FILE = "fraud_db.json"

# Schema
@dataclass
class FraudCase:
    userName: str
    securityIdentifier: str
    cardEnding: str
    transactionName: str
    transactionAmount: str
    transactionTime: str
    transactionSource: str
    case_status: str = "pending_review"
    notes: str = ""


def seed_database():
    """Creates a sample database if one doesn't exist."""
    path = os.path.join(os.path.dirname(__file__), DB_FILE)
    if not os.path.exists(path):
        sample_data = [
            {
                "userName": "Amit",
                "securityIdentifier": "A1001",
                "cardEnding": "4242",
                "transactionName": "Local Electronics",
                "transactionAmount": "₹11,500.00",
                "transactionTime": "2025-11-25 14:30 IST",
                "transactionSource": "localshop.example",
                "case_status": "pending_review",
                "notes": "Automated flag: High value purchase."
            },
            {
                "userName": "Kunal",
                "securityIdentifier": "P9988",
                "cardEnding": "1199",
                "transactionName": "Unknown Exchange",
                "transactionAmount": "$2,100.00",
                "transactionTime": "2025-11-26 04:15 PST",
                "transactionSource": "online_transfer",
                "case_status": "pending_review",
                "notes": "Automated flag: Unusual location."
            }
        ]
        with open(path, "w", encoding='utf-8') as f:
            json.dump(sample_data, f, indent=4)
        print(f"✅ Database seeded at {DB_FILE}")

# Initialize DB on load
seed_database()

# ======================================================
# 🧠 2. STATE MANAGEMENT
# ======================================================

@dataclass
class Userdata:
    active_case: Optional[FraudCase] = None

# ======================================================
# 🛠️ 3. FRAUD AGENT TOOLS
# ======================================================

@function_tool
async def lookup_customer(
    ctx: RunContext[Userdata],
    name: Annotated[str, Field(description="The name the user provides")]
) -> str:
    """
    🔍 Looks up a customer in the fraud database by name.
    Call this immediately when the user says their name.
    """
    print(f"🔎 LOOKING UP: {name}")
    path = os.path.join(os.path.dirname(__file__), DB_FILE)
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
        found_record = next((item for item in data if item["userName"].lower() == name.lower()), None)

        if found_record:
            ctx.userdata.active_case = FraudCase(**found_record)
            return (
                f"Record Found."

                f"User: {found_record['userName']}"

                f"Security ID (Expected): {found_record['securityIdentifier']}"
                
                f"Transaction Details: {found_record['transactionAmount']} at {found_record['transactionName']} ({found_record['transactionSource']})"

                f"Instructions: Ask for the Security Identifier to verify identity before discussing the transaction."
            )
        else:
            return "User not found. Ask them to repeat the name or contact support manually."

    except Exception as e:
        return f"Database error: {str(e)}"


@function_tool
async def resolve_fraud_case(
    ctx: RunContext[Userdata],
    status: Annotated[str, Field(description="'confirmed_safe' or 'confirmed_fraud'")],
    notes: Annotated[str, Field(description="A brief summary of the user's response")]
) -> str:
    """Saves the case result to DB."""

    if not ctx.userdata.active_case:
        return "Error: No active case selected."

    case = ctx.userdata.active_case
    case.case_status = status
    case.notes = notes

    path = os.path.join(os.path.dirname(__file__), DB_FILE)

    try:
        with open(path, "r") as f:
            data = json.load(f)

        for i, item in enumerate(data):
            if item["userName"] == case.userName:
                data[i] = asdict(case)
                break

        with open(path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"✅ CASE UPDATED: {case.userName} -> {status}")

        if status == "confirmed_fraud":
            return (
                "Case updated as FRAUD. Inform the user: Card ending in "
                + case.cardEnding
                + " is now blocked. A replacement card will be issued."
            )
        else:
            return "Case updated as SAFE. Inform the user: The restriction has been lifted. Thank you for verifying."

    except Exception as e:
        return f"Error saving to DB: {e}"

# ======================================================
# 🤖 4. AGENT DEFINITION
# ======================================================

class FraudAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            You are 'Alex', a Fraud Detection Specialist at Global Bank.
            Your task is to verify a suspicious transaction.

            SECURITY PROTOCOL:
            1. Greet & Ask Name.
            2. Use lookup_customer immediately when user says their name.
            3. Ask for Security Identifier.
            4. If mismatch → Apologize & End call.
            5. If match → Proceed.
            6. Ask if they recognize the flagged transaction.
            7. If YES → resolve_fraud_case('confirmed_safe')
            8. If NO → resolve_fraud_case('confirmed_fraud')
            9. Close call professionally.

            Tone: Calm, clear, professional.
            """,
            tools=[lookup_customer, resolve_fraud_case],
        )

# ======================================================
# 🎬 ENTRYPOINT
# ======================================================

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    print("\n" + "💼" * 25)
    print("🚀 STARTING FRAUD ALERT SESSION")

    userdata = Userdata()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),  # Ensure you have access to this model
        tts=murf.TTS(
            voice="en-US-marcus",
            style="Conversational",
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )

    # 3. Start the agent session
    await session.start(
        agent=FraudAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    # Connect context (keeps the worker alive)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
