# ======================================================
# 🍽️ DAY 7: FOOD & GROCERY ORDERING AGENT (JSON backend, Indian catalog)
# 🛒 "Tushar QuickCart" - JSON persistence (catalog.json + orders.json)
# Assistant: Amit (with fuzzy search)
# ======================================================

import os
import json
import uuid
import asyncio
import logging
import re
import string
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Annotated
from difflib import get_close_matches, SequenceMatcher

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

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("tushar_quickcart_agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

load_dotenv(".env.local")

# -------------------------
# Paths (data directory under backend/data/)
# -------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # backend/src
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
CURRENCY = "INR"

os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------
# JSON helpers
# -------------------------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            with open(path, "w", encoding="utf-8") as fw:
                json.dump(default, fw, indent=2, ensure_ascii=False)
            return default

def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

# -------------------------
# Seed catalog (Tushar QuickCart)
# -------------------------
SAMPLE_CATALOG = {
    "meta": {"store_name": "Tushar QuickCart", "currency": CURRENCY},
    "items": [
        {"id": "milk-amul-1l", "name": "Amul Taaza Milk", "category": "Dairy", "price": 72.00, "brand": "Amul", "size": "1L", "units": "pack",
         "tags": ["dairy", "milk", "amul", "taaza"]},
        {"id": "paneer-200g", "name": "Amul Malai Paneer", "category": "Dairy", "price": 95.00, "brand": "Amul", "size": "200g", "units": "pack",
         "tags": ["paneer", "amul", "veg"]},
        {"id": "butter-100g", "name": "Amul Butter", "category": "Dairy", "price": 58.00, "brand": "Amul", "size": "100g", "units": "pack",
         "tags": ["butter", "amul"]},
        {"id": "curd-400g", "name": "Mother Dairy Dahi", "category": "Dairy", "price": 40.00, "brand": "Mother Dairy", "size": "400g", "units": "cup",
         "tags": ["dahi", "curd", "mother dairy"]},
        {"id": "atta-5kg", "name": "Aashirvaad Whole Wheat Atta", "category": "Staples", "price": 245.00, "brand": "Aashirvaad", "size": "5kg", "units": "bag",
         "tags": ["atta", "flour", "roti"]},
        {"id": "rice-basmati-1kg", "name": "India Gate Basmati Rice", "category": "Staples", "price": 160.00, "brand": "India Gate", "size": "1kg", "units": "bag",
         "tags": ["rice", "basmati"]},
        {"id": "dal-toor-1kg", "name": "Tata Sampann Toor Dal", "category": "Staples", "price": 185.00, "brand": "Tata", "size": "1kg", "units": "pack",
         "tags": ["dal", "toor", "tata"]},
        {"id": "salt-1kg", "name": "Tata Salt", "category": "Staples", "price": 28.00, "brand": "Tata", "size": "1kg", "units": "pack",
         "tags": ["salt", "essential"]},
        {"id": "sugar-1kg", "name": "Madhur Sugar", "category": "Staples", "price": 60.00, "brand": "Madhur", "size": "1kg", "units": "pack",
         "tags": ["sugar", "madhur"]},
        {"id": "maggi-masala", "name": "Maggi 2-Minute Noodles", "category": "Instant Food", "price": 14.00, "brand": "Nestle", "size": "70g", "units": "pack",
         "tags": ["maggi", "noodles", "masala"]},
        {"id": "biscuits-marie", "name": "Britannia Marie Gold", "category": "Snacks", "price": 35.00, "brand": "Britannia", "size": "250g", "units": "pack",
         "tags": ["biscuits", "marie"]},
        {"id": "chips-lays", "name": "Lays Magic Masala", "category": "Snacks", "price": 20.00, "brand": "Lays", "size": "50g", "units": "pack",
         "tags": ["chips", "lays"]},
        {"id": "tea-250g", "name": "Red Label Tea", "category": "Beverages", "price": 140.00, "brand": "Brooke Bond", "size": "250g", "units": "pack",
         "tags": ["tea", "chai", "red label"]},
        {"id": "potato-1kg", "name": "Fresh Potatoes", "category": "Vegetables", "price": 40.00, "brand": "", "size": "1kg", "units": "kg",
         "tags": ["potato", "potatoes", "aloo", "veg"]},
        {"id": "onion-1kg", "name": "Fresh Onions", "category": "Vegetables", "price": 55.00, "brand": "", "size": "1kg", "units": "kg",
         "tags": ["onion", "pyaz", "veg"]},
        {"id": "tomato-1kg", "name": "Fresh Tomatoes", "category": "Vegetables", "price": 60.00, "brand": "", "size": "1kg", "units": "kg",
         "tags": ["tomato", "tamatar", "veg"]},
        {"id": "ginger-100g", "name": "Fresh Ginger", "category": "Vegetables", "price": 20.00, "brand": "", "size": "100g", "units": "g",
         "tags": ["ginger", "adrak", "veg", "chai"]},
    ]
}

def seed_catalog_if_missing():
    catalog = load_json(CATALOG_FILE, SAMPLE_CATALOG)
    if "items" not in catalog or not catalog["items"]:
        save_json(CATALOG_FILE, SAMPLE_CATALOG)
        logger.info("✅ Seeded sample catalog.json for Tushar QuickCart")
    else:
        if "meta" not in catalog:
            catalog["meta"] = SAMPLE_CATALOG["meta"]
            save_json(CATALOG_FILE, catalog)

def ensure_orders_file():
    orders = load_json(ORDERS_FILE, [])
    if not isinstance(orders, list):
        save_json(ORDERS_FILE, [])

seed_catalog_if_missing()
ensure_orders_file()

# -------------------------
# Models & userdata
# -------------------------
@dataclass
class CartItem:
    item_id: str
    name: str
    unit_price: float
    quantity: int = 1
    notes: str = ""

@dataclass
class Userdata:
    cart: List[CartItem] = field(default_factory=list)
    customer_name: Optional[str] = None
    last_order_id: Optional[str] = None

# -------------------------
# Recipe map & helpers
# -------------------------
RECIPE_MAP = {
    "chai": ["milk-amul-1l", "tea-250g", "sugar-1kg", "ginger-100g"],
    "maggi": ["maggi-masala"],
    "paneer butter masala": ["paneer-200g", "butter-100g", "tomato-1kg"],
    "dal chawal": ["dal-toor-1kg", "rice-basmati-1kg"],
}

_NUMBER_WORDS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
}

