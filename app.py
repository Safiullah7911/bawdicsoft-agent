"""
BawdicSoft AI Sales Agent — IP + Email dual tracking + CORS enabled.
- Known user: email diya hai
- Familiar user: email nahi diya, lekin IP 2+ baar aayi
- Unknown user: pehli baar aa raha hai
"""
import os, re, json, time
from typing import Dict, List
from collections import defaultdict

import torch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ============ CONFIG ============
MODEL_DIR = os.environ.get("MODEL_DIR", "./model_out")
USERS_FILE = os.environ.get("USERS_FILE", "./users.json")
IP_INDEX_FILE = os.environ.get("IP_INDEX_FILE", "./ip_index.json")
ANON_FILE = os.environ.get("ANON_FILE", "./anon_visitors.json")
DWELL_TRIGGER_SECONDS = 5
FAMILIAR_VISIT_THRESHOLD = 2

SYSTEM = (
    "You are BawdicSoft's AI sales assistant. Qualify visitors and capture "
    "their name, email, and what they want to build. Keep replies to 1-2 "
    "short sentences. Be direct, not salesy. Ask one question at a time. "
    "Never say you are an AI unless asked. If the visitor has sent 3 or more "
    "messages and hasn't given their email yet, ask for their email to send "
    "a detailed breakdown. If the user is a known/returning user, greet them "
    "personally and reference their past interests."
)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

app = FastAPI(title="BawdicSoft AI Sales Agent")

# ============ CORS — Zaroori! ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bawdicsoft.com",
        "https://www.bawdicsoft.com",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)
model.eval()
print("Model loaded OK")

# ============ PERSISTENT STORAGE HELPERS ============
def load_json(path: str) -> Dict:
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SAVE] {path} failed: {e}")

# ============ PERSISTENT STORES ============
USERS: Dict = load_json(USERS_FILE)
IP_INDEX: Dict = load_json(IP_INDEX_FILE)
ANON_VISITORS: Dict = load_json(ANON_FILE)

# ============ IN-MEMORY STORES ============
SESSIONS: Dict[str, List[str]] = {}
LEADS: Dict[str, Dict] = {}
PAGE_DWELL: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
TRIGGERED: Dict[str, bool] = {}

# ============ PAGE MESSAGES ============
PAGE_MESSAGES = {
    "/": "Hey! Building something with AI or blockchain? I can help you figure out where to start.",
    "/services": "Looking at our services? Tell me what you're trying to build and I'll point you the right way.",
    "/portfolio": "See something that fits? Happy to walk you through similar projects we've done.",
    "/contact": "Want to get in touch? I can help you figure out the right starting point before you fill the form.",
    "/contact-us": "Want to get in touch? I can help you figure out the right starting point before you fill the form.",
    "/deep-trace": "Checking out Deep-Trace? Want to integrate AI detection into your platform?",
    "/cybercity": "CyberCity runs free security audits. Need help setting up something similar?",
    "/hashfor": "Looking at Hashfor? We built it to boost SEO rankings with data-driven insights.",
}

# ============ HELPERS ============
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def clean_interest(raw: str) -> str:
    if not raw:
        return ""
    kws = ["AI chatbot", "chatbot", "blockchain", "CRM", "SEO", "wallet",
           "NFT", "mobile app", "DeFi", "dApp", "e-commerce"]
    for kw in kws:
        if kw.lower() in raw.lower():
            return kw
    return raw.strip()[:40]


def detect_user(session_id: str, ip: str) -> Dict:
    lead = LEADS.get(session_id, {})
    email = lead.get("email")

    if not email and ip in IP_INDEX:
        email = IP_INDEX[ip]
        LEADS.setdefault(session_id, {})["email"] = email

    if email and email in USERS:
        u = USERS[email]
        return {
            "type": "known",
            "name": u.get("name", ""),
            "interests": clean_interest(u.get("interests", "")),
            "email": email,
        }

    anon = ANON_VISITORS.get(ip, {})
    if anon.get("visits", 0) >= FAMILIAR_VISIT_THRESHOLD:
        return {
            "type": "familiar",
            "name": "",
            "interests": anon.get("top_page", "").strip("/").replace("-", " "),
            "email": "",
        }

    return {"type": "unknown", "name": "", "interests": "", "email": ""}


