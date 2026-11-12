"""
Clinic chatbot: a small Flask app behind a chat widget for a physiotherapy
clinic. It answers the questions reception gets most (which therapist suits my
injury, how do I book, how do I contact you) and hands anything else over to
a person.

This is a demo for a made-up clinic, Northbank Physio. The answers are plain
rules, not AI: every reply is predictable, so the clinic stays in control of
what patients are told. Messages that mention urgent symptoms (chest pain,
breathing difficulty, numbness and so on) get a "call 112/999 or your GP"
message instead of a normal answer.
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

# ----- Urgent symptoms -----
# Some symptoms need a doctor or an ambulance, not a physio appointment. If a
# typed message mentions one, the bot gives the safety message below and nothing
# else: no therapist, no booking link. This is a plain list of words and phrases,
# not a diagnosis. It errs on the side of caution ("no chest pain" still gets the
# safety message) and it can't catch every way of describing an emergency.
URGENT_PHRASES = [
    # chest
    "chest pain", "chest pains", "pain in my chest", "chest tightness", "tight chest", "tightness in my chest",
    "heart attack",
    # breathing
    "cant breathe", "cannot breathe", "can not breathe", "difficulty breathing", "trouble breathing",
    "struggling to breathe", "hard to breathe", "short of breath", "shortness of breath", "breathless",
    # numbness and weakness
    "numb", "numbness", "cant feel my", "sudden weakness", "lost the use", "cant move my", "paralysed", "paralyzed",
    # stroke signs
    "drooping", "droopy face", "slurred", "slurring", "stroke",
    # bladder and bowel changes with back pain (cauda equina)
    "bladder", "bowel", "incontinence", "incontinent", "wet myself", "soiled myself",
    # other emergencies
    "fainted", "passed out", "collapsed", "unconscious", "seizure", "coughing up blood", "worst headache",
]

URGENT_REPLY = (
    "Some of what you've described can be a sign of something serious, so please don't wait for a "
    "physio appointment. If it's severe or came on suddenly, call "
    '<a href="tel:112">112</a> or <a href="tel:999">999</a> now. Otherwise, contact your GP '
    "(or an out-of-hours GP service) today."
)

NOT_SURE = "Sorry, I'm not quite sure what you mean. Try one of the buttons, or I can pass you to a person."
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def normalise(text):
    """Lowercase words separated by single spaces, with apostrophes dropped (so "can't" becomes "cant")."""
    text = re.sub(r"['\u2019]", "", text.lower())
    return " " + " ".join(re.findall(r"[a-z]+", text)) + " "


def is_urgent(message):
    """True if the message mentions a symptom that needs a doctor, not a physio. Whole words only."""
    text = normalise(message)
    return any(f" {phrase} " in text for phrase in URGENT_PHRASES)


def reply_for(message):
    """The best reply to something a patient typed, or None if no rule matches.

    Urgent symptoms are checked first, so "chest pain after football" never gets
    the sports therapist.
    """
    if is_urgent(message):
        return URGENT_REPLY
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
    if is_urgent(message):
        return jsonify({"reply": URGENT_REPLY, "handoff": False, "urgent": True})
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
