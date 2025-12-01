# 🎭 Day 10 – AI Voice Improv Battle Agent (Grand Line Edition)

Welcome to the grand finale of my 10 Days of AI Voice Agents Challenge —
and for the final build, I went full anime × pirate energy! 🏴‍☠️🔥

Today, I built a complete AI Improv Battle Voice Agent inspired by One Piece–style adventure shows — powered by
Murf Falcon TTS + LiveKit Agents + Gemini + Deepgram.

This agent behaves like a dramatic anime host / pirate captain and guides the user through 3 rounds of improv acting.

This project combines:

Real-time voice recognition

Scenario generation

State machine architecture

Live dialogue

Pirate energy ⚔️😂

#🚀 What This Agent Can Do
```🧠 1. Runs a Full Improv Battle Show

The AI hosts a 3-round improv game, each round containing:

🎭 A new story scenario

🎤 User’s performance (live speech)

⚡ The AI’s dramatic reaction

🏁 Summary in the finale
```
# 🗺️ 2. Generates One Piece–Style Scenarios

The agent creates energetic, anime-like prompts such as:

A parrot telepathically leaking the captain’s secrets

Selling chopsticks to a stubborn swordsman

Navigating the ship toward a floating tea stall

Hosting a morale chant that makes an admiral cry laughing

Every scenario hits with the classic “grand adventure” vibe.


# 🎤 3. Reacts to the Player’s Performance

After you act, the AI:

Delivers supportive, neutral, or pirate-style critique

References your lines

Encourages you to push the energy

Adds anime-style flair (“That spirit could split the sea!” ⚡)

# 🔁 4. Maintains Full Session State

Internally it tracks:

Session ID

Player name

Current round

Round transcript

Reactions

History & timing

# 🎬 5. Finale Summary

At the end, the AI creates:

Highlights of each round

Praise + critiques

A pirate-style closing speech 🎉

# 🧩 How It Works (Architecture)

The system is built on a Python state machine, powered by:

Tools (start_show, next_scenario, react_to_improv, end_show)

Round progression logic

Random scenario selection

Reaction-style selector

Transcript-based feedback engine

Voice agent runtime handles:

Speech detection

STT → LLM → TTS loop

Real-time messaging

#🛠️ Tech Stack

🔊 Voice & Speech

Deepgram Nova-3 STT (speech-to-text)

Murf Falcon TTS (Dramatic style, fast output)

Silero VAD + Multilingual Turn Detection

🧠 LLM

Google Gemini 2.5 Flash

☁️ Runtime

LiveKit Agents

⚙️ Logic Engine

Custom Python improv engine

State machine

Scenario generator

Reaction system

Round management

#📁 File Structure (Key Files)
```
backend/
└── agent_onepiece_improv.py     # Main improv agent
└── ... (runtime, modules, plugins)

frontend/
└── components/                  # UI (React)
└── welcome-view.tsx
└── session-view.tsx
└── app.tsx
```
```
# 🎮 How to Run Locally
1️⃣ Install
pip install -r requirements.txt
npm install

2️⃣ Start Backend
python agent_onepiece_improv.py

3️⃣ Start Frontend
npm run dev

4️⃣ Open App
http://localhost:3000
``` 
# 🎉 Final Thoughts

Day 10 was the wildest, funniest, and most challenging build of the whole series.
Combining anime energy with voice-driven AI felt like building my own AI pirate show host.

This marks the completion of my 10 Days of AI Voice Agents Challenge — what a journey! 🚀🔥

🏷️ Tags