def _parse_servings_from_text(text: str) -> int:
    text = (text or "").lower()
    m = re.search(r"for\s+(\d+)", text)
    if m:
        try:
            return max(1, int(m.group(1)))
        except Exception:
            pass
    for w,num in _NUMBER_WORDS.items():
        if f"for {w}" in text:
            return num
    return 1

# -------------------------
# Fuzzy search helpers
# -------------------------
def _normalize_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = s.translate(str.maketrans("", "", string.punctuation))
    # simple plural -> singular attempt: potatoes->potato, tomatoes->tomato
    if s.endswith("ies"):
        s = s[:-3] + "y"
    elif s.endswith("oes"):
        s = s[:-2]
    elif s.endswith("es") and len(s) > 4:
        s = s[:-2]
    elif s.endswith("s") and len(s) > 3:
        s = s[:-1]
    # replace bilingual synonyms
    s = s.replace("tamatar", "tomato").replace("aloo", "potato").replace("pyaz", "onion").replace("adrak", "ginger")
    return s

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def _search_items_fuzzy(query: str, limit=20, threshold=0.55):
    """
    Returns list of matching items (dicts) from catalog using a combination of:
    - exact substring match
    - tag match
    - fuzzy name match via SequenceMatcher
    """
    q = _normalize_text(query)
    catalog = load_json(CATALOG_FILE, SAMPLE_CATALOG)
    items = catalog.get("items", [])
    scored = []
    for it in items:
        name_norm = _normalize_text(it.get("name",""))
        id_norm = _normalize_text(it.get("id",""))
        tags = [ _normalize_text(t) for t in it.get("tags",[]) ]
        score = 0.0
        # exact id or name substring
        if q in name_norm or q in id_norm or any(q == t or q in t for t in tags):
            score += 1.0
        # partial substring
        if q in name_norm:
            score += 0.8
        # tag match boosts
        if any(q in t for t in tags):
            score += 0.6
        # fuzzy match on name
        sim = _similar(q, name_norm)
        if sim > threshold:
            score += sim
        # also allow close matches using difflib
        close = get_close_matches(q, [name_norm] + tags + [id_norm], n=1, cutoff=threshold)
        if close:
            score += 0.5
        if score > 0:
            scored.append((score, it))
    # sort by score descending then return top
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _,it in scored][:limit]

