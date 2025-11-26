# ☕ Day 2 — Coffee Shop Barista Voice Agent

Welcome to the Brew & Bean Cafe — Barista Voice Agent!
This agent takes coffee orders through voice interaction, validates order completeness, stores them in JSON format, and provides a seamless café ordering experience.

# 🧭 Overview

The Day 2 Barista Voice Agent simulates a real coffee shop ordering workflow.
Users speak their order, the agent confirms details, checks for missing information, and saves every order into a structured JSON file. It also supports real-time logging for staff.

Core goals:

Receive coffee orders

Ask follow-up questions (size, type, milk, sugar, add-ons)

Validate order completeness

Confirm final order

Save structured JSON data

#☕ Example Drinks Supported

Americano

Cappuccino

Latte

Espresso

Cold Coffee

Mocha

(+ you can add more in your menu JSON)

# 📋 Barista Agent Features
✔ Natural voice ordering

Understands beverage, size, milk preferences, sweetness, toppings, etc.

✔ Smart follow-up questioning

Asks for missing details like:

“Which size?”

“Hot or iced?”

“What milk would you like?”

✔ Order validation

Ensures order is fully complete before finalizing.

✔ Order confirmation

Repeats the final order in a natural barista style.

✔ JSON order logging

Every order is saved in a file like:

backend/orders/order_2025-11-26.json

✔ Voice support

Uses STT + TTS depending on your stack (LiveKit / Murf / Deepgram).

# 📦 Order Data Saved (JSON Example)
'''{
  "order_id": "2025-11-26T12:49:33",
  "customer_request": "I want a cold coffee with extra ice",
  "drink": "Cold Coffee",
  "size": "Medium",
  "temperature": "Cold",
  "milk": "None",
  "sugar": "Normal",
  "addons": ["Extra Ice"],
  "status": "completed"
}'''

# 🔁 Conversation Flow Example

User: Hi, I want a cappuccino.
Agent: Sure! What size would you like — small, medium, or large?
User: Medium.
Agent: Great! Any sugar preference?
User: 1 spoon.
Agent: Noted. Would you like any add-ons?
User: No.
Agent: Perfect — your medium cappuccino with 1 spoon sugar is being prepared!

# 🤖 Agent Logic (Modes)

listen_order → understand the user’s request

ask_missing_info → ask about size, sugar, milk, etc.

validate_order → check if all fields are complete

confirm_order → speak back final order

save_order → write JSON entry

# 🧱 Tech Stack

Backend: Python

Voice Pipeline: LiveKit Agents / Google / Deepgram

TTS: Murf Falcon (optional)

Storage: JSON File Logging

Frontend: Simple HTML/CSS/JS

⚙️ Backend Setup
cd Day_2/backend
uv sync
cp .env.example .env.local


Required values in .env.local:

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
MURF_API_KEY=
DEEPGRAM_API_KEY=
GOOGLE_API_KEY=


Run backend:

uv run python src/agent_day2.py dev

# 🖥️ Frontend Setup

cd Day_2/frontend
pnpm install
cp .env.example .env.local
pnpm dev
