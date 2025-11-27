# 📘 Day 7 – Fraud Alert AI Voice Agent

10 Days of AI Voice Agents Challenge – Murf Falcon + LiveKit

# 📌 Overview

Day 7 continues the development of the Fraud Alert Voice Agent, designed to simulate a real bank fraud verification call.

The agent speaks naturally, verifies the user, explains the suspicious transaction, and updates the fraud status in real time.
All data is stored inside a JSON-based database for easy persistence.

This is the standard version — clean, simple, and fully functional.

# 🚀 Features
1. Fraud Verification Call Flow

The agent performs a complete fraud verification workflow:

Greets the user

Asks for their name

Retrieves the fraud case from fraud_db.json

Reads the suspicious transaction

Asks: “Was this you?”

Marks the transaction as fraud or genuine

Returns a clear summary at the end

2. JSON Fraud Database

All fraud cases are stored inside fraud_db.json, including:

User profile

Suspicious transaction details

Current status (pending → fraud/genuine)

Timestamp of the update

3. Natural Conversation Handling

The agent understands and responds to:

“Yes” → Mark as genuine

“No” → Mark as fraud

“Repeat” → Read the transaction again

“Stop” → End the call with a summary

No complex logic — just smooth, realistic communication.

4. Real-Time Voice Pipeline

Built with a reliable low-latency stack:

Deepgram – Speech-to-Text

Murf Falcon – Ultra-fast voice output

Gemini 2.5 Flash – LLM reasoning

LiveKit Agents – Real-time audio interaction

# 📂 Project Structure
/day-7
│
├── agent.py          # Main fraud agent logic
├── fraud_db.json     # Fraud case database
└── README.md         # Documentation

# ✅ What’s Working in Day 7

Full fraud alert workflow

Real-time STT → LLM → TTS pipeline

Natural yes/no decision-making

Database write/update

Clean final fraud summary

Smooth, human-like voice interaction

# 📌 Notes

This is the basic Day 7 version (as requested)

No multi-case handling or advanced fraud logic included

Fully compatible with future upgrades
