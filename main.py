# main.py — Conversational commerce (ants) — PUBLIC DEMO (Render-ready)
# Serves frontend at "/" and static files at "/static". Stripe (test) optional.
import os
import time
import uuid
from typing import Optional, Dict, Any, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ====== Stripe (optional) ======
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "").strip()
if STRIPE_API_KEY:
    import stripe
    stripe.api_key = STRIPE_API_KEY
else:
    stripe = None  # not configured

app = FastAPI(title="Conversational Commerce — Mini MVP")

# CORS relaxed per demo; en prod, limita origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Root serves the SPA
@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse(os.path.join("frontend", "index.html"))

# --- Mock catalog (3 products) ---
CATALOG = [
    {
        "id": "gel-xyz",
        "name": "Gel Antiformigues XYZ (tub 10 g)",
        "price_eur": 5.90,
        "pros": ["Alta efectivitat al niu", "Fàcil d'aplicar", "Actua 24–48 h"],
        "cons": ["Pot fer una mica de brutícia", "Cal reaplicar si plou molt"],
        "best_for": ["eliminar colònia", "exterior", "interior"],
        "kids_pets_note": "Mantenir fora de l'abast; evita zones on juguin nens i mascotes."
    },
    {
        "id": "trap-abc",
        "name": "Trampes Antiformigues ABC (pack 2)",
        "price_eur": 9.50,
        "pros": ["Més net i segur", "Sense contacte directe amb el gel", "Durada ~3 setmanes"],
        "cons": ["Una mica més car", "Triga 48–72 h en eliminar la colònia"],
        "best_for": ["amb nens", "amb mascotes", "exterior", "interior"],
        "kids_pets_note": "Disseny tancat; col·locar en zones discretes, no a l'abast directe."
    },
    {
        "id": "spray-123",
        "name": "Spray Contacte 123 (500 ml)",
        "price_eur": 6.75,
        "pros": ["Efecte immediat", "Ideal per a focus visibles"],
        "cons": ["No arriba al niu", "No elimina la colònia"],
        "best_for": ["acció ràpida", "interior"],
        "kids_pets_note": "Ventila l'estança i segueix les instruccions de seguretat."
    },
]

DELIVERY_SLOTS = [
    "Demà 8–10h", "Demà 10–12h", "Demà 16–18h",
    "Passat demà 8–10h", "Passat demà 10–12h"
]

# --- In-memory sessions (demo only) ---
SESSIONS: Dict[str, Dict[str, Any]] = {}

class ChatIn(BaseModel):
    message: str
    session_id: Optional[str] = None

def new_session() -> str:
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "created_at": time.time(),
        "context": {
            "topic": None,
            "need": None,
            "preference": None,        # 'ràpid' | 'colònia'
            "kids_pets": None,         # True/False/None
            "selected_product_id": None,
            "quantity": 1,
            "mode": None,              # "comparing"
            "compare_alt_id": None,
            "address": None,
            "delivery_slot": None,
        },
        "history": []
    }
    return sid

def system_reply(text: str, choices: Optional[List[str]] = None, done: bool = False, payload: Optional[Dict[str, Any]] = None):
    out = {"reply": text, "choices": choices or [], "done": done}
    if payload: out["payload"] = payload
    return out

def match_topic(message: str) -> Optional[str]:
    msg = message.lower()
    if "formig" in msg or "hormig" in msg or "ants" in msg:
        return "ants"
    return None

def pick_recommendation(preference: str, kids_pets: Optional[bool]):
    if preference == "ràpid":
        return next(p for p in CATALOG if p["id"] == "spray-123")
    if kids_pets is True:
        return next(p for p in CATALOG if p["id"] == "trap-abc")
    return next(p for p in CATALOG if p["id"] == "gel-xyz")

