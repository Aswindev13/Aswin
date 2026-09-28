# LegalEase — AI-Powered Legal Document Generator

LegalEase is a local-first Streamlit + FastAPI application for drafting editable legal-document text with Google's Gemini API and exporting the result to TXT, DOCX, and PDF.

> **Important:** LegalEase generates draft legal content for informational purposes. It is not a law firm, does not provide legal advice, and does not guarantee that a document is valid or appropriate for a particular jurisdiction. Have a qualified lawyer review documents before signing or relying on them.

## Architecture

- **Frontend:** Streamlit (`frontend/app.py`)
- **Backend:** FastAPI (`backend/main.py`)
- **API route:** `POST /generate`
- **AI layer:** Google GenAI Python SDK (`google-genai`)
- **Document formatting:** `python-docx`, `fpdf2`, Pillow
- **Configuration:** `.env`
- **Tests:** pytest

The supplied project document specifies Gemini 1.5 Pro and the legacy `google-generativeai` package. This implementation keeps the requested Gemini architecture but uses Google's current `google-genai` SDK and a configurable current model (`gemini-2.5-flash` by default). Change `GEMINI_MODEL` in `.env` if your account has access to another supported model.

## Project structure

```text
LegalEase/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── schemas.py
│   └── services/
│       ├── __init__.py
│       ├── generator.py
│       └── document_formatter.py
├── frontend/
│   └── app.py
├── assets/
│   └── logo.png
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_formatter.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## VS Code setup

Requirements: Python 3.10+, VS Code, and a Gemini API key.

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configure Gemini

Copy `.env.example` to `.env` and add your key:

```text
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
BACKEND_URL=http://127.0.0.1:8000
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

Never commit `.env`.

## Run

Terminal 1:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
streamlit run frontend/app.py
```

Backend: `http://127.0.0.1:8000` and docs: `http://127.0.0.1:8000/docs`. Frontend: `http://localhost:8501`.

## Test

```bash
pytest -q
```

Tests mock Gemini where appropriate, so they do not require a live API call.

Example input:

- Document type: `Freelance Work Contract`
- Parties: `Jane Doe (Service Provider), TechNova Inc. (Client)`
- Terms: `Payment within 30 days of invoice; Provider delivers work by the agreed deadline; Confidentiality must be maintained; Either party may terminate with 15 days notice`
- Effective date: `September 23, 2026`

## Docker

```bash
docker compose up --build
```

Frontend is on port 8501 and backend on port 8000.

## Scope implemented from the supplied documentation

The application implements the documented Streamlit frontend, FastAPI `/generate` API, Gemini generation layer, editable preview, TXT/DOCX/PDF export, logo branding, terms table, footer, environment configuration, health check, validation, error handling, tests, and local deployment.
