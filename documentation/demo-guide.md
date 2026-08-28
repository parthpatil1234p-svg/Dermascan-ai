# College Demonstration Guide

## Prerequisites

- Python 3.12, Node.js 22, npm, and MongoDB, or Docker Compose.
- A populated `backend/.env` and `frontend/.env`.
- Fictional catalogue data from `python -m app.scripts.seed_demo_data`.
- Trained model artifacts, or explicit `AI_DEMO_MODE=true` for a labelled mock
  demonstration.

## Startup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m app.scripts.seed_demo_data
uvicorn app.main:app --reload

cd ..\frontend
npm ci
npm run dev
```

Unix activation is `source .venv/bin/activate`. Create the demonstration account
through the registration UI; no shared account or password is committed.

## Demonstration Image

Use [synthetic-demo-portrait.png](demo-assets/synthetic-demo-portrait.png). It
was generated for this project, depicts no known person, is not training or
evaluation data, and must not be used to claim model performance. A presenter
may instead use an image they have the right and consent to use.

## Successful Walkthrough

1. Show health and readiness. Explain model or demonstration mode honestly.
2. Register and complete the profile, including one avoidance and a budget.
3. Upload the synthetic portrait and accept image-processing consent.
4. Review quality, face detection, preprocessing, uncertainty, and visible labels.
5. Show a hard exclusion never entering recommendation or routine output.
6. Generate a routine and versioned final report; export privacy-reduced PDF.
7. Submit optional feedback, view history, then withdraw it.
8. Show previous reports, logout, and confirm protected routes return to login.

## Failure Cases

- Upload a `.txt` renamed to `.jpg` to show actual decoding rejection.
- Use a very small or uniformly blurred synthetic image for quality failure.
- Use a landscape image without a face for face-detection failure.
- Enter fragrance in known allergies and show fragrance products excluded.
- Use strict budget/availability constraints and show a no-result state without
  silently relaxing restrictions.
- Use a second account to request the first account's report ID and show safe
  not-found behavior.

## Safety Points To Explain

Image checks are technical heuristics. Skin output is AI-assisted and uncertain,
sensitivity/allergies are self-reported, products are fictional demonstration
catalogue entries, scores are relevance only, and no clinical accuracy is claimed.

## Troubleshooting

- `503 /readiness`: start MongoDB, seed products, install model artifacts, or
  explicitly enable demonstration mode.
- CORS failure: match `FRONTEND_ORIGIN` exactly to the browser origin.
- Broken Python venv: delete only `.venv`, recreate it with an installed Python
  3.12 interpreter, and reinstall requirements.
- Upload failure: confirm private storage roots are writable and the image is
  JPG/PNG, below 5 MB, and within configured dimensions.

