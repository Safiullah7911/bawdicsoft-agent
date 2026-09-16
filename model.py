import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_DIR = "./model_out"

print("Loading model...")
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
mdl = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR).eval()
print("Model loaded OK")

SYSTEM = (
    "You are BawdicSoft's AI sales assistant. Qualify visitors and capture "
    "their name, email, and what they want to build. Keep replies to 1-2 "
    "short sentences. Be direct, not salesy. Ask one question at a time. "
    "Never say you are an AI unless asked. If the visitor has sent 3 or more "
    "messages and hasn't given their email yet, ask for their email to send "
    "a detailed breakdown. If the user is a known/returning user, greet them "
    "personally and reference their past interests."
)

def build_input(user_type, user_name, user_interests, page, context):
    return (
        f"user_type: {user_type} | "
        f"user_name: {user_name or 'none'} | "
        f"user_interests: {user_interests or 'none'} | "
        f"page: {page} | "
        f"context: {context}"
    )

def reply(model_input):
    ids = tok(model_input, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = mdl.generate(**ids, max_new_tokens=48, num_beams=3, no_repeat_ngram_size=2)
    return tok.decode(out[0], skip_special_tokens=True)


print("\n--- Test 1: Unknown user, homepage ---")
print(reply(build_input("unknown", "", "", "/", "[conversation start]")))

print("\n--- Test 2: Unknown user, contact page, mid-conversation ---")
print(reply(build_input(
    "unknown", "", "", "/contact",
    "agent: Hey! Before you fill the form — want me to help? | visitor: I need an AI chatbot"
)))

print("\n--- Test 3: Known user, returning ---")
print(reply(build_input(
    "known", "Ahmed", "AI chatbot", "/",
    "[conversation start]"
)))

print("\n--- Test 4: Known user, new interest ---")
print(reply(build_input(
    "known", "Sara", "custom CRM", "/services",
    "[conversation start]"
)))