# -------------------------
# Orders JSON helpers
# -------------------------
def append_order_json(order_obj: dict):
    orders = load_json(ORDERS_FILE, [])
    orders.append(order_obj)
    save_json(ORDERS_FILE, orders)

def update_order_json(order_id: str, **kwargs) -> bool:
    orders = load_json(ORDERS_FILE, [])
    changed = False
    for o in orders:
        if o.get("order_id") == order_id:
            o.update(kwargs)
            o["updated_at"] = datetime.utcnow().isoformat() + "Z"
            changed = True
            break
    if changed:
        save_json(ORDERS_FILE, orders)
    return changed

def get_order_json(order_id: str) -> Optional[dict]:
    orders = load_json(ORDERS_FILE, [])
    for o in orders:
        if o.get("order_id") == order_id:
            return o
    return None

def list_orders_json(limit=10, customer_name: Optional[str]=None):
    orders = load_json(ORDERS_FILE, [])
    if customer_name:
        return [o for o in reversed(orders) if o.get("customer_name","").lower()==customer_name.lower()][:limit]
    return list(reversed(orders))[:limit]

# -------------------------
# Simulation background
# -------------------------
STATUS_FLOW = ["received", "confirmed", "shipped", "out_for_delivery", "delivered"]

async def simulate_delivery_flow(order_id: str):
    logger.info(f"🔄 [Simulation] Starting simulation for {order_id}")
    await asyncio.sleep(5)
    for status in STATUS_FLOW[1:]:
        o = get_order_json(order_id)
        if not o:
            logger.info(f"⚠️ Order {order_id} missing; stopping simulation.")
            return
        if o.get("status") == "cancelled":
            logger.info(f"🛑 [Simulation] Order {order_id} cancelled; stopping.")
            return
        update_order_json(order_id, status=status)
        logger.info(f"🚚 [Simulation] Order {order_id} -> {status}")
        await asyncio.sleep(5)
    logger.info(f"✅ [Simulation] Order {order_id} delivered.")

# -------------------------
# Cart helpers
# -------------------------
def cart_total(cart: List[CartItem]) -> float:
    return round(sum(ci.unit_price * ci.quantity for ci in cart), 2)

# -------------------------
# AGENT TOOLS (function_tool) - USE FUZZY SEARCH
# -------------------------
@function_tool
async def find_item(ctx: RunContext[Userdata], query: Annotated[str, Field(description="Name or partial name (e.g. 'milk')")]) -> str:
    matches = _search_items_fuzzy(query)
    if not matches:
        return f"Sorry, I couldn't find \"{query}\" in our catalog. Would you like to try a similar item or a different name?"
    lines = []
    for it in matches[:10]:
        lines.append(f"- {it['name']} (id: {it['id']}) — ₹{it['price']:.2f} — {it.get('size','')}")
    return "Found:\n" + "\n".join(lines) + "\nWhat would you like to add to your cart?"

@function_tool
async def add_to_cart(ctx: RunContext[Userdata], item_id: Annotated[str, Field(description="Catalog item id or name")], quantity: Annotated[int, Field(description="Quantity", default=1)] = 1, notes: Annotated[str, Field(description="Optional notes")] = "") -> str:
    # allow item_id to be fuzzy name too
    # if id not found, try fuzzy search and pick top match
    item = _find_item_by_id(item_id) if isinstance(item_id, str) and "-" in item_id else None
    if not item:
        fuzzy = _search_items_fuzzy(item_id, limit=1)
        if fuzzy:
            item = fuzzy[0]
    if not item:
        return f"Item '{item_id}' not found in catalog."
    # merge if exists
    for ci in ctx.userdata.cart:
        if ci.item_id.lower() == item["id"].lower():
            ci.quantity += int(quantity)
            if notes:
                ci.notes = notes
            total = cart_total(ctx.userdata.cart)
            return f"Updated '{ci.name}' to {ci.quantity}. Cart total: ₹{total:.2f}"
    ci = CartItem(item_id=item["id"], name=item["name"], unit_price=float(item["price"]), quantity=int(quantity), notes=notes)
    ctx.userdata.cart.append(ci)
    total = cart_total(ctx.userdata.cart)
    return f"Added {quantity} x '{ci.name}' to cart. Cart total: ₹{total:.2f}"

