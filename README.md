# Murf Falcon Voice Agents — 10 Days Challenge

This repository contains my submissions for the **Murf AI Voice Agent Challenge**, where I build **10 AI Voice Agents in 10 Days** using the fastest TTS engine — **Murf Falcon** and **LiveKit Agents**.

---

## 🚀 Project Structure

murf-falcon-voice-agents-10-days/
├── backend/ # LiveKit Agents backend with Murf Falcon TTS
├── frontend/ # Next.js/React frontend for real-time voice interaction
├── start_app.sh # Script to run entire project
└── demo/ # Demo videos for each day's task

yaml
Copy code

---

## 🧠 Tech Stack

### **Backend**
- Python (LiveKit Agent Starter)
- Murf Falcon TTS (Ultra-fast speech synthesis)
- Deepgram STT (optional)
- Gemini / OpenAI LLMs (optional)
- WebRTC, Turn detection, noise cancellation

### **Frontend**
- Next.js 15 / React
- LiveKit Client SDK
- Real-time audio streaming UI
- Mic input, Audio visualizer, Dark/Light theme

---

## ⚡ Quick Start

### 1️⃣ Clone the Repo
```bash
git clone https://github.com/Tsrinivas123/murf-falcon-voice-agents-10-days.git
cd murf-falcon-voice-agents-10-days
2️⃣ Backend Setup
bash
Copy code
cd backend

# Install dependencies
uv sync   # or use pip if uv not available

# Create environment
cp .env.example .env.local

# Add your keys inside .env.local:
# LIVEKIT_URL=
# LIVEKIT_API_KEY=
# LIVEKIT_API_SECRET=
# MURF_API_KEY=
# DEEPGRAM_API_KEY= (optional)
# GOOGLE_API_KEY= (optional)

# Download model assets
uv run python src/agent.py download-files

# Run backend (development mode)
uv run python src/agent.py dev
3️⃣ Frontend Setup
bash
Copy code
cd ../frontend

pnpm install
cp .env.example .env.local      # Add LiveKit keys here too

pnpm dev
# Open: http://localhost:3000
🏃 Run Everything Together
bash
Copy code
chmod +x start_app.sh
./start_app.sh
This starts:

LiveKit Server (dev)

Backend Agent

Frontend UI

🎥 Demo Videos
All daily demo videos will be added inside:

bash
Copy code
/demo/day1-demo.mp4
/demo/day2-demo.mp4
...
🔗 Challenge Details
This project is part of the Murf AI Voice Agent Challenge.
Follow my daily updates on LinkedIn using the hashtags:

#MurfAIVoiceAgentsChallenge

#10DaysofAIVoiceAgents