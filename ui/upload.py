"""Upload-Tab der Streamlit-App."""

import tempfile
from pathlib import Path

import streamlit as st
from loguru import logger

from core.config import get_settings
from core.document_parser import parse_document

settings = get_settings()


def render_upload_tab() -> None:
    """Rendert den Tab für Upload und Parsing."""
    st.subheader("Urkunde hochladen")

    uploaded_file = st.file_uploader(
        "Urkunde auswählen (PDF, DOCX, RTF, TXT)",
        type=["pdf", "docx", "rtf", "txt"],
        help="Maximal 50 MB. Die Datei wird ausschließlich lokal verarbeitet.",
    )

    if uploaded_file is not None:
        col_btn, col_info = st.columns([1, 3])
        with col_info:
            st.write(f"**Datei**: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

        if col_btn.button("🔍 Dokument analysieren", type="primary"):
            _parse_uploaded_file(uploaded_file)

    # Vorschau des geparsten Dokuments
    if st.session_state.parsed_document is not None:
        _render_document_preview()


def _parse_uploaded_file(uploaded_file) -> None:
    with st.spinner("Dokument wird geparst …"):
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            parsed = parse_document(tmp_path)
            st.session_state.parsed_document = parsed
            st.session_state.workflow_step = "preview"
        except Exception as e:
            st.error("Fehler beim Parsen des Dokuments. Bitte überprüfen Sie das Dateiformat.")
            logger.error(f"Parse-Fehler: {type(e).__name__}")
            st.session_state.parsed_document = None
        finally:
            Path(tmp_path).unlink(missing_ok=True)


def _render_document_preview() -> None:
    doc = st.session_state.parsed_document
    st.divider()
    st.subheader("📝 Geparster Dokumententext")

    col_q, col_l = st.columns(2)
    col_q.metric("Extraktionsqualität", doc.extraction_quality.value)
    col_l.metric("Textlänge", f"{len(doc.full_text):,} Zeichen")

    with st.expander("📄 Volltext anzeigen", expanded=False):
        st.text_area(
            "Dokumententext",
            value=doc.full_text,
            height=400,
            disabled=True,
            label_visibility="collapsed",
        )

    if st.button("→ Zur Extraktion", type="primary"):
        if st.session_state.notary_profile is None:
            st.warning("Bitte zuerst das Notar-Profil in der Sidebar ausfüllen.")
        else:
            st.session_state.workflow_step = "extraction"
            st.rerun()