@app.post("/chat")
def chat(body: ChatIn):
    sid = body.session_id or new_session()
    state = SESSIONS.get(sid) or SESSIONS.setdefault(sid, {"context": {}, "history": []})
    ctx = state["context"]
    user_msg = body.message.strip()
    state["history"].append({"role": "user", "content": user_msg})

    # 0) Tema
    if ctx["topic"] is None:
        topic = match_topic(user_msg)
        if not topic:
            bot = system_reply("En què t'ajudo a comprar avui? (p. ex. 'vull eliminar una colònia de formigues al jardí')")
            bot["session_id"] = sid
            state["history"].append({"role": "assistant", "content": bot["reply"]})
            return JSONResponse(bot)
        ctx["topic"] = topic
        bot = system_reply(
            "Entesos. Vols <b>eliminar tota la colònia</b> o <b>una solució ràpida</b> per les que veus?",
            choices=["Eliminar colònia", "Solució ràpida"]
        )
        bot["session_id"] = sid
        state["history"].append({"role": "assistant", "content": bot["reply"]})
        return JSONResponse(bot)

    # 1) Preferència
    if ctx["preference"] is None:
        msg = user_msg.lower()
        if any(k in msg for k in ["ràpid", "rapid", "rápida", "rápido", "rapida"]):
            ctx["preference"] = "ràpid"
        elif any(k in msg for k in ["colònia", "colonia", "tota", "eliminar"]):
            ctx["preference"] = "colònia"
        else:
            bot = system_reply(
                "Disculpa, prefereixes <b>eliminar la colònia</b> o una <b>solució ràpida</b>?",
                choices=["Eliminar colònia", "Solució ràpida"]
            )
            bot["session_id"] = sid
            state["history"].append({"role": "assistant", "content": bot["reply"]})
            return JSONResponse(bot)

        bot = system_reply("Hi ha <b>nens o mascotes</b> a la zona on ho aplicaràs?", choices=["Sí", "No"])
        bot["session_id"] = sid
        state["history"].append({"role": "assistant", "content": bot["reply"]})
        return JSONResponse(bot)

    # 2) Nens/mascotes
    if ctx["kids_pets"] is None:
        msg = user_msg.lower()
        if any(k in msg for k in ["sí", "si", "yes"]):
            ctx["kids_pets"] = True
        elif "no" in msg:
            ctx["kids_pets"] = False
        else:
            bot = system_reply("Per seguretat, confirma: <b>Hi ha nens o mascotes a prop?</b>", choices=["Sí", "No"])
            bot["session_id"] = sid
            state["history"].append({"role": "assistant", "content": bot["reply"]})
            return JSONResponse(bot)

        product = pick_recommendation(ctx["preference"], ctx["kids_pets"])
        ctx["selected_product_id"] = product["id"]
        text = (
            f"Et recomano <b>{product['name']}</b> — {product['price_eur']:.2f} €.<br>"
            f"<b>Pros</b>: " + ", ".join(product["pros"]) + ".<br>"
            f"<b>Contres</b>: " + ", ".join(product["cons"]) + ".<br>"
            f"<b>Nota</b>: {product['kids_pets_note']}<br><br>"
            "Vols que et <b>compari</b> amb una alternativa o <b>compres aquest</b>?"
        )
        bot = system_reply(text, choices=["Comparar", "Comprar"])
        bot["session_id"] = sid
        bot["payload"] = {"product": product}
        state["history"].append({"role": "assistant", "content": bot["reply"]})
        return JSONResponse(bot)

    msg = user_msg.lower().strip()

    # 3) COMPARAR
    if "compar" in msg:
        current_id = ctx["selected_product_id"]
        if not current_id:
            bot = system_reply("Encara no tenim cap producte seleccionat per comparar. Vols que te'n recomani un primer?")
            bot["session_id"] = sid
            return JSONResponse(bot)

        alternatives = [p for p in CATALOG if p["id"] != current_id]
        if not alternatives:
            bot = system_reply("No tinc alternatives per comparar ara mateix.")
            bot["session_id"] = sid
            return JSONResponse(bot)

        cur = next(p for p in CATALOG if p["id"] == current_id)
        alt = alternatives[0]
        ctx["mode"] = "comparing"
        ctx["compare_alt_id"] = alt["id"]

        text = (
            "Comparativa ràpida:<br>"
            f"- <b>{cur['name']}</b> ({cur['price_eur']:.2f} €): " + ", ".join(cur["pros"]) + ".<br>"
            f"- <b>{alt['name']}</b> ({alt['price_eur']:.2f} €): " + ", ".join(alt["pros"]) + ".<br><br>"
            "Quin prefereixes? (respon amb <b>1</b> pel primer o <b>2</b> pel segon)"
        )
        bot = system_reply(text, choices=["1", "2"])
        bot["session_id"] = sid
        state["history"].append({"role": "assistant", "content": bot["reply"]})
        return JSONResponse(bot)

    if msg in ["1", "2"] and ctx.get("mode") == "comparing":
        current_id = ctx["selected_product_id"]
        alt_id = ctx.get("compare_alt_id")
        if not current_id or not alt_id:
            ctx["mode"] = None
            ctx["compare_alt_id"] = None
            bot = system_reply("Sembla que s'ha perdut el context. Vols <b>comparar</b> de nou o <b>comprar</b> directament?")
            bot["session_id"] = sid
            return JSONResponse(bot)

        chosen_id = current_id if msg == "1" else alt_id
        chosen = next(p for p in CATALOG if p["id"] == chosen_id)
        ctx["selected_product_id"] = chosen_id
        ctx["mode"] = None
        ctx["compare_alt_id"] = None

        text = f"Perfecte. Has seleccionat <b>{chosen['name']}</b> ({chosen['price_eur']:.2f} €).<br>Quantes unitats vols?"
        bot = system_reply(text)
        bot["session_id"] = sid
        state["history"].append({"role": "assistant", "content": bot["reply"]})
        return JSONResponse(bot)

    # 4) COMPRAR
    if any(k in msg for k in ["comprar", "compro", "vull comprar", "buy"]):
        if not ctx["selected_product_id"]:
            bot = system_reply("Primer necessito saber quin producte vols. Vols que te'n recomani un?")
            bot["session_id"] = sid
            return JSONResponse(bot)
        product = next(p for p in CATALOG if p["id"] == ctx["selected_product_id"])
        text = f"Perfecte. Has seleccionat <b>{product['name']}</b> ({product['price_eur']:.2f} €).<br>Quantes unitats vols?"
        bot = system_reply(text)
        bot["session_id"] = sid
        state["history"].append({"role": "assistant", "content": bot["reply"]})
        return JSONResponse(bot)

    # 5) QUANTITAT / ADREÇA / FRANJA (si no comparem)
    if ctx["selected_product_id"] and ctx.get("mode") != "comparing":
        # Últim missatge de l'assistent (per saber què ens havia demanat)
        last_assistant_text = ""
        for h in reversed(state["history"]):
            if h["role"] == "assistant":
                last_assistant_text = h["content"].lower()
                break

        digits = ''.join(ch for ch in msg if ch.isdigit())

        # --- PRIORITZA ADREÇA quan l'assistent l'acaba de demanar,
        #     encara que el text contingui números (p. ex. "C/ Indústria 12")
        if ctx["address"] is None and "adreça d'entrega" in last_assistant_text:
            ctx["address"] = user_msg
            slots_text = "<br>".join(f"{i+1}) {s}" for i, s in enumerate(DELIVERY_SLOTS))
            bot = system_reply(
                f"Perfecte. Adreça: <b>{ctx['address']}</b><br>"
                f"Tria <b>franja d’entrega</b>:<br>{slots_text}<br>"
                f"(Respon amb 1-{len(DELIVERY_SLOTS)})"
            )
            bot["session_id"] = sid
            state["history"].append({"role": "assistant", "content": bot["reply"]})
            return JSONResponse(bot)

        # --- QUANTITAT (només abans d'haver demanat l'adreça)
        if digits and ctx["address"] is None:
            qty = max(1, int(digits))
            ctx["quantity"] = qty
            product = next(p for p in CATALOG if p["id"] == ctx["selected_product_id"])
            total = qty * product["price_eur"]
            text = (
                f"Resum parcial:<br>"
                f"- Producte: <b>{product['name']}</b><br>"
                f"- Quantitat: <b>{qty}</b><br>"
                f"- Subtotal: <b>{total:.2f} €</b><br><br>"
                "Escriu <b>l'adreça d'entrega</b> (ex: 'C/ Indústria 12, Granollers')."
            )
            bot = system_reply(text)
            bot["session_id"] = sid
            state["history"].append({"role": "assistant", "content": bot["reply"]})
            return JSONResponse(bot)

        # 6) ADREÇA (entrada lliure, si encara no s'ha demanat explícitament)
        if ctx["address"] is None and len(user_msg) >= 6 and not digits:
            ctx["address"] = user_msg
            slots_text = "<br>".join(f"{i+1}) {s}" for i, s in enumerate(DELIVERY_SLOTS))
            bot = system_reply(
                f"Perfecte. Adreça: <b>{ctx['address']}</b><br>"
                f"Tria <b>franja d’entrega</b>:<br>{slots_text}<br>"
                f"(Respon amb 1-{len(DELIVERY_SLOTS)})"
            )
            bot["session_id"] = sid
            state["history"].append({"role": "assistant", "content": bot["reply"]})
            return JSONResponse(bot)

        # 7) FRANJA
        if ctx["address"] is not None and ctx["delivery_slot"] is None and digits:
            idx = int(digits) - 1
            if 0 <= idx < len(DELIVERY_SLOTS):
                ctx["delivery_slot"] = DELIVERY_SLOTS[idx]
                product = next(p for p in CATALOG if p["id"] == ctx["selected_product_id"])
                total = ctx["quantity"] * product["price_eur"]
                text = (
                    f"Resum:<br>"
                    f"- Producte: <b>{product['name']}</b><br>"
                    f"- Quantitat: <b>{ctx['quantity']}</b><br>"
                    f"- Adreça: <b>{ctx['address']}</b><br>"
                    f"- Franja: <b>{ctx['delivery_slot']}</b><br>"
                    f"- Total estimat: <b>{total:.2f} €</b><br><br>"
                    "Vols <b>pagar ara</b> o <b>canviar</b> alguna cosa?"
                )
                bot = system_reply(text, choices=["Pagar ara", "Canviar"])
                bot["session_id"] = sid
                bot["payload"] = {"total_eur": total}
                state["history"].append({"role": "assistant", "content": bot["reply"]})
                return JSONResponse(bot)
            else:
                bot = system_reply(f"Si us plau, tria un número entre <b>1</b> i <b>{len(DELIVERY_SLOTS)}</b>.")
                bot["session_id"] = sid
                return JSONResponse(bot)

        # 8) PAY (Stripe o Mock)
        if "pagar" in msg:
            if stripe:
                product = next(p for p in CATALOG if p["id"] == ctx["selected_product_id"])
                qty = ctx["quantity"]
                unit_amount_cents = int(round(product["price_eur"] * 100))
                metadata = {
                    "session_id": sid,
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": str(qty),
                    "address": ctx["address"] or "",
                    "delivery_slot": ctx["delivery_slot"] or "",
                }
                checkout = stripe.checkout.Session.create(
                    mode="payment",
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": "eur",
                            "product_data": {"name": product["name"]},
                            "unit_amount": unit_amount_cents,
                        },
                        "quantity": qty,
                    }],
                    success_url="https://example.com/success?sid={CHECKOUT_SESSION_ID}",
                    cancel_url="https://example.com/cancel",
                    metadata=metadata,
                )
                return JSONResponse({
                    "reply": "Genial! 👇 Fes clic per pagar de forma segura (Stripe test).",
                    "checkout_url": checkout.url,
                    "done": False,
                    "session_id": sid
                })
            else:
                # Fallback al mock si Stripe no està configurat
                return JSONResponse({
                    "reply": "Mode demo: pagament simulat.",
                    "checkout_url": "/static/mock-payment.html?sid=" + sid,
                    "done": False,
                    "session_id": sid
                })

        if "canviar" in msg:
            ctx.update({
                "preference": None, "kids_pets": None, "selected_product_id": None,
                "quantity": 1, "mode": None, "compare_alt_id": None,
                "address": None, "delivery_slot": None
            })
            bot = system_reply(
                "Cap problema! Tornem a començar. Vols <b>eliminar colònia</b> o <b>solució ràpida</b>?",
                choices=["Eliminar colònia", "Solució ràpida"]
            )
            bot["session_id"] = sid
            return JSONResponse(bot)

    # Fallback
    bot = system_reply("Perdona, no t'he entès. Pots repetir-ho o escriure <b>ajuda</b>?")
    bot["session_id"] = sid
    state["history"].append({"role": "assistant", "content": bot["reply"]})
    return JSONResponse(bot)
