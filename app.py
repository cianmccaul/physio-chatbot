"""
Clinic chatbot: a small Flask app behind a chat widget for a physiotherapy
clinic. It answers the questions reception gets most (which therapist suits my
injury, how do I book, how do I contact you) and hands anything else over to
a person.

This is a demo for a made-up clinic, Northbank Physio. The answers are plain
rules, not AI: every reply is predictable, so the clinic stays in control of
what patients are told.
"""

import re

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

CLINIC = {
    "name": "Northbank Physio",
    "phone": "01 555 0100",
    "email": "hello@northbank.example",
    "booking_url": "https://cian-clinic-demo.vercel.app",
}


def book_link(label="Book online"):
    return f'<a href="{CLINIC["booking_url"]}" target="_blank" rel="noopener">{label}</a>'


RESPONSES = {
    "book": f'You can book online here: {book_link()}, or call us on {CLINIC["phone"]}.',
    "contact": (
        f'Email us at <a href="mailto:{CLINIC["email"]}?subject=Enquiry%20from%20the%20website%20chat">{CLINIC["email"]}</a> '
        f'or call {CLINIC["phone"]}. We answer the phone 8am to 8pm on weekdays.'
    ),
}

# Which therapist suits which problem. The keywords also catch free-typed questions.
INJURIES = {
    "back": {
        "keywords": ["back", "spine", "sciatica", "neck"],
        "reply": f"For back and neck pain, Sarah Byrne (physiotherapist) is your best bet. {book_link('Book with Sarah')}",
    },
    "knee": {
        "keywords": ["knee", "acl", "meniscus", "hip"],
        "reply": f"For knee and hip problems, Mark Ryan (physiotherapist) specialises in this. {book_link('Book with Mark')}",
    },
    "shoulder": {
        "keywords": ["shoulder", "rotator", "elbow", "wrist"],
        "reply": f"For shoulder and arm issues, Tom Hayes (physiotherapist) covers this. {book_link('Book with Tom')}",
    },
    "sports": {
        "keywords": ["sport", "sports", "running", "hamstring", "ankle", "sprain", "football", "gym"],
        "reply": f"For sports injuries, Lucy Chen (physiotherapist and sports massage) is the one to see. {book_link('Book with Lucy')}",
    },
}

NOT_SURE = "Sorry, I'm not quite sure what you mean. Try one of the buttons, or I can pass you to a person."
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def reply_for(message):
    """The best reply to something a patient typed, or None if no rule matches."""
    found = words(message)
    for injury in INJURIES.values():
        if found & set(injury["keywords"]):
            return injury["reply"]
    if found & {"book", "booking", "appointment", "appointments", "available", "slot"}:
        return RESPONSES["book"]
    if found & {"contact", "phone", "call", "email", "number", "address"}:
        return RESPONSES["contact"]
    return None


@app.get("/")
def home():
    return render_template("index.html", clinic=CLINIC)


@app.post("/ask")
def ask():
    topic = (request.get_json(silent=True) or {}).get("topic", "")
    if topic == "injury":
        return jsonify({"type": "submenu", "options": list(INJURIES)})
    if topic in INJURIES:
        return jsonify({"type": "text", "reply": INJURIES[topic]["reply"]})
    if topic in RESPONSES:
        return jsonify({"type": "text", "reply": RESPONSES[topic]})
    return jsonify({"type": "text", "reply": NOT_SURE, "handoff": True})


@app.post("/ask-text")
def ask_text():
    message = str((request.get_json(silent=True) or {}).get("message", ""))[:500]
    reply = reply_for(message)
    if reply is None:
        return jsonify({"reply": NOT_SURE, "handoff": True})
    return jsonify({"reply": reply, "handoff": False})


@app.post("/handoff")
def handoff():
    """A patient asked for a person. In the real clinic this emails reception; the demo sends nothing."""
    email = str((request.get_json(silent=True) or {}).get("email", "")).strip()
    if not EMAIL_RE.match(email) or len(email) > 254:
        return jsonify({"ok": False, "error": "That doesn't look like an email address."}), 400
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
