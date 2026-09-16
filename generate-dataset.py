%%writefile generate_dataset.py
"""
Generates multi-column synthetic training data for BawdicSoft AI agent.
Columns: user_type, user_name, user_interests, page, context -> output

Run: python generate_dataset.py
Output: data/train.jsonl, data/val.jsonl
"""
import json
import random

random.seed(42)

SYSTEM = (
    "You are BawdicSoft's AI sales assistant. Qualify visitors and capture "
    "their name, email, and what they want to build. Keep replies to 1-2 "
    "short sentences. Be direct, not salesy. Ask one question at a time. "
    "Never say you are an AI unless asked. If the visitor has sent 3 or more "
    "messages and hasn't given their email yet, ask for their email to send "
    "a detailed breakdown. If the user is a known/returning user, greet them "
    "personally and reference their past interests."
)

PAGE_OPENERS = {
    "/": [
        "Hey! Building something with AI or blockchain? That's our space.",
        "Welcome! We build AI-powered systems and blockchain platforms that scale. What are you working on?",
        "Hey — looking for a dev team or exploring a specific solution?",
    ],
    "/services": [
        "Hey — looking for a dev team or exploring a specific solution?",
        "We cover web apps, blockchain/Web3, and AI solutions. What's your focus?",
        "Need help with strategy, design, or full development? Happy to point you the right way.",
    ],
    "/portfolio": [
        "See something that fits what you need? Happy to walk you through it.",
        "These are some of our best projects. Building something similar?",
        "Our team's delivered 250+ projects. What kind of product are you thinking about?",
    ],
    "/contact": [
        "Hey! Before you fill the form — want me to help figure out the right starting point?",
        "Looking to get in touch? I can help route you to the right person.",
    ],
    "/deep-trace": [
        "Checking out Deep-Trace? It detects AI-generated text, images, and video. Need it for your platform?",
        "Deep-Trace is our live AI detection product. Want to integrate something like this?",
    ],
    "/cybercity": [
        "CyberCity runs free security audits. Want to scan your site or build a similar security tool?",
        "CyberCity is our AI security audit agent. Building something in cybersecurity?",
    ],
    "/hashfor": [
        "Hashfor is our AI visibility & SEO audit platform. Building something in this space?",
        "Looking at Hashfor? We built it to boost rankings with data-driven insights.",
    ],
}

PROJECT_TYPES = [
    ("an AI chatbot for my platform", "customer support, lead capture, or something internal?"),
    ("a mobile app with AI features", "what should the AI feature actually do for the user?"),
    ("an AI-powered automation tool", "what process are you trying to automate?"),
    ("a recommendation engine", "what kind of content or products will it recommend?"),
    ("an AI detection tool like Deep-Trace", "what kind of content are you trying to detect?"),
    ("a blockchain wallet app", "consumer-facing or an internal tool?"),
    ("a DeFi protocol", "lending, swapping, or something else?"),
    ("an NFT marketplace", "for art, gaming, or utility NFTs?"),
    ("a crypto exchange", "spot trading or something more advanced?"),
    ("a smart contract audit", "what kind of contracts are we looking at?"),
    ("a custom CRM", "for sales, support, or both?"),
    ("an e-commerce platform", "B2B or B2C?"),
    ("a SaaS dashboard", "what's the core metric users will track?"),
    ("a Web3-integrated web app", "what wallet or chain are you targeting?"),
    ("a security audit tool like CyberCity", "internal use or a product for clients?"),
    ("an SEO/visibility platform like Hashfor", "what's your main SEO challenge right now?"),
]

PURPOSE_ANSWERS = [
    "Lead capture", "Customer support", "Internal tool", "Sales tracking",
    "Just exploring options", "Automating a manual process", "Building a client-facing product",
]

STACKS = [
    "React + Node", "Next.js + Postgres", "Not sure yet, still planning",
    "Python backend, React frontend", "WordPress currently, want to rebuild",
    "MERN stack", "Solidity + Hardhat",
]

NAMES = ["John", "Ayesha", "Bilal", "Sara", "Hamza", "Fatima", "Ali", "Zara", "Omar", "Mariam"]
DOMAINS = ["gmail.com", "company.com", "outlook.com", "startup.io", "protonmail.com"]

INTERESTS = [
    "AI chatbot", "blockchain wallet", "custom CRM", "SEO tool",
    "AI detection tool", "mobile app with AI", "NFT marketplace",
    "e-commerce platform",
]

def email_for(name):
    return f"{name.lower()}@{random.choice(DOMAINS)}"


# ============================================================
# UNKNOWN USER BUILDERS
# ============================================================

