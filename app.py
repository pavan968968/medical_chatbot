import os
import re
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "medical-chatbot-secret")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


GREETING_WORDS = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening"}

EMERGENCY_PATTERNS = [
    r"chest pain",
    r"trouble breathing",
    r"shortness of breath",
    r"can't breathe",
    r"cannot breathe",
    r"fainting",
    r"passed out",
    r"unconscious",
    r"seizure",
    r"one side (?:is )?weak",
    r"face droop",
    r"stroke",
    r"severe bleeding",
    r"vomiting blood",
    r"black stool",
    r"blue lips",
    r"severe allergic reaction",
    r"swelling of the tongue",
]

URGENT_PATTERNS = [
    r"high fever",
    r"stiff neck",
    r"severe headache",
    r"worst headache",
    r"severe abdominal pain",
    r"persistent vomiting",
    r"dehydration",
    r"confusion",
    r"worsening",
    r"pain (?:is )?8/10",
    r"pain (?:is )?9/10",
    r"pain (?:is )?10/10",
]

SYMPTOM_GROUPS: List[Tuple[str, List[str], str, List[str]]] = [
    (
        "breathing",
        ["cough", "wheezing", "breath", "chest tightness", "shortness of breath"],
        "I want to understand the breathing issue better.",
        ["How long has this been happening?", "Any fever or chest pain?", "Is breathing difficult right now?"],
    ),
    (
        "fever",
        ["fever", "temperature", "chills", "body ache", "flu"],
        "I can help narrow down the fever symptoms.",
        ["What is your temperature if you checked it?", "Any cough, sore throat, or body aches?", "How many days has it lasted?"],
    ),
    (
        "stomach",
        ["stomach", "belly", "abdominal", "nausea", "vomit", "diarrhea", "vomiting"],
        "Let’s look at the stomach symptoms.",
        ["Where exactly is the pain?", "Any vomiting or diarrhea?", "Can you keep fluids down?"],
    ),
    (
        "headache",
        ["headache", "migraine", "head pain", "dizzy", "dizziness"],
        "I need a bit more detail about the headache.",
        ["Did it start suddenly or gradually?", "Any vision changes or neck stiffness?", "How severe is the pain from 1 to 10?"],
    ),
    (
        "skin",
        ["rash", "itch", "swelling", "hives", "allergy"],
        "I can help with the skin or allergy symptoms.",
        ["Is there swelling of the lips or tongue?", "Any new medicine, food, or soap?", "Is the rash spreading quickly?"],
    ),
]


def normalize_text(message: str) -> str:
    return re.sub(r"\s+", " ", message.lower()).strip()


def contains_pattern(message: str, patterns: List[str]) -> bool:
    return any(re.search(pattern, message) for pattern in patterns)


def detect_emergency(message: str) -> bool:
    return contains_pattern(message, EMERGENCY_PATTERNS)


def detect_urgent(message: str) -> bool:
    return contains_pattern(message, URGENT_PATTERNS)


def identify_symptom_group(message: str):
    for name, keywords, intro, follow_ups in SYMPTOM_GROUPS:
        if any(keyword in message for keyword in keywords):
            return name, intro, follow_ups
    return None


def has_duration(message: str) -> bool:
    return bool(re.search(r"\b\d+\s*(?:day|days|week|weeks|hour|hours|month|months)\b", message))


def has_severity(message: str) -> bool:
    return bool(re.search(r"\b(?:mild|moderate|severe|worst|8/10|9/10|10/10)\b", message))


def starter_message() -> str:
    return (
        "I can help you think through symptoms, but I am not a doctor. "
        "Tell me what symptoms you have, when they started, and whether anything feels severe."
    )


def triage_response(message: str) -> Dict[str, object]:
    normalized = normalize_text(message)

    if not normalized:
        return {
            "reply": starter_message(),
            "severity": "info",
            "suggestions": ["I have a fever", "I have chest pain", "I have stomach pain"],
        }

    if normalized in GREETING_WORDS or any(normalized.startswith(word + " ") for word in GREETING_WORDS):
        return {
            "reply": starter_message(),
            "severity": "info",
            "suggestions": ["Fever and cough", "Headache", "Stomach pain"],
        }

    if detect_emergency(normalized):
        return {
            "reply": (
                "This could be an emergency. Please go to the nearest hospital now or call emergency services immediately. "
                "If you have chest pain, trouble breathing, fainting, severe bleeding, stroke-like symptoms, or blue lips, do not wait."
            ),
            "severity": "emergency",
            "suggestions": ["Tell me the main symptom", "How long has it been happening?"],
        }

    if detect_urgent(normalized):
        return {
            "reply": (
                "You should seek urgent medical care today. A hospital or urgent care clinic is the safer choice if this is getting worse, "
                "if the pain is severe, or if you have trouble keeping fluids down."
            ),
            "severity": "urgent",
            "suggestions": ["How long has it lasted?", "Do you have a fever?", "Is the pain severe?"],
        }

    group = identify_symptom_group(normalized)
    if group:
        _, intro, follow_ups = group
        details: List[str] = []
        if not has_duration(normalized):
            details.append("how long it has been going on")
        if not has_severity(normalized):
            details.append("how severe it feels")

        if details:
            question = " and ".join(details)
            reply = f"{intro} Please tell me {question}."
        else:
            reply = (
                f"{intro} Since you already mentioned timing and severity, tell me if anything is getting worse or if you have new symptoms."
            )

        return {
            "reply": reply,
            "severity": "medium",
            "suggestions": follow_ups,
        }

    if any(word in normalized for word in ["pain", "ache", "sore", "feeling", "sick"]):
        return {
            "reply": (
                "Tell me the exact symptom, where it is, when it started, and whether it is mild, moderate, or severe. "
                "If you have chest pain, trouble breathing, fainting, severe bleeding, or sudden weakness, go to a hospital now."
            ),
            "severity": "info",
            "suggestions": ["It is a fever", "It is chest pain", "It is stomach pain"],
        }

    return {
        "reply": (
            "I need a bit more detail. What symptoms are you having, when did they start, and do you have fever, chest pain, "
            "breathing trouble, vomiting, rash, or severe pain?"
        ),
        "severity": "info",
        "suggestions": ["Fever", "Cough", "Headache", "Stomach pain"],
    }


@app.route("/")
def index():
    return render_template("index.html", google_api_key_configured=bool(GOOGLE_API_KEY))


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", ""))
    response = triage_response(message)
    response["disclaimer"] = (
        "This chatbot is for general guidance only and does not replace professional medical advice. "
        "If symptoms feel severe or unusual, get medical help promptly."
    )
    response["google_api_key_configured"] = bool(GOOGLE_API_KEY)
    return jsonify(response)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)