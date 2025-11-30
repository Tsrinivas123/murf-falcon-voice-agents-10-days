# agent_tushar.py
# ======================================================
# 🎲 VOICE E-COMMERCE AGENT — Tushar Shop
# - LiveKit agent plumbing preserved (deepgram, murf, silero, MultilingualModel)
# - Tools: show_catalog, add_to_cart, show_cart, clear_cart, place_order, last_order, get_world_state
# - Per-session userdata holds continuity (cart / orders / history / session id)
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
logger = logging.getLogger("voice_shop_agent_tushar")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# -------------------------
# Simple Product Catalog (Tushar Shop)
# -------------------------
CATALOG = [
    {"id": "mug-001", "name": "Stoneware Chai Mug", "description": "Hand-glazed ceramic mug perfect for masala chai.", "price": 299, "currency": "INR", "category": "mug", "color": "blue", "sizes": []},
    {"id": "tee-001", "name": "Tushar Tee (Cotton)", "description": "Comfort-fit cotton t-shirt with subtle logo.", "price": 799, "currency": "INR", "category": "tshirt", "color": "black", "sizes": ["S", "M", "L", "XL"]},
    {"id": "hoodie-001", "name": "Cozy Hoodie", "description": "Warm pullover hoodie, fleece-lined.", "price": 1499, "currency": "INR", "category": "hoodie", "color": "grey", "sizes": ["M", "L", "XL"]},
    {"id": "mug-002", "name": "Insulated Travel Mug", "description": "Keeps chai warm on your way to work.", "price": 599, "currency": "INR", "category": "mug", "color": "white", "sizes": []},
    {"id": "hoodie-002", "name": "Black Zip Hoodie", "description": "Lightweight zip-up hoodie, black.", "price": 1299, "currency": "INR", "category": "hoodie", "color": "black", "sizes": ["S", "M", "L"]},
    {"id": "tee-002", "name": "Casual Cotton Tee", "description": "Everyday cotton t-shirt, breathable and soft.", "price": 299, "currency": "INR", "category": "tshirt", "color": "white", "sizes": ["S", "M", "L", "XL"]},
    {"id": "tee-003", "name": "Graphic Tee", "description": "Printed graphic t-shirt with vibrant design.", "price": 499, "currency": "INR", "category": "tshirt", "color": "navy", "sizes": ["S", "M", "L", "XL"]},
    {"id": "tee-004", "name": "Premium Polo Tee", "description": "Polo-style t-shirt with premium stitching.", "price": 999, "currency": "INR", "category": "tshirt", "color": "maroon", "sizes": ["M", "L", "XL"]},
    {"id": "tee-005", "name": "Summer V-neck Tee", "description": "Lightweight V-neck tee for hot days.", "price": 350, "currency": "INR", "category": "tshirt", "color": "sky", "sizes": ["S", "M", "L"]},
    {"id": "tee-006", "name": "Henley Tee", "description": "Smart casual henley style t-shirt.", "price": 699, "currency": "INR", "category": "tshirt", "color": "olive", "sizes": ["M", "L", "XL"]},
    {"id": "rain-001", "name": "Light Raincoat", "description": "Waterproof light raincoat, packable.", "price": 1299, "currency": "INR", "category": "raincoat", "color": "yellow", "sizes": ["M", "L", "XL"]},
    {"id": "rain-002", "name": "Heavy Duty Raincoat", "description": "Heavy-duty rainproof coat for monsoon.", "price": 2499, "currency": "INR", "category": "raincoat", "color": "navy", "sizes": ["L", "XL"]},
    {"id": "laptop-001", "name": "Generic Laptop (50k)", "description": "A reliable laptop suitable for everyday use.", "price": 50000, "currency": "INR", "category": "laptop", "color": "silver", "sizes": []},
    {"id": "laptop-002", "name": "Dell Inspiron (Budget)", "description": "Compact Dell laptop for students and professionals.", "price": 27800, "currency": "INR", "category": "laptop", "color": "black", "sizes": []},
    {"id": "laptop-003", "name": "Lenovo ThinkPad", "description": "Durable Lenovo laptop with strong performance.", "price": 60000, "currency": "INR", "category": "laptop", "color": "black", "sizes": []},
    {"id": "laptop-004", "name": "HP Pavilion", "description": "High-performance HP laptop for creators.", "price": 100000, "currency": "INR", "category": "laptop", "color": "silver", "sizes": []},
    {"id": "storage-001", "name": "External Hard Disk 1TB", "description": "Portable external hard disk for backups.", "price": 50000, "currency": "INR", "category": "storage", "color": "black", "sizes": []},
    {"id": "phone-001", "name": "Redmi Note (Entry)", "description": "Affordable Redmi smartphone with solid features.", "price": 12000, "currency": "INR", "category": "mobile", "color": "blue", "sizes": []},
    {"id": "phone-002", "name": "Oppo A-Series", "description": "Stylish Oppo phone with good camera.", "price": 18000, "currency": "INR", "category": "mobile", "color": "green", "sizes": []},
    {"id": "phone-003", "name": "Samsung M-Series", "description": "Mid-range Samsung phone for everyday use.", "price": 25000, "currency": "INR", "category": "mobile", "color": "black", "sizes": []},
    {"id": "phone-004", "name": "iPhone (Standard)", "description": "Apple iPhone model example (price varies by config).", "price": 50000, "currency": "INR", "category": "mobile", "color": "white", "sizes": []},
    {"id": "phone-005", "name": "Oppo Reno", "description": "Higher-end Oppo phone with premium features.", "price": 35000, "currency": "INR", "category": "mobile", "color": "black", "sizes": []},
    {"id": "phone-006", "name": "Redmi Pro", "description": "Redmi higher-tier phone with improved camera and battery.", "price": 22000, "currency": "INR", "category": "mobile", "color": "grey", "sizes": []},
    {"id": "shoes-001", "name": "Everyday Sneakers", "description": "Comfortable canvas sneakers for daily wear.", "price": 1499, "currency": "INR", "category": "shoes", "color": "white", "sizes": ["7", "8", "9", "10"]},
    {"id": "shoes-002", "name": "Running Shoes", "description": "Lightweight running shoes with breathable mesh.", "price": 2499, "currency": "INR", "category": "shoes", "color": "black", "sizes": ["7", "8", "9", "10", "11"]},
    {"id": "shoes-003", "name": "Formal Leather Shoes", "description": "Classic leather formal shoes, polished finish.", "price": 3499, "currency": "INR", "category": "shoes", "color": "brown", "sizes": ["7", "8", "9", "10", "11"]}
]

ORDERS_FILE = "orders.json"
if not os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "w") as f:
        json.dump([], f)

# -------------------------
# Per-session Userdata (shopping-centric)
# -------------------------
@dataclass
class Userdata:
    player_name: Optional[str] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    cart: List[Dict[str, Any]] = field(default_factory=list)
    orders: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

# -------------------------
# Merchant-layer helpers
# -------------------------
def _load_all_orders() -> List[Dict[str, Any]]:
    try:
        with open(ORDERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save_order(order: Dict[str, Any]):
    orders = _load_all_orders()
    orders.append(order)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)


def list_products(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    filters = filters or {}
    results = []
    query = filters.get("q")
    category = filters.get("category")
    max_price = filters.get("max_price") or filters.get("to") or filters.get("max")
    min_price = filters.get("min_price") or filters.get("from") or filters.get("min")
    color = filters.get("color")
    size = filters.get("size")

    # normalize category synonyms
    if category:
        cat = category.lower()
        if cat in ("phone", "phones", "mobile", "mobile phone", "mobiles"):
            category = "mobile"
        elif cat in ("tshirt", "t-shirts", "t-shirt", "t shirt", "tshirts", "tee", "tees"):
            category = "tshirt"
        elif cat in ("shoes", "shoe", "sneakers"):
            category = "shoes"
        elif cat in ("laptop", "laptops"):
            category = "laptop"
        else:
            category = cat

    for p in CATALOG:
        ok = True
        pcat = p.get("category", "").lower()
        if category:
            if pcat != category and category not in pcat and pcat not in category:
                ok = False
        if max_price:
            try:
                if p.get("price", 0) > int(max_price):
                    ok = False
            except Exception:
                pass
        if min_price:
            try:
                if p.get("price", 0) < int(min_price):
                    ok = False
            except Exception:
                pass
        if color and p.get("color") and p.get("color") != color:
            ok = False
        if size and (not p.get("sizes") or size not in p.get("sizes")):
            ok = False
        if query:
            q = query.lower()
            if "phone" in q or "mobile" in q:
                if p.get("category") != "mobile":
                    ok = False
            else:
                if q not in p.get("name", "").lower() and q not in p.get("description", "").lower():
                    ok = False
        if ok:
            results.append(p)
    return results


def find_product_by_ref(ref_text: str, candidates: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    ref = (ref_text or "").lower().strip()
    cand = candidates if candidates is not None else CATALOG

    wants_mobile = any(w in ref for w in ("phone", "phones", "mobile", "mobiles"))
    filtered = cand
    if wants_mobile:
        filtered = [p for p in cand if p.get("category") == "mobile"] or cand

    ordinals = {"first": 0, "second": 1, "third": 2, "fourth": 3}
    for word, idx in ordinals.items():
        if word in ref and idx < len(filtered):
            return filtered[idx]

    for p in cand:
        if p["id"].lower() == ref:
            return p

    for p in cand:
        if p.get("color") and p["color"] in ref and p.get("category") and p["category"] in ref:
            return p

    for p in filtered:
        name = p["name"].lower()
        if all(tok in name for tok in ref.split() if len(tok) > 2):
            return p
    for p in cand:
        for tok in ref.split():
            if len(tok) > 2 and tok in p["name"].lower():
                return p

    for token in ref.split():
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(filtered):
                return filtered[idx]

    for word, idx in ordinals.items():
        if word in ref and idx < len(cand):
            return cand[idx]

    return None


def create_order_object(line_items: List[Dict[str, Any]], currency: str = "INR") -> Dict[str, Any]:
    items = []
    total = 0
    for li in line_items:
        pid = li.get("product_id")
        qty = int(li.get("quantity", 1))
        prod = next((p for p in CATALOG if p["id"] == pid), None)
        if not prod:
            raise ValueError(f"Product {pid} not found")
        line_total = prod["price"] * qty
        total += line_total
        items.append({
            "product_id": pid,
            "name": prod["name"],
            "unit_price": prod["price"],
            "quantity": qty,
            "line_total": line_total,
            "attrs": li.get("attrs", {}),
        })
    order = {
        "id": f"order-{str(uuid.uuid4())[:8]}",
        "items": items,
        "total": total,
        "currency": currency,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _save_order(order)
    return order


def get_most_recent_order() -> Optional[Dict[str, Any]]:
    all_orders = _load_all_orders()
    if not all_orders:
        return None
    return all_orders[-1]

# -------------------------
# Agent Tools (function_tool)
# -------------------------

@function_tool
async def show_catalog(
    ctx: RunContext[Userdata],
    q: Annotated[Optional[str], Field(description="Search query (optional)", default=None)] = None,
    category: Annotated[Optional[str], Field(description="Category (optional)", default=None)] = None,
    max_price: Annotated[Optional[int], Field(description="Maximum price (optional)", default=None)] = None,
    color: Annotated[Optional[str], Field(description="Color (optional)", default=None)] = None,
) -> str:
    """Return a short spoken summary of matching products (name, price, id)."""
    userdata = ctx.userdata
    # normalize category synonyms
    if category:
        cat = category.lower()
        if cat in ("phone", "phones", "mobile", "mobile phone", "mobiles"):
            category = "mobile"
        elif cat in ("tshirt", "t-shirts", "t-shirt", "t shirt", "tshirts", "tee", "tees"):
            category = "tshirt"
        else:
            category = cat
    if not category and q:
        if any(w in q.lower() for w in ("phone", "phones", "mobile", "mobiles")):
            category = "mobile"
        if any(w in q.lower() for w in ("tee", "tshirt", "t-shirts", "tees")):
            category = "tshirt"
    filters = {"q": q, "category": category, "max_price": max_price, "color": color}
    prods = list_products({k: v for k, v in filters.items() if v is not None})
    if not prods:
        return "Sorry — I couldn't find any items that match. Would you like to try another search?"
    lines = [f"Here are the top {min(8, len(prods))} items I found at Tushar Shop:"]
    for idx, p in enumerate(prods[:8], start=1):
        size_info = f" (sizes: {', '.join(p['sizes'])})" if p.get('sizes') else ""
        lines.append(f"{idx}. {p['name']} — {p['price']} {p['currency']} (id: {p['id']}){size_info}")
    lines.append("You can say: 'I want the second item in size M' or 'add mug-001 to my cart, quantity 2'.")
    if any(p.get('category') == 'mobile' for p in prods):
        lines.append("To buy a phone say: 'Add phone-002 to my cart' or 'I want the second phone, quantity 1'.")
    return "\n".join(lines)


@function_tool
async def add_to_cart(
    ctx: RunContext[Userdata],
    product_ref: Annotated[str, Field(description="Reference to product: id, name, or spoken ref")],
    quantity: Annotated[int, Field(description="Quantity", default=1)] = 1,
    size: Annotated[Optional[str], Field(description="Size (optional)", default=None)] = None,
) -> str:
    """Resolve a product and add to the session cart."""
    userdata = ctx.userdata
    candidates = CATALOG
    prod = find_product_by_ref(product_ref, candidates)
    if not prod:
        return "I couldn't resolve which product you meant. Try using the item id or say 'show catalog' to hear options."
    userdata.cart.append({
        "product_id": prod["id"],
        "quantity": int(quantity),
        "attrs": {"size": size} if size else {},
    })
    userdata.history.append({
        "time": datetime.utcnow().isoformat() + "Z",
        "action": "add_to_cart",
        "product_id": prod["id"],
        "quantity": int(quantity),
    })
    return f"Added {quantity} x {prod['name']} to your cart. What would you like to do next?"


@function_tool
async def show_cart(ctx: RunContext[Userdata]) -> str:
    userdata = ctx.userdata
    if not userdata.cart:
        return "Your cart is empty. You can say 'show catalog' to browse items."
    lines = ["Items in your cart:"]
    total = 0
    for li in userdata.cart:
        p = next((x for x in CATALOG if x["id"] == li["product_id"]), None)
        if not p:
            continue
        line_total = p["price"] * li.get("quantity", 1)
        total += line_total
        sz = li.get("attrs", {}).get("size")
        sz_text = f", size {sz}" if sz else ""
        lines.append(f"- {p['name']} x {li['quantity']}{sz_text}: {line_total} INR")
    lines.append(f"Cart total: {total} INR")
    lines.append("Say 'place my order' to checkout or 'clear cart' to empty the cart.")
    return "\n".join(lines)


@function_tool
async def clear_cart(ctx: RunContext[Userdata]) -> str:
    userdata = ctx.userdata
    userdata.cart = []
    userdata.history.append({"time": datetime.utcnow().isoformat() + "Z", "action": "clear_cart"})
    return "Your cart has been cleared. What would you like to do next?"


@function_tool
async def place_order(ctx: RunContext[Userdata], confirm: Annotated[bool, Field(description="Confirm order placement", default=True)] = True) -> str:
    userdata = ctx.userdata
    if not userdata.cart:
        return "Your cart is empty — nothing to place. Would you like to browse items?"
    line_items = []
    for li in userdata.cart:
        line_items.append({
            "product_id": li["product_id"],
            "quantity": li.get("quantity", 1),
            "attrs": li.get("attrs", {}),
        })
    order = create_order_object(line_items)
    userdata.orders.append(order)
    userdata.history.append({"time": datetime.utcnow().isoformat() + "Z", "action": "place_order", "order_id": order["id"]})
    userdata.cart = []
    return f"Order placed. Order ID {order['id']}. Total {order['total']} {order['currency']}. What would you like to do next?"


@function_tool
async def last_order(ctx: RunContext[Userdata]) -> str:
    ord = get_most_recent_order()
    if not ord:
        return "You have no past orders yet."
    lines = [f"Most recent order: {ord['id']} — {ord['created_at']}"]
    for it in ord['items']:
        lines.append(f"- {it['name']} x {it['quantity']}: {it['line_total']} {ord['currency']}")
    lines.append(f"Total: {ord['total']} {ord['currency']}")
    return "\n".join(lines)


@function_tool
async def get_world_state(ctx: RunContext[Userdata]) -> str:
    u = ctx.userdata
    return json.dumps({
        "player_name": u.player_name,
        "session_id": u.session_id,
        "started_at": u.started_at,
        "cart": u.cart,
        "orders": u.orders,
        "recent_history": u.history[-8:],
    }, indent=2)

# -------------------------
# The Agent (Tushar persona)
# -------------------------
class TusharAgent(Agent):
    def __init__(self):
        instructions = """
        You are 'Tushar', the friendly shopkeeper and voice assistant for Tushar Shop.
        Universe: A small neighbourhood Indian shop selling mugs, hoodies, t-shirts, shoes, phones, laptops, and raincoats.
        Tone: Warm, helpful, slightly jocular; keep sentences short for TTS clarity.
        Role: Help the customer browse the catalog, add items to cart, place orders, and review recent orders.

        Rules:
            - Use the provided tools (show_catalog, add_to_cart, show_cart, place_order, last_order, clear_cart, get_world_state).
            - Keep continuity using the per-session userdata. Mention cart contents if relevant.
            - Drive short voice-first turns suitable for spoken delivery.
            - When presenting options, include product id and price (e.g. 'mug-001 — 299 INR').
        """
        super().__init__(instructions=instructions, tools=[show_catalog, add_to_cart, show_cart, clear_cart, place_order, last_order, get_world_state])

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
    logger.info("🛍️ STARTING VOICE E-COMMERCE AGENT (Tushar Shop)")
    userdata = Userdata()
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-marcus", style="Conversational", text_pacing=True),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata.get("vad"),
        userdata=userdata,
    )
    await session.start(agent=TusharAgent(), room=ctx.room, room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    await ctx.connect()

# -------------------------
# DEV_SMOKE: quick local test (no LiveKit). Set DEV_SMOKE=1 in .env.local to run this on `python agent_tushar.py`.
# -------------------------
if __name__ == "__main__":
    if os.getenv("DEV_SMOKE"):
        import asyncio
        class DummyCtx:
            pass
        async def smoke():
            print("DEV_SMOKE: starting local simulation of Shop agent tools.\n")
            ctx = DummyCtx()
            ctx.userdata = Userdata()
            print("=== show_catalog (q='mug') ===")
            print(await show_catalog(ctx, q="mug"), "\n")
            print("=== add_to_cart (mug-001 x2) ===")
            print(await add_to_cart(ctx, "mug-001", quantity=2), "\n")
            print("=== show_cart ===")
            print(await show_cart(ctx), "\n")
            print("=== place_order ===")
            print(await place_order(ctx), "\n")
            print("=== last_order ===")
            print(await last_order(ctx), "\n")
            print("DEV_SMOKE done.")
        asyncio.run(smoke())
    else:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