# The rest of tools are same as previous file (remove_from_cart, update_cart_quantity, show_cart, add_recipe, ingredients_for, place_order, cancel_order, get_order_status, order_history)
# For brevity we re-include them unchanged below.

@function_tool
async def remove_from_cart(ctx: RunContext[Userdata], item_id: Annotated[str, Field(description="Catalog item id")]) -> str:
    before = len(ctx.userdata.cart)
    ctx.userdata.cart = [ci for ci in ctx.userdata.cart if ci.item_id.lower() != item_id.lower()]
    after = len(ctx.userdata.cart)
    if before == after:
        return f"Item '{item_id}' was not in your cart."
    total = cart_total(ctx.userdata.cart)
    return f"Removed item '{item_id}' from cart. Cart total: ₹{total:.2f}"

@function_tool
async def update_cart_quantity(ctx: RunContext[Userdata], item_id: Annotated[str, Field(description="Catalog item id")], quantity: Annotated[int, Field(description="New quantity")]) -> str:
    if quantity < 1:
        return await remove_from_cart(ctx, item_id)
    for ci in ctx.userdata.cart:
        if ci.item_id.lower() == item_id.lower():
            ci.quantity = int(quantity)
            total = cart_total(ctx.userdata.cart)
            return f"Updated '{ci.name}' quantity to {ci.quantity}. Cart total: ₹{total:.2f}"
    return f"Item '{item_id}' not found in cart."

@function_tool
async def show_cart(ctx: RunContext[Userdata]) -> str:
    if not ctx.userdata.cart:
        return "Your cart is empty."
    lines = []
    for ci in ctx.userdata.cart:
        lines.append(f"- {ci.quantity} x {ci.name} @ ₹{ci.unit_price:.2f} each = ₹{ci.unit_price * ci.quantity:.2f}")
    total = cart_total(ctx.userdata.cart)
    return "Your cart:\n" + "\n".join(lines) + f"\nTotal: ₹{total:.2f}"

@function_tool
async def add_recipe(ctx: RunContext[Userdata], dish_name: Annotated[str, Field(description="Dish name like 'chai'")]) -> str:
    key = dish_name.strip().lower()
    if key not in RECIPE_MAP:
        return f"No recipe for '{dish_name}'. Try 'chai', 'maggi', or 'paneer butter masala'."
    added = []
    for iid in RECIPE_MAP[key]:
        it = _find_item_by_id(iid)
        if not it:
            continue
        found = False
        for ci in ctx.userdata.cart:
            if ci.item_id.lower() == iid.lower():
                ci.quantity += 1
                found = True
                break
        if not found:
            ctx.userdata.cart.append(CartItem(item_id=it["id"], name=it["name"], unit_price=float(it["price"]), quantity=1))
        added.append(it["name"])
    total = cart_total(ctx.userdata.cart)
    return f"Added ingredients for '{dish_name}': {', '.join(added)}. Cart total: ₹{total:.2f}"

@function_tool
async def ingredients_for(ctx: RunContext[Userdata], request: Annotated[str, Field(description="NL request like 'ingredients for chai for two'")]) -> str:
    text = (request or "").strip()
    servings = _parse_servings_from_text(text)
    m = re.search(r"ingredients? for (.+)", text, re.I)
    dish = m.group(1) if m else text
    dish = re.sub(r"for\s+\w+(?: people| person| persons)?", "", dish, flags=re.I).strip()
    key = dish.lower()
    item_ids = []
    if key in RECIPE_MAP:
        item_ids = RECIPE_MAP[key]
    else:
        found = _search_items_fuzzy(dish, limit=6)
        item_ids = [f["id"] for f in found]
    if not item_ids:
        return f"Sorry, couldn't find ingredients for '{request}'. Try simpler phrasing."
    added = []
    for iid in item_ids:
        it = _find_item_by_id(iid)
        if not it:
            continue
        found = False
        for ci in ctx.userdata.cart:
            if ci.item_id.lower() == iid.lower():
                ci.quantity += servings
                found = True
                break
        if not found:
            ctx.userdata.cart.append(CartItem(item_id=it["id"], name=it["name"], unit_price=float(it["price"]), quantity=servings))
        added.append(it["name"])
    total = cart_total(ctx.userdata.cart)
    return f"I've added {', '.join(added)} to your cart for '{dish}' (servings: {servings}). Cart total: ₹{total:.2f}"

