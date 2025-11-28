# 🛒 Tushar QuickCart – Day 7
AI Food & Grocery Ordering Voice Agent (LiveKit + Murf + Deepgram + Gemini)

This project is a fully conversational real-time food & grocery ordering voice agent, built as part of the Murf AI Voice Agent Challenge – Day 7.

The agent can search items, add to cart, suggest ingredients, place orders, track deliveries, and store everything in JSON files — all using natural voice.

##🚀 Features
#🗣️ Conversational Voice Agent ("Amit")

Understands natural English like:

“Do you have bread?”

“Add 2 pasta”

“Show my cart”

Fuzzy search for items, brands, tags (even with typos)

Friendly quick-commerce style behaviour (like Instamart/Blinkit)

#📦 Shopping Cart + Orders

Add, update, remove items

Add ingredients for dishes automatically

Calculate totals

Store all orders in orders.json

Automatically simulates tracking:

received → confirmed → shipped → out_for_delivery → delivered

##📚 JSON Storage Backend

Product catalog stored in catalog.json

Orders stored in orders.json

Safe read/write using atomic updates

##🎤 Real-Time Voice Pipeline

Deepgram STT → Speech to text

Gemini 2.5 Flash → Conversational logic & reasoning

Murf Falcon TTS → Fast human-like voice

LiveKit Agents → Real-time low-latency interaction

##📁 Project Structure
```backend/
│
├── src/
│   ├── agent.py          # Main agent logic (Amit)
│   ├── database.py       # (removed in day 7)
│   └── ...              
│
├── data/
│   ├── catalog.json      # Product catalog
│   └── orders.json       # Order storage
│
└── README.md             # Project documentation
```

##🧠 How It Works
1️⃣ User speaks → Deepgram converts speech to text
2️⃣ Gemini processes the request
3️⃣ The agent calls tools like:

`` find_item

add_to_cart

show_cart

place_order

cancel_order ```

4️⃣ Murf Falcon TTS speaks the response
5️⃣ Orders get updated & tracked in JSON

## 💬 Example Conversation
User: Amit, do you have bread?
Amit: Yes, I found Whole Wheat Bread.

User: Add 2 breads.
Amit: Added 2 items to your cart.

User: Add one peanut butter.
User: Show my cart.
User: Place my order under the name Tushar.
User: Track my order.

## 🛠️ Setup & Run
1️⃣ Install dependencies
pip install -r requirements.txt

2️⃣ Create .env.local with API keys
DEEPGRAM_API_KEY=
GOOGLE_API_KEY=
MURF_API_KEY=
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_SECRET=

3️⃣ Run the agent
python agent.py

## 🎯 Why This Project?

Day 7 focused on:

Creating a realistic grocery ordering experience

Combining fuzzy search + JSON persistence

Full end-to-end voice flow

Clean carts, orders, and tracking simulation

This brings real-world quick-commerce behavior into a simple but powerful voice agent.

## 🏷️ Credits

Murf Falcon TTS

Deepgram STT

Google Gemini

LiveKit Agents

Built for the Murf AI Voice Agent Challenge
