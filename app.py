from __future__ import annotations
import os
from datetime import date
import requests
import streamlit as st
from dotenv import load_dotenv
from backend.services.document_formatter import format_docx, format_html_preview, format_pdf, format_txt

load_dotenv()
st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def inject_css() -> None:
    st.markdown("""
    <style>
    .block-container { max-width: 1200px; padding-top: 2rem; }
    .legal-preview { background:#111827; color:#f9fafb; border:1px solid #374151; border-radius:12px; padding:28px; max-height:620px; overflow-y:auto; line-height:1.65; font-family:Georgia,"Times New Roman",serif; }
    .legal-preview h3 { color:#fff; margin-top:18px; margin-bottom:8px; font-size:1.05rem; }
    .notice { border-left:4px solid #d97706; padding:10px 14px; background:#fffbeb; border-radius:4px; }
    </style>
    """, unsafe_allow_html=True)


def generate(payload: dict[str, str]) -> str:
    response = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=180)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(str(detail))
    return response.json()["content"]


def main() -> None:
    inject_css()
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
    _, center, _ = st.columns([1, 2, 1])
    with center:
        if os.path.exists(logo_path):
            st.image(logo_path, width=145)
        st.markdown("<h1 style='text-align:center'>LegalEase</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center'>AI-Powered Legal Document Generator</p>", unsafe_allow_html=True)

    st.markdown('<div class="notice"><b>Review notice:</b> LegalEase creates AI-assisted drafts for informational purposes. Review the final document with a qualified lawyer before signing or relying on it.</div>', unsafe_allow_html=True)
    st.write("")

    with st.sidebar:
        st.subheader("Connection")
        st.code(BACKEND_URL, language="text")
        if st.button("Check backend"):
            try:
                r = requests.get(f"{BACKEND_URL}/health", timeout=5)
                if r.ok: st.success("Backend is healthy.")
                else: st.error(f"Backend returned HTTP {r.status_code}.")
            except requests.RequestException as exc:
                st.error(f"Backend unavailable: {exc}")
        st.divider()
        st.caption("Generated files are prepared in memory and downloaded through your browser.")

    st.subheader("Document details")
    with st.form("legal_document_form"):
        document_type = st.text_input("Document type", placeholder="e.g. Freelance Work Contract, NDA, Lease Agreement")
        parties = st.text_area("Parties involved", placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)", height=100)
        terms = st.text_area("Terms & conditions", placeholder="Payment within 30 days of invoice; Provider delivers work by the agreed deadline; Confidentiality must be maintained", height=150, help="Separate each term with a semicolon (;).")
        effective_date = st.text_input("Effective date", value=date.today().strftime("%B %d, %Y"))
        submitted = st.form_submit_button("Generate Document", type="primary", use_container_width=True)

    if submitted:
        if not all([document_type.strip(), parties.strip(), terms.strip(), effective_date.strip()]):
            st.error("Please complete all fields.")
            return
        with st.spinner("Generating your draft with Gemini..."):
            try:
                content = generate({"document_type": document_type.strip(), "parties": parties.strip(), "terms": terms.strip(), "effective_date": effective_date.strip()})
                st.session_state["document"] = content
                st.session_state["document_type"] = document_type.strip()
                st.session_state["terms"] = terms.strip()
                st.success("Document generated.")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

    content = st.session_state.get("document")
    if not content:
        st.info("Fill in the fields above and click Generate Document.")
        return

    st.divider()
    st.subheader("Document preview")
    tab_preview, tab_edit = st.tabs(["Preview", "Edit Document"])
    with tab_preview:
        st.markdown(format_html_preview(content), unsafe_allow_html=True)
    with tab_edit:
        edited = st.text_area("Editable document", value=content, height=620, key="editable_document")
        if st.button("Apply edits", use_container_width=True):
            st.session_state["document"] = edited
            st.success("Edits applied.")
            st.rerun()

    current = st.session_state.get("document", content)
    doc_type = st.session_state.get("document_type", "Legal Document")
    term_text = st.session_state.get("terms", "")
    st.subheader("Download")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Download TXT", data=format_txt(current), file_name="legalease_document.txt", mime="text/plain", use_container_width=True)
    with c2:
        st.download_button("Download DOCX", data=format_docx(current, doc_type, term_text), file_name="legalease_document.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with c3:
        st.download_button("Download PDF", data=format_pdf(current, doc_type, term_text), file_name="legalease_document.pdf", mime="application/pdf", use_container_width=True)


if __name__ == "__main__":
    main()
