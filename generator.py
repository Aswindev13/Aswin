from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None

load_dotenv()


SYSTEM_INSTRUCTION = '''
You are the drafting engine for LegalEase, an AI-assisted legal-document drafting application.

Draft a clear, professional legal document based only on the supplied document type, parties, terms, and effective date.

Rules:
1. Do not invent names, addresses, amounts, dates, governing-law jurisdictions, registration numbers, or other material facts not supplied by the user.
2. If important information is missing, use a neutral placeholder such as [INSERT GOVERNING LAW] rather than silently inventing it.
3. Preserve all material user-provided terms.
4. Produce editable plain text, not Markdown tables and not HTML.
5. Use a professional structure with a title, numbered sections, and signature blocks where appropriate.
6. Do not claim the document is legally valid, legally sound, compliant, or suitable for a specific jurisdiction unless the user supplied that basis.
7. Include a short IMPORTANT REVIEW NOTICE at the end stating that the draft should be reviewed by a qualified lawyer before signing or relying on it.
8. Do not provide legal advice to the user; produce the requested draft.
9. Do not use fake citations or cite laws you have not been given.
'''


@dataclass
class GeminiDocumentGenerator:
    api_key: str | None = None
    model: str | None = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        self.model = self.model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured. Add it to your .env file.")
        if genai is None:
            raise RuntimeError("google-genai is not installed. Run pip install -r requirements.txt.")
        self.client = genai.Client(api_key=self.api_key)

    def generate_document(self, document_type: str, parties: str, terms: str, effective_date: str) -> str:
        prompt = f'''Create a draft for the following legal document.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

EFFECTIVE DATE:
{effective_date}

USER-SUPPLIED TERMS:
{terms}

Return only the document body. Use clear numbered headings and paragraphs. Do not add facts that are not supplied.
'''
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
            max_output_tokens=8192,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty document.")
        return text.strip()