def build_model_input(session_id: str, page: str, context_str: str, ip: str) -> str:
    user = detect_user(session_id, ip)
    model_user_type = "known" if user["type"] in ("known", "familiar") else "unknown"
    return (
        f"user_type: {model_user_type} | "
        f"user_name: {user['name'] or 'none'} | "
        f"user_interests: {user['interests'] or 'none'} | "
        f"page: {page} | "
        f"context: {context_str}"
    )


def generate_reply(model_input: str) -> str:
    ids = tokenizer(model_input, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=20, num_beams=1, no_repeat_ngram_size=2)
    return tokenizer.decode(out[0], skip_special_tokens=True).strip()


def maybe_capture_lead(session_id, visitor_text, history, page, ip):
    """Lead capture — email + name detection."""
    lead = LEADS.setdefault(session_id, {})

    # Email detection
    match = EMAIL_RE.search(visitor_text)
    if match:
        lead["email"] = match.group(0)

    last_agent = next((t for t in reversed(history) if t.startswith("agent:")), "")
    is_email = bool(EMAIL_RE.search(visitor_text))
    words = visitor_text.strip().split()

    # Name detection (improved)
    should_capture_name = False
    if not is_email and len(words) <= 2 and not any(c.isdigit() for c in visitor_text):
        if "name" in last_agent.lower():
            should_capture_name = True
        elif lead.get("email") and not lead.get("name"):
            should_capture_name = True

    if should_capture_name:
        lead["name"] = visitor_text.strip()

    # Project detection
    keywords = ["chatbot", "blockchain", "crm", "seo", "wallet", "nft",
                "mobile", "defi", "dapp", "ecommerce", "e-commerce"]
    if any(k in visitor_text.lower() for k in keywords) and not lead.get("project"):
        lead["project"] = visitor_text.strip()

    if lead.get("email") and lead.get("name"):
        fire_lead_webhooks(session_id, lead, ip)


def fire_lead_webhooks(session_id, lead, ip):
    print(f"[LEAD CAPTURED] session={session_id} ip={ip} lead={lead}")

    email = lead.get("email")
    if email:
        USERS[email] = {
            "name": lead.get("name", ""),
            "interests": clean_interest(lead.get("project", "")),
            "ip": ip,
            "last_seen": time.time(),
            "session_id": session_id,
        }
        IP_INDEX[ip] = email

        save_json(USERS_FILE, USERS)
        save_json(IP_INDEX_FILE, IP_INDEX)
        print(f"[USER SAVED] {email} | ip={ip}")


def pick_proactive_message(page: str, session_id: str, ip: str) -> str:
    user = detect_user(session_id, ip)

    if user["type"] == "known":
        name = user["name"]
        interests = user["interests"]
        if name and interests:
            return f"Welcome back {name}! Still working on {interests}?"
        elif name:
            return f"Welcome back {name}! What can I help with today?"
        else:
            return "Welcome back! What can I help with today?"

    if user["type"] == "familiar":
        return f"Welcome back! Still checking our {page.strip('/').replace('-', ' ')} page?"

    if page in PAGE_MESSAGES:
        return PAGE_MESSAGES[page]
    for known_page, msg in PAGE_MESSAGES.items():
        if page.startswith(known_page) and known_page != "/":
            return msg
    return "Hey! Anything I can help you with while you're browsing?"


# ============ MODELS ============
class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str = ""
    page: str = "/"

class ChatResponse(BaseModel):
    reply: str
    lead: Dict
    user_type: str = "unknown"

class TrackRequest(BaseModel):
    session_id: str
    page: str
    dwell_ms: int
    referrer: str = ""

class TriggerResponse(BaseModel):
    trigger: bool
    message: str = ""
    user_type: str = "unknown"


