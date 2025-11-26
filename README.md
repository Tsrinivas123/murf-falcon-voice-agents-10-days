🌿 Day 3 — Wellness Companion Agent

AI agent that acts as your personal wellness buddy — tracking mood, offering meditation, hydration reminders, and giving positive support.

📌 Overview

The Wellness Companion Agent interacts with users via voice or text and helps them improve daily mental & physical well-being.
It uses state management, stores user logs in JSON, and gives context-aware responses.

✨ Features
🧠 Core Capabilities

Mood tracking (happy, low, stressed, neutral, etc.)

Hydration reminders

Guided breathing & meditation prompts

Daily wellness score summary

Saves sessions to JSON

Voice input/output (TTS + STT) enabled

Simple flow-based state machine

🎙️ Interaction Modes

Text chat

Voice mode (speech-to-text + text-to-speech)

🗂️ Repository Structure
Day-3-Wellness-Agent/
│
├── backend/
│   ├── app.py
│   ├── agent/
│   │   ├── wellness_agent.py
│   │   ├── state_manager.py
│   │   └── utils.py
│   ├── data/
│   │   └── wellness_logs.json
│   ├── requirements.txt
│   └── README.md   ← (backend README optional)
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── README.md   ← (frontend README optional)
│
└── README.md  ← main README (this file)

🧩 How It Works
1️⃣ User Message → Mood Analysis

Agent reads user input → detects emotional tone → updates state.

2️⃣ State Manager Logic

Decides what the agent should respond with:

If user feels stressed → suggest breathing exercise

If low mood → give encouragement

If positive → reinforce good habits

Every 2 hours → water reminder (optional)

3️⃣ Store Log

Every session is saved in data/wellness_logs.json.

4️⃣ Output to User

Output can be:

Supportive text

Voice response

Guided prompts

🚀 Run the Backend
Install
cd backend
pip install -r requirements.txt

Start Server
python app.py


Server will run on:

http://localhost:8000

🖥️ Run the Frontend

Just open the file:

frontend/index.html


It will connect to the backend API.

🧪 API Endpoints
▶️ /chat (POST)

Send user message → get agent response.

Request

{
  "message": "I'm feeling stressed"
}


Response

{
  "reply": "I understand. Let's try a short 30-second breathing exercise together...",
  "mood": "stressed",
  "recommendation": "breathing_exercise"
}
