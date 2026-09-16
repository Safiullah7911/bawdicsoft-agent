"""
Tests the full tracker + known/unknown flow locally.
Server chalu hona chahiye: python app.py
"""
import requests
import json
import time

API = "http://localhost:8000"


# ==================== TEST 1: Unknown User Flow ====================
print("\n\n🔵 TEST 1: Unknown user (first visit)")

session = "test_unknown_" + str(int(time.time()))

# ─── Correct sequence (matches training data) ───
messages = [
    "I need an AI chatbot",      # project
    "Lead capture",              # purpose
    "React + Node",              # stack     ← YEH ADD HUA
    "test1@gmail.com",           # email
    "Bilal",                     # name
]

for msg in messages:
    r = requests.post(f"{API}/chat", json={
        "session_id": session, "message": msg, "page": "/contact"
    }).json()
    print(f"\n  👤 Visitor: {msg}")
    print(f"  🤖 Agent:   {r['reply']}")
    print(f"  🏷️  User type: {r.get('user_type', '?')}")
    if r.get("lead"):
        print(f"  📋 Lead: {r['lead']}")


# ==================== TEST 2: Same IP, New Session (Known) ====================
print("\n\n🟡 TEST 2: Same IP, new session (should be known via IP)")

session2 = "test_known_" + str(int(time.time()))
r = requests.post(f"{API}/chat", json={
    "session_id": session2, "message": "Hi", "page": "/"
}).json()
print(f"\n  👤 Visitor: Hi")
print(f"  🤖 Agent:   {r['reply']}")
print(f"  🏷️  User type: {r.get('user_type', '?')}")


# ==================== TEST 3: Track + Trigger ====================
print("\n\n🟢 TEST 3: Track + Trigger (unknown user)")

session3 = "test_trigger_" + str(int(time.time()))

# Simulate 6s dwell on /contact
r = requests.post(f"{API}/track", json={
    "session_id": session3, "page": "/contact", "dwell_ms": 6000
}).json()
print(f"\n  📡 Track response: {r}")

# Check trigger
r = requests.get(f"{API}/check-trigger", params={
    "session_id": session3, "page": "/contact"
}).json()
print(f"  🎯 Trigger response:")
print(f"      trigger:   {r['trigger']}")
print(f"      message:   {r.get('message', '')}")
print(f"      user_type: {r.get('user_type', '?')}")


# ==================== TEST 4: Check Duplicate ====================
print("\n\n🔴 TEST 4: Same session, trigger again (should be false)")

r = requests.get(f"{API}/check-trigger", params={
    "session_id": session3, "page": "/contact"
}).json()
print(f"\n  trigger: {r['trigger']}   (expected: False — popup already fired)")


# ==================== TEST 5: Admin View ====================
print("\n\n📊 TEST 5: Admin state")

r = requests.get(f"{API}/admin/sessions").json()
print(f"\n  Total known users: {r['total_known_users']}")
print(f"  Total anon IPs:    {r['total_anon_ips']}")
print(f"  Known users:       {list(r['known_users'].keys())}")
print(f"  IP index:          {r['ip_index']}")

print("\n\n✅ Sab tests complete!\n")