@function_tool
async def place_order(ctx: RunContext[Userdata], customer_name: Annotated[str, Field(description="Customer name")], address: Annotated[str, Field(description="Delivery address")]) -> str:
    if not ctx.userdata.cart:
        return "Your cart is empty."
    order_id = str(uuid.uuid4())[:8]
    placed_at = datetime.utcnow().isoformat() + "Z"
    total = cart_total(ctx.userdata.cart)
    order = {
        "order_id": order_id,
        "timestamp": placed_at,
        "total": total,
        "customer_name": customer_name,
        "address": address,
        "status": "received",
        "created_at": placed_at,
        "updated_at": placed_at,
        "items": [{"item_id": ci.item_id, "name": ci.name, "quantity": ci.quantity, "unit_price": ci.unit_price, "notes": ci.notes} for ci in ctx.userdata.cart]
    }
    append_order_json(order)
    ctx.userdata.cart = []
    ctx.userdata.customer_name = customer_name
    ctx.userdata.last_order_id = order_id
    try:
        asyncio.create_task(simulate_delivery_flow(order_id))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.get_event_loop().call_soon_threadsafe(lambda: asyncio.create_task(simulate_delivery_flow(order_id)))
    return f"Order placed! ID: {order_id}. Total: ₹{total:.2f}. Tracking will update automatically."

@function_tool
async def cancel_order(ctx: RunContext[Userdata], order_id: Annotated[str, Field(description="Order ID to cancel")]) -> str:
    o = get_order_json(order_id)
    if not o:
        return f"No order found with id {order_id}."
    status = o.get("status")
    if status == "delivered":
        return f"Order {order_id} already delivered; cannot cancel."
    if status == "cancelled":
        return f"Order {order_id} is already cancelled."
    update_order_json(order_id, status="cancelled")
    return f"Order {order_id} has been cancelled."

@function_tool
async def get_order_status(ctx: RunContext[Userdata], order_id: Annotated[str, Field(description="Order ID to check")]) -> str:
    o = get_order_json(order_id)
    if not o:
        return f"No order found with id {order_id}."
    return f"Order {order_id} status: {o.get('status')}. Last updated: {o.get('updated_at')}"

@function_tool
async def order_history(ctx: RunContext[Userdata], customer_name: Annotated[Optional[str], Field(description="Optional customer name")] = None) -> str:
    rows = list_orders_json(limit=5, customer_name=customer_name)
    if not rows:
        return "No orders found."
    lines = []
    for r in rows:
        lines.append(f"- {r['order_id']} | ₹{r['total']:.2f} | {r.get('status')} | {r.get('created_at')}")
    prefix = "Recent Orders"
    if customer_name:
        prefix += f" for {customer_name}"
    return prefix + ":\n" + "\n".join(lines)

# -------------------------
# Agent Definition (assistant name: Amit)
# -------------------------
class FoodAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            You are 'Amit', assistant for 'Tushar QuickCart' (Indian grocery).
            - Help users search catalog, add to cart, add recipe ingredients, place orders.
            - When placing order ask for name and address, then confirm placement.
            - Support cancelling orders if not delivered.
            - Support 'where is my order' using simulated tracking (advances automatically).
            Be polite, confirm cart changes, and ask clarifying questions when necessary.
            """,
            tools=[find_item, add_to_cart, remove_from_cart, update_cart_quantity, show_cart, add_recipe, ingredients_for, place_order, cancel_order, get_order_status, order_history],
        )

# -------------------------
# Entrypoint
# -------------------------
def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
    except Exception:
        logger.warning("VAD prewarm failed; continuing.")

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info("🚀 STARTING TUSHAR QUICKCART (JSON backend) — assistant: Amit (fuzzy search enabled)")
    userdata = Userdata()
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-marcus", style="Conversational", text_pacing=True),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata.get("vad"),
        userdata=userdata,
    )
    await session.start(agent=FoodAgent(), room=ctx.room, room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
