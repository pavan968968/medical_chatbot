# medical_chatbot

A small Flask-based medical triage chatbot that asks about symptoms, follows up on timing and severity, and points users to hospital care when the answers sound urgent.

## What it includes

- Flask backend with a `/api/chat` JSON endpoint
- Rule-based symptom triage and urgency detection
- Frontend chat UI built with HTML, CSS, and a small amount of browser JavaScript
- Placeholder Google API key support through `.env`

## Run locally

1. Create a virtual environment.
2. Install the dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and place your Google key in `GOOGLE_API_KEY`.
4. Start the app with `python app.py`.

The app will be available at `http://localhost:5000`.

## Notes

- The Google API key is currently a placeholder for future Gemini integration.
- The current chatbot response logic is rule-based, so it works even without an external API key.