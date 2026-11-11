# Clinic chatbot

A chat assistant for a physiotherapy clinic's website. It answers the questions reception gets asked most, and hands anything else to a person.

**Live demo:** _coming soon_ · for a made-up clinic, Northbank Physio. Nothing you type is stored or sent.

## What it does

- **"Who's best for my injury?"** Pick back, knee, shoulder or sports, and it names the therapist who specialises in that, with a link to book with them.
- **Booking and contact questions** answered with the booking link, phone number and email.
- **Typed questions** too: "I sprained my ankle at football" goes to the sports therapist, "what's your number?" gets the contact details. It matches whole words, so "feedback" isn't mistaken for back pain.
- **Hand-off to a person** when it doesn't know: it asks for an email address, checks it and confirms it before passing it on.
- Typing dots and short pauses so replies feel natural, an "anything else?" step, and a clear end to the chat.

The replies are plain rules, not AI. Every answer is predictable, so the clinic decides exactly what patients are told, and there's nothing to go off-script on health advice.

## How it's built

- **Flask** (`app.py`): three small JSON endpoints, `/ask` for the buttons, `/ask-text` for typed questions and `/handoff` for the email.
- **The widget** (`templates/index.html`, `static/style.css`): plain JavaScript, no framework. Replies from the server can contain links; anything the patient types is always shown as plain text.
- **Tests** (`tests/test_app.py`): pytest, covering every button, typed questions, word matching, bad requests and email checks.

In the real clinic, `/handoff` emails reception. The demo sends nothing.

## Run it

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
flask --app app run      # http://localhost:5000
pytest                   # run the tests
```

---

Built by [Cian McCaul](https://cianmccaul.vercel.app).
