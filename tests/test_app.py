import pytest

from app import app, reply_for


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_home_page_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Northbank Physio" in res.data


def test_injury_button_offers_the_areas(client):
    data = client.post("/ask", json={"topic": "injury"}).get_json()
    assert data == {"type": "submenu", "options": ["back", "knee", "shoulder", "sports"]}


@pytest.mark.parametrize("topic,therapist", [("back", "Sarah"), ("knee", "Mark"), ("shoulder", "Tom"), ("sports", "Lucy")])
def test_each_area_names_its_therapist(client, topic, therapist):
    data = client.post("/ask", json={"topic": topic}).get_json()
    assert therapist in data["reply"]


def test_unknown_topic_offers_a_person(client):
    data = client.post("/ask", json={"topic": "parking"}).get_json()
    assert data["handoff"] is True


@pytest.mark.parametrize(
    "message,expected",
    [
        ("My lower back has been killing me", "Sarah"),
        ("I sprained my ankle at football", "Lucy"),
        ("Can I get an appointment on Friday?", "book online"),
        ("What's your phone number?", "01 555 0100"),
    ],
)
def test_typed_questions(message, expected):
    assert expected.lower() in reply_for(message).lower()


def test_words_inside_other_words_dont_match():
    # "feedback" contains "back", but it isn't about back pain
    assert reply_for("I'd like to leave some feedback") is None


def test_typed_question_with_no_match_offers_a_person(client):
    data = client.post("/ask-text", json={"message": "Do you sell gift cards?"}).get_json()
    assert data["handoff"] is True


def test_bad_requests_are_handled(client):
    assert client.post("/ask-text", data="not json").status_code == 200
    assert client.post("/ask", json={}).get_json()["handoff"] is True


@pytest.mark.parametrize("email,ok", [("pat@example.com", True), ("not-an-email", False), ("", False)])
def test_handoff_checks_the_email(client, email, ok):
    res = client.post("/handoff", json={"email": email})
    assert res.get_json()["ok"] is ok
    assert res.status_code == (200 if ok else 400)


# ----- Urgent symptoms -----

URGENT_MESSAGES = [
    "I have chest pain when I run",
    "My chest is tight, tightness in my chest since this morning",
    "I can't breathe properly",
    "I can’t breathe properly",  # curly apostrophe, as phones type it
    "I've been short of breath all day",
    "my leg has gone numb",
    "Numbness down my arm",
    "I can't feel my feet",
    "Back pain and I can't control my bladder",
    "my dad's face is drooping and his speech is slurred",
    "She collapsed at training",
]


@pytest.mark.parametrize("message", URGENT_MESSAGES)
def test_urgent_symptoms_get_the_safety_message(client, message):
    data = client.post("/ask-text", json={"message": message}).get_json()
    assert data["urgent"] is True
    assert data["handoff"] is False
    assert "112" in data["reply"] and "999" in data["reply"] and "GP" in data["reply"]
    # never a normal answer: no therapist, no booking link
    assert "Book" not in data["reply"]
    assert "cian-clinic-demo" not in data["reply"]


def test_urgent_beats_an_injury_match():
    # "football" alone would go to the sports therapist
    reply = reply_for("Chest pain after football last night")
    assert "112" in reply
    assert "Lucy" not in reply


def test_urgent_errs_on_the_side_of_caution():
    # a plain word list can't tell "no chest pain" from "chest pain", so it plays safe
    assert "112" in reply_for("No chest pain, just a sore knee")


@pytest.mark.parametrize(
    "message",
    ["My lower back is sore", "Do you do breathing exercises?", "I pulled a muscle doing chest press", "Can I book a sports massage?"],
)
def test_everyday_questions_are_not_flagged(client, message):
    data = client.post("/ask-text", json={"message": message}).get_json()
    assert "urgent" not in data
    assert "112" not in data["reply"]


def test_urgent_needs_whole_words():
    # "numbers" contains "numb"
    assert "112" not in (reply_for("What are your opening numbers?") or "")