def build_happy_path(page):
    turns = []
    turns.append({"role": "agent", "text": random.choice(PAGE_OPENERS[page])})
    project, followup_q = random.choice(PROJECT_TYPES)
    turns.append({"role": "visitor", "text": f"I need {project}"})
    turns.append({"role": "agent", "text": f"Good timing. Is this for {followup_q}"})
    turns.append({"role": "visitor", "text": random.choice(PURPOSE_ANSWERS)})
    turns.append({"role": "agent", "text": "Got it. What's the platform built on?"})
    turns.append({"role": "visitor", "text": random.choice(STACKS)})
    turns.append({"role": "agent", "text": "Perfect stack. Drop your email and I'll have Bilal send you a quick breakdown — takes 2 mins."})
    name = random.choice(NAMES)
    turns.append({"role": "visitor", "text": email_for(name)})
    turns.append({"role": "agent", "text": "Done. Bilal will be in touch within the hour. What's your name?"})
    turns.append({"role": "visitor", "text": name})
    turns.append({"role": "agent", "text": f"Thanks {name}. Talk soon."})
    return turns


def build_pricing_objection(page):
    turns = [{"role": "agent", "text": random.choice(PAGE_OPENERS[page])}]
    project, _ = random.choice(PROJECT_TYPES)
    turns.append({"role": "visitor", "text": f"How much would {project} cost?"})
    turns.append({"role": "agent", "text": "Depends on scope — let me get Bilal to give you a real number."})
    turns.append({"role": "visitor", "text": "Fair enough, what do you need from me?"})
    turns.append({"role": "agent", "text": "Just your email — Bilal will follow up with real numbers."})
    name = random.choice(NAMES)
    turns.append({"role": "visitor", "text": email_for(name)})
    turns.append({"role": "agent", "text": "Got it. And your name?"})
    turns.append({"role": "visitor", "text": name})
    turns.append({"role": "agent", "text": f"Thanks {name}. Bilal will reach out shortly."})
    return turns


def build_not_ready(page):
    turns = [{"role": "agent", "text": random.choice(PAGE_OPENERS[page])}]
    turns.append({"role": "visitor", "text": "Just browsing for now, not ready to commit"})
    turns.append({"role": "agent", "text": "No worries. Want a free audit of your current setup instead?"})
    turns.append({"role": "visitor", "text": "Sure, why not"})
    turns.append({"role": "agent", "text": "Nice. Drop your email and I'll send the audit request over."})
    name = random.choice(NAMES)
    turns.append({"role": "visitor", "text": email_for(name)})
    turns.append({"role": "agent", "text": "And your name, so Bilal knows who to address?"})
    turns.append({"role": "visitor", "text": name})
    turns.append({"role": "agent", "text": f"Thanks {name}. You'll hear from us soon."})
    return turns


def build_name_first(page):
    turns = [{"role": "agent", "text": random.choice(PAGE_OPENERS[page])}]
    project, followup_q = random.choice(PROJECT_TYPES)
    turns.append({"role": "visitor", "text": f"Looking into {project}"})
    turns.append({"role": "agent", "text": f"Cool — is this for {followup_q}"})
    turns.append({"role": "visitor", "text": random.choice(PURPOSE_ANSWERS)})
    name = random.choice(NAMES)
    turns.append({"role": "agent", "text": "Got it. What's your name?"})
    turns.append({"role": "visitor", "text": name})
    turns.append({"role": "agent", "text": f"Thanks {name}. What's the best email for Bilal to reach you?"})
    turns.append({"role": "visitor", "text": email_for(name)})
    turns.append({"role": "agent", "text": f"Perfect, {name}. Bilal will be in touch shortly."})
    return turns


def build_high_engagement(page):
    turns = []
    turns.append({"role": "agent", "text": random.choice(PAGE_OPENERS[page])})
    project, followup_q = random.choice(PROJECT_TYPES)
    turns.append({"role": "visitor", "text": f"I need {project}"})
    turns.append({"role": "agent", "text": f"Good timing. Is this for {followup_q}"})
    turns.append({"role": "visitor", "text": random.choice(PURPOSE_ANSWERS)})
    turns.append({"role": "visitor", "text": "Also, what's your typical timeline?"})
    turns.append({"role": "agent", "text": "Usually 4-8 weeks for a first version. What's your target launch date?"})
    turns.append({"role": "visitor", "text": "We're aiming for Q3. Can you handle the full build?"})
    turns.append({"role": "agent", "text": "Sounds like you're serious about this — drop your email and Bilal will send a detailed breakdown."})
    name = random.choice(NAMES)
    turns.append({"role": "visitor", "text": email_for(name)})
    turns.append({"role": "agent", "text": "Done. Bilal will be in touch within the hour. What's your name?"})
    turns.append({"role": "visitor", "text": name})
    turns.append({"role": "agent", "text": f"Thanks {name}. Talk soon."})
    return turns


# ============================================================
# KNOWN USER BUILDERS (returning visitors)
# ============================================================

