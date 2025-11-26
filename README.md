🎓 Day 4 – Teach-the-Tutor: Active Recall Coach

An interactive learning agent that teaches concepts, quizzes the learner, and then asks the learner to teach the concept back — leveraging the proven “active recall” technique. The agent dynamically shifts between learn, quiz, and teach_back modes and uses a small JSON course file to power the entire learning flow.

🧭 Overview

The core idea of Day 4 is simple:

The best way to learn is to teach.

This agent explains concepts, quizzes the user, asks the user to explain them back, and scores the explanation qualitatively.
The user may switch modes at any time, and the agent should respond by shifting to that mode instantly.

🎙️ Voices (Murf Falcon)
Mode	Voice Name
learn	Matthew
quiz	Alicia
teach_back	Ken

Each mode uses a different Murf Falcon voice to create a strong distinction between learning phases.

🧩 Learning Modes (Required)
1. 📘 Learn Mode

Agent explains a concept using the content file.

Uses summary field from JSON.

Voice: Matthew

2. ❓ Quiz Mode

Agent asks a question based on the concept's sample question.

Voice: Alicia

3. 🧑‍🏫 Teach-Back Mode

Agent asks user to explain the concept in their own words.

Gives simple qualitative feedback (good / decent / needs clarity).

Voice: Ken

📂 Course Content File (JSON)

Location:

shared-data/day4_tutor_content.json


Example file:

[
  {
    "id": "variables",
    "title": "Variables",
    "summary": "Variables store values so you can reuse them later...",
    "sample_question": "What is a variable and why is it useful?"
  },
  {
    "id": "loops",
    "title": "Loops",
    "summary": "Loops let you repeat an action multiple times...",
    "sample_question": "Explain the difference between a for loop and a while loop."
  }
]

The agent uses this file to:

Explain concepts in Learn mode

Ask quiz questions in Quiz mode

Prompt the student during Teach-Back mode

🎯 Completion Criteria

You successfully complete Day 4 when:

✔ 1. Agent greets the user

Asks which learning mode they prefer

Switches to proper voice & mode

✔ 2. All three modes are implemented

learn → explains concept from JSON

quiz → asks question from JSON

teach_back → user explains, agent evaluates qualitatively

✔ 3. User can switch modes anytime

Example:

“Switch to quiz”
“Now teach back loops”
“Explain variables”

✔ 4. JSON content fully drives the learning

No hallucination, no external content.

🤖 Agent Capabilities

Reads the course content file on startup

Supports multiple concepts (variables, loops, etc.)

Responds strictly using JSON-provided summaries & questions

Maintains current mode state

Detects mode-switching phrases

Gives short evaluation feedback based on user's explanation

Uses correct Murf Falcon voice per mode

🧠 Teach-Back Feedback Logic

Qualitative evaluation based on learner’s answer:

Great → User explanation covers definition + purpose

Good → User explanation is mostly correct but lacks depth

Needs Improvement → Missing key points, unclear or incomplete

No scoring, just friendly coaching feedback.

🔁 Conversation Flow Example

Agent: Hi there! Which mode would you like to start with — learn, quiz, or teach back?
User: Learn variables.
Agent (Matthew): Sure! Variables store values so you can reuse them later…

User: Switch to quiz.
Agent (Alicia): Okay! What is a variable and why is it useful?

User: Teach back loops.
Agent (Ken): Great! Explain loops to me in your own words.

User: [Explains]
Agent: Nice job! You explained the basic idea well — but try to include how loops help repeat actions.

📦 Data & Content

All concepts loaded from day4_tutor_content.json

No extra content should be invented

All explanations & questions strictly come from JSON fields

🧱 Tech Stack

Backend: Python

Learning Engine: JSON-driven content lookup

Voices: Murf Falcon (Matthew, Alicia, Ken)

State Manager: Keeps track of active mode

LiveKit / Gemini / STT (if used in your challenge setup)

🛠 Setup Instructions
Backend Setup
cd Day_4/backend
uv sync
cp .env.example .env.local


Add in .env.local:

MURF_API_KEY=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
GOOGLE_API_KEY=


Run agent:

uv run python src/agent_day4.py dev

Content File Setup

Place course JSON here:

shared-data/day4_tutor_content.json