# ============ ENDPOINTS ============
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    ip = get_client_ip(request)
    history = SESSIONS.setdefault(req.session_id, [])
    msg = req.message.strip()
    is_first_message = len(history) == 0

    if msg:
        history.append(f"visitor: {msg}")
        maybe_capture_lead(req.session_id, msg, history, req.page, ip)

    user = detect_user(req.session_id, ip)

    if is_first_message and user["type"] == "known":
        name = user["name"]
        interests = user["interests"]
        if name and interests:
            reply = f"Welcome back {name}! Still interested in {interests}?"
        elif name:
            reply = f"Welcome back {name}! What can I help with today?"
        else:
            reply = "Welcome back! What can I help with today?"
    elif is_first_message and user["type"] == "familiar":
        reply = f"Welcome back! Still looking at {user['interests'] or 'our services'}?"
    else:
        context_str = " | ".join(history) if history else "[conversation start]"
        model_input = build_model_input(req.session_id, req.page, context_str, ip)
        reply = generate_reply(model_input)

    history.append(f"agent: {reply}")

    return ChatResponse(
        reply=reply,
        lead=LEADS.get(req.session_id, {}),
        user_type=user["type"],
    )


@app.post("/track")
async def track(req: TrackRequest, request: Request):
    ip = get_client_ip(request)
    PAGE_DWELL[req.session_id][req.page] += req.dwell_ms

    now = time.time()
    if ip not in ANON_VISITORS:
        ANON_VISITORS[ip] = {
            "first_seen": now,
            "last_seen": now,
            "visits": 1,
            "top_page": req.page,
            "session_ids": [req.session_id],
        }
    else:
        av = ANON_VISITORS[ip]
        av["last_seen"] = now
        if req.session_id not in av["session_ids"]:
            av["visits"] += 1
            av["session_ids"].append(req.session_id)
            av["session_ids"] = av["session_ids"][-10:]

    pages = PAGE_DWELL[req.session_id]
    if pages:
        ANON_VISITORS[ip]["top_page"] = max(pages, key=pages.get)

    save_json(ANON_FILE, ANON_VISITORS)

    print(f"[TRACK] ip={ip} page={req.page} dwell={req.dwell_ms}ms "
          f"visits={ANON_VISITORS[ip]['visits']}")

    return {
        "status": "ok",
        "ip": ip,
        "visits": ANON_VISITORS[ip]["visits"],
    }


@app.get("/check-trigger", response_model=TriggerResponse)
async def check_trigger(session_id: str, page: str, request: Request):
    ip = get_client_ip(request)

    if TRIGGERED.get(session_id):
        return TriggerResponse(trigger=False, user_type=detect_user(session_id, ip)["type"])

    page_dwell = PAGE_DWELL.get(session_id, {})
    if not page_dwell:
        return TriggerResponse(trigger=False, user_type=detect_user(session_id, ip)["type"])

    current_dwell_sec = page_dwell.get(page, 0) / 1000.0
    if current_dwell_sec < DWELL_TRIGGER_SECONDS:
        return TriggerResponse(trigger=False, user_type=detect_user(session_id, ip)["type"])

    top_page = max(page_dwell, key=page_dwell.get)
    if top_page != page:
        return TriggerResponse(trigger=False, user_type=detect_user(session_id, ip)["type"])

    TRIGGERED[session_id] = True
    message = pick_proactive_message(page, session_id, ip)
    user = detect_user(session_id, ip)

    print(f"[TRIGGER] session={session_id} ip={ip} page={page} "
          f"dwell={current_dwell_sec:.1f}s user_type={user['type']}")

    return TriggerResponse(trigger=True, message=message, user_type=user["type"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin/sessions")
def admin_sessions():
    return {
        "total_sessions": len(PAGE_DWELL),
        "total_known_users": len(USERS),
        "total_anon_ips": len(ANON_VISITORS),
        "known_users": USERS,
        "ip_index": IP_INDEX,
        "anon_visitors": ANON_VISITORS,
        "sessions": {
            sid: {
                "pages": dict(pages),
                "top_page": max(pages, key=pages.get) if pages else None,
                "triggered": TRIGGERED.get(sid, False),
                "lead": LEADS.get(sid, {}),
            }
            for sid, pages in PAGE_DWELL.items()
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)