"""Rechnungs-Tab der Streamlit-App."""

from datetime import datetime

import pandas as pd
import streamlit as st

from core.config import get_settings
from core.excel_logger import create_audit_log
from core.invoice_generator import generate_invoice

settings = get_settings()


def render_invoice_tab() -> None:
    """Rendert den Tab für Rechnungserstellung und Export."""
    st.subheader("📄 Honorarrechnung")

    if not st.session_state.final_positions:
        st.info("Bitte zuerst Positionen prüfen und bestätigen (Tab 3).")
        return

    st.success("Rechnung zur Generierung bereit.")

    _render_summary()
    _render_positions_table()

    col_fmt, col_gen = st.columns([1, 1])
    output_format = col_fmt.selectbox("Ausgabeformat", options=["docx", "rtf", "txt"], index=0)

    if col_gen.button("📥 Rechnung + Excel-Log erzeugen", type="primary"):
        _generate_invoice(output_format)

    st.divider()
    st.caption(
        "⚠️ **Disclaimer**: Diese Rechnung wurde mit Unterstützung eines KI-Tools erstellt. "
        "Die alleinige Verantwortung für die Richtigkeit und die Einhaltung "
        "des Gerichts- und Notarkostengesetzes (GNotKG) liegt beim Notar."
    )


def _render_summary() -> None:
    total_net = sum(p.get("fee_amount", 0) for p in st.session_state.final_positions)
    vat = total_net * settings.app_vat_rate
    total_gross = total_net + vat

    st.write("### Zusammenfassung")
    col1, col2, col3 = st.columns(3)
    col1.metric("Netto", f"{total_net:,.2f} €")
    col2.metric("USt (19 %)", f"{vat:,.2f} €")
    col3.metric("**Brutto**", f"**{total_gross:,.2f} €**")


def _render_positions_table() -> None:
    st.write("### Positionen")
    st.dataframe(
        pd.DataFrame(st.session_state.final_positions),
        use_container_width=True,
        hide_index=True,
    )


def _generate_invoice(output_format: str) -> None:
    with st.spinner("Rechnung wird erstellt …"):
        try:
            profile = st.session_state.notary_profile or {}
            original_document = ""
            if st.session_state.parsed_document:
                original_document = st.session_state.parsed_document.metadata.get(
                    "original_filename", ""
                )

            content, invoice = generate_invoice(
                final_positions=st.session_state.final_positions,
                notary=profile,
                original_document=original_document,
                output_format=output_format,
            )
            audit_bytes = create_audit_log(invoice)

            st.session_state.generated_invoice = invoice
            st.session_state.generated_audit = audit_bytes

            _render_download_buttons(content, audit_bytes, output_format)
            st.success("✅ Rechnung und Audit-Log erfolgreich erstellt!")
        except Exception:
            st.error("Fehler bei der Rechnungserstellung. Bitte versuchen Sie es erneut.")


def _render_download_buttons(content: bytes, audit_bytes: bytes, output_format: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    mime = _mime_for_format(output_format)

    st.download_button(
        label=f"⬇️ Rechnung herunterladen (.{output_format})",
        data=content,
        file_name=f"Rechnung_{today}.{output_format}",
        mime=mime,
    )

    st.download_button(
        label="📊 Excel-Traceability-Log herunterladen (.xlsx)",
        data=audit_bytes,
        file_name=f"Traceability_{today}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _mime_for_format(output_format: str) -> str:
    if output_format == "docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if output_format == "rtf":
        return "text/richtext"
    return "text/plain"
