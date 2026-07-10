"""Extraktions-Tab der Streamlit-App."""

import streamlit as st

from core.llm_extractor import extract_from_text


def render_extraction_tab() -> None:
    """Rendert den Tab für die LLM-gestützte Extraktion."""
    st.subheader("🤖 KI-Extraktion")

    if st.session_state.parsed_document is None:
        st.info("Bitte zuerst eine Urkunde hochladen und analysieren (Tab 1).")
        return

    if st.session_state.extraction_result is None:
        _run_extraction()
    else:
        _render_extraction_result()


def _run_extraction() -> None:
    st.write("Die KI analysiert den Dokumententext und schlägt relevante Positionen vor.")

    if st.button("🧠 Extraktion starten", type="primary"):
        try:
            with st.spinner(f"LLM ({st.session_state.llm_model}) extrahiert Positionen …"):
                result = extract_from_text(
                    text=st.session_state.parsed_document.full_text,
                    model=st.session_state.llm_model,
                )
                st.session_state.extraction_result = result
                st.session_state.final_positions = [
                    {
                        "kv_number": p.kv_number or "",
                        "description": p.description,
                        "business_value_eur": p.business_value_eur,
                        "source_reference": p.source_reference,
                        "confidence": p.confidence,
                        "reasoning": p.reasoning,
                        "was_overridden": False,
                        "fee_amount": 0.0,
                    }
                    for p in result.extracted_positions
                ]
                st.rerun()
        except Exception:
            st.error(
                "Fehler bei der Extraktion. "
                "Bitte überprüfen Sie, ob Ollama läuft und das Modell verfügbar ist."
            )


def _render_extraction_result() -> None:
    result = st.session_state.extraction_result
    st.success(
        f"Extraktion abgeschlossen – "
        f"{len(result.extracted_positions)} Positionen gefunden "
        f"(Dokumenttyp: {result.document_type})"
    )
    if result.notes:
        st.info(result.notes)

    st.write("**Erkannte Beteiligte:**")
    for party in result.parties:
        st.write(f"- {party.get('name', '?')} ({party.get('role', '?')})")

    if st.button("→ Zur Prüfung", type="primary"):
        st.session_state.workflow_step = "review"
        st.rerun()