def build_returning_user(page):
    name = random.choice(NAMES)
    interest = random.choice(INTERESTS)
    turns = []
    turns.append({"role": "agent", "text": f"Welcome back {name}! Still interested in {interest}?"})
    turns.append({"role": "visitor", "text": "Yeah, but also exploring something new"})
    turns.append({"role": "agent", "text": "Sure, what else are you looking at?"})
    project, _ = random.choice(PROJECT_TYPES)
    turns.append({"role": "visitor", "text": f"Maybe {project}"})
    turns.append({"role": "agent", "text": f"Got it. Want me to compare {interest} with {project} for you?"})
    turns.append({"role": "visitor", "text": "Yes please"})
    turns.append({"role": "agent", "text": f"Done, {name}. Bilal will send the comparison over."})
    return turns


def build_returning_ask_progress(page):
    name = random.choice(NAMES)
    interest = random.choice(INTERESTS)
    turns = []
    turns.append({"role": "agent", "text": f"Hey {name}, how's the {interest} project going?"})
    turns.append({"role": "visitor", "text": "We're still figuring it out"})
    turns.append({"role": "agent", "text": "Want me to send a fresh breakdown to help you decide?"})
    turns.append({"role": "visitor", "text": "Sure"})
    turns.append({"role": "agent", "text": f"Perfect, {name}. Bilal will reach out with updates."})
    return turns


def build_returning_new_interest(page):
    name = random.choice(NAMES)
    old_interest = random.choice(INTERESTS)
    new_interest = random.choice([i for i in INTERESTS if i != old_interest])
    turns = []
    turns.append({"role": "agent", "text": f"Welcome back {name}! You were looking at {old_interest}."})
    turns.append({"role": "visitor", "text": f"Actually now I'm interested in {new_interest}"})
    turns.append({"role": "agent", "text": f"Nice pivot. Want me to loop in Bilal for {new_interest}?"})
    turns.append({"role": "visitor", "text": "Yes"})
    turns.append({"role": "agent", "text": f"Got it, {name}. Bilal will follow up today."})
    return turns


def build_returning_quick_question(page):
    name = random.choice(NAMES)
    interest = random.choice(INTERESTS)
    turns = []
    turns.append({"role": "agent", "text": f"Hey {name}! What can I help with today?"})
    turns.append({"role": "visitor", "text": "Quick question about pricing"})
    turns.append({"role": "agent", "text": f"For {interest}? Let me get Bilal to send you exact numbers."})
    turns.append({"role": "visitor", "text": "Okay"})
    turns.append({"role": "agent", "text": f"Done, {name}. You'll hear within the hour."})
    return turns


# ============================================================
# MULTI-COLUMN CONVERTER
# ============================================================

def turns_to_examples(turns, user_type="unknown", user_info=None, page="/"):
    """Conversation ko multi-column examples mein todo."""
    examples = []
    history = []

    user_name = user_info.get("name", "") if user_info else ""
    user_interests = user_info.get("interests", "") if user_info else ""

    for turn in turns:
        if turn["role"] == "agent":
            context = " | ".join(history) if history else "[conversation start]"
            examples.append({
                "user_type": user_type,
                "user_name": user_name,
                "user_interests": user_interests,
                "page": page,
                "context": context,
                "output": turn["text"],
            })
        history.append(f"{turn['role']}: {turn['text']}")
    return examples


# ============================================================
# MAIN
# ============================================================

UNKNOWN_BUILDERS = [
    build_happy_path,
    build_pricing_objection,
    build_not_ready,
    build_name_first,
    build_high_engagement,
]

KNOWN_BUILDERS = [
    build_returning_user,
    build_returning_ask_progress,
    build_returning_new_interest,
    build_returning_quick_question,
]


def main():
    import os
    os.makedirs("data", exist_ok=True)

    all_examples = []
    pages = list(PAGE_OPENERS.keys())

    # 70% unknown users
    for page in pages:
        for builder in UNKNOWN_BUILDERS:
            for _ in range(15):
                convo = builder(page)
                all_examples.extend(
                    turns_to_examples(convo, user_type="unknown", page=page)
                )

    # 30% known users
    for page in pages:
        for builder in KNOWN_BUILDERS:
            for _ in range(10):
                convo = builder(page)
                name = random.choice(NAMES)
                interest = random.choice(INTERESTS)
                all_examples.extend(
                    turns_to_examples(
                        convo,
                        user_type="known",
                        user_info={"name": name, "interests": interest},
                        page=page,
                    )
                )

    random.shuffle(all_examples)
    split = int(len(all_examples) * 0.9)
    train, val = all_examples[:split], all_examples[split:]

    with open("data/train.jsonl", "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")
    with open("data/val.jsonl", "w") as f:
        for ex in val:
            f.write(json.dumps(ex) + "\n")

    known = sum(1 for ex in all_examples if ex["user_type"] == "known")
    unknown = len(all_examples) - known
    print(f"Generated {len(all_examples)} examples")
    print(f"  Known: {known} | Unknown: {unknown}")
    print(f"Train: {len(train)} | Val: {len(val)}")


if __name__ == "__main__":
    main()