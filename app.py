"""Notar GNotKG Assistent – Haupt-App (Streamlit)."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.config import get_settings

st.set_page_config(
    page_title="Notar GNotKG Assistent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

settings = get_settings()

# ---------------------------------------------------------------------------
# Session-State initialisieren
# ---------------------------------------------------------------------------
DEFAULTS = {
    "notary_profile": None,
    "parsed_document": None,
    "extraction_result": None,
    "final_positions": [],
    "generated_invoice": None,
    "llm_model": settings.ollama_default_model,
    "gnotkg_status": None,
    "workflow_step": "upload",  # upload | preview | extraction | review | invoice
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def load_notary_profile() -> dict | None:
    path = Path(settings.app_data_dir) / "notary_profile.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_notary_profile(profile: dict) -> None:
    path = Path(settings.app_data_dir) / "notary_profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")


def list_ollama_models() -> list[str]:
    import ollama

    try:
        client = ollama.Client(host=settings.ollama_url)
        models = client.list()
        return [m.model for m in models]
    except Exception:
        return [settings.ollama_default_model]


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Einstellungen")

    # Notar-Profil
    if st.session_state.notary_profile is None:
        st.session_state.notary_profile = load_notary_profile()

    with st.expander("👤 Notar-Profil", expanded=st.session_state.notary_profile is None):
        profile = st.session_state.notary_profile or {}
        col1, col2 = st.columns(2)
        name = col1.text_input("Name", value=profile.get("name", ""))
        firm_name = col2.text_input("Kanzlei", value=profile.get("firm_name", ""))
        address = st.text_area("Adresse", value=profile.get("address", ""))
        col3, col4 = st.columns(2)
        phone = col3.text_input("Telefon", value=profile.get("phone", ""))
        email = col4.text_input("E-Mail", value=profile.get("email", ""))
        col5, col6 = st.columns(2)
        bank_name = col5.text_input("Bank", value=profile.get("bank_name", ""))
        iban = col6.text_input("IBAN", value=profile.get("iban", ""))
        bic = st.text_input("BIC", value=profile.get("bic", ""))
        tax_number = st.text_input("Steuernummer", value=profile.get("tax_number", ""))
        vat_id = st.text_input("USt-ID", value=profile.get("vat_id", ""))

        if st.button("💾 Profil speichern"):
            new_profile = {
                "name": name,
                "firm_name": firm_name,
                "address": address,
                "phone": phone,
                "email": email,
                "bank_name": bank_name,
                "iban": iban,
                "bic": bic,
                "tax_number": tax_number,
                "vat_id": vat_id,
            }
            save_notary_profile(new_profile)
            st.session_state.notary_profile = new_profile
            st.success("Profil gespeichert!")

    st.divider()

    # LLM-Modell
    with st.expander("🧠 LLM-Modell", expanded=False):
        try:
            models = list_ollama_models()
        except Exception:
            models = [settings.ollama_default_model]
        selected_model = st.selectbox(
            "Modell",
            options=models,
            index=(
                models.index(st.session_state.llm_model)
                if st.session_state.llm_model in models
                else 0
            ),
        )
        st.session_state.llm_model = selected_model
        st.caption(f"Ollama: `{settings.ollama_url}`")

    st.divider()

    # GNotKG-Status (placeholder)
    with st.expander("📜 GNotKG-Status", expanded=False):
        status = st.session_state.gnotkg_status
        if status and status.is_current:
            st.success("✅ GNotKG aktuell")
        elif status and not status.is_current:
            st.warning(f"⚠️ GNotKG veraltet – Aktueller Stand: {status.remote_version}")
        else:
            st.info("ℹ️ Noch nicht geprüft")

    st.divider()
    st.caption("Notar GNotKG Assistent v0.1.0")
    st.caption("Alle Daten bleiben lokal. Keine Cloud.")


# ---------------------------------------------------------------------------
# Hauptbereich
# ---------------------------------------------------------------------------
st.title("⚖️ Notar GNotKG Assistent")
st.caption("GNotKG-konforme Honorarrechnung aus Ihrer Urkunde – mit lokalem KI-Assistent")

# Workflow-Steps als Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📤 Upload", "🔍 Extraktion", "✏️ Prüfung", "📄 Rechnung"]
)

# ---------------------------------------------------------------------------
# Tab 1: Upload & Parsing
# ---------------------------------------------------------------------------
with tab1:
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
            with st.spinner("Dokument wird geparst …"):
                # Temporäre Datei
                suffix = Path(uploaded_file.name).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                try:
                    from core.document_parser import parse_document

                    parsed = parse_document(tmp_path)
                    st.session_state.parsed_document = parsed
                    st.session_state.workflow_step = "preview"
                except Exception as e:
                    st.error("Fehler beim Parsen des Dokuments. Bitte überprüfen Sie das Dateiformat.")
                    logger.error(f"Parse-Fehler: {type(e).__name__}")
                    st.session_state.parsed_document = None
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

    # Vorschau des geparsten Dokuments
    if st.session_state.parsed_document is not None:
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

# ---------------------------------------------------------------------------
# Tab 2: Extraktion (LLM)
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("🤖 KI-Extraktion")

    if st.session_state.parsed_document is None:
        st.info("Bitte zuerst eine Urkunde hochladen und analysieren (Tab 1).")
    elif st.session_state.extraction_result is None:
        st.write("Die KI analysiert den Dokumententext und schlägt relevante Positionen vor.")

        if st.button("🧠 Extraktion starten", type="primary"):
            try:
                from core.llm_extractor import extract_from_text

                with st.spinner(
                    f"LLM ({st.session_state.llm_model}) extrahiert Positionen …"
                ):
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
            except Exception as e:
                st.error(
                    "Fehler bei der Extraktion. "
                    "Bitte überprüfen Sie, ob Ollama läuft und das Modell verfügbar ist."
                )
    else:
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

# ---------------------------------------------------------------------------
# Tab 3: Prüfung & Bearbeitung
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("✏️ Positionen prüfen und bearbeiten")

    if not st.session_state.final_positions:
        st.info("Keine Positionen vorhanden. Bitte zuerst die Extraktion durchführen (Tab 2).")
    else:
        import pandas as pd

        df = pd.DataFrame(st.session_state.final_positions)

        # Neue Berechnung wenn FeeEngine verfügbar
        try:
            from core.fee_engine import FeeEngine

            engine = FeeEngine()
            for i, row in df.iterrows():
                if row["kv_number"] and row["business_value_eur"]:
                    calc = engine.calculate_position(
                        row["kv_number"], row["business_value_eur"]
                    )
                    df.at[i, "fee_amount"] = calc.fee_amount
                    df.at[i, "description"] = calc.description
        except (ImportError, ModuleNotFoundError):
            pass

        edited_df = st.data_editor(
            df,
            column_config={
                "kv_number": st.column_config.TextColumn("KV-Nr.", width="small"),
                "description": st.column_config.TextColumn("Beschreibung"),
                "business_value_eur": st.column_config.NumberColumn(
                    "Geschäftswert (€)", format="%.2f"
                ),
                "fee_amount": st.column_config.NumberColumn(
                    "Gebühr (€)", format="%.2f", disabled=True
                ),
                "source_reference": st.column_config.TextColumn("Fundstelle"),
                "confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0.0, max_value=1.0, format="%.0f%%"
                ),
                "reasoning": st.column_config.TextColumn("Begründung", width="medium"),
                "was_overridden": st.column_config.CheckboxColumn(
                    "Manuell geändert", disabled=True
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="position_editor",
            hide_index=True,
        )

        # Gesamtsumme
        total_net = edited_df["fee_amount"].sum()
        vat = total_net * settings.app_vat_rate
        total_gross = total_net + vat

        col_sum, col_vat, col_gross = st.columns(3)
        col_sum.metric("Netto", f"{total_net:,.2f} €")
        col_vat.metric("USt (19 %)", f"{vat:,.2f} €")
        col_gross.metric("Brutto", f"{total_gross:,.2f} €")

        st.divider()

        # Auslagen
        with st.expander("💰 Auslagen & Pauschalen"):
            col_a1, col_a2 = st.columns(2)
            dokumentenpauschale = col_a1.number_input(
                "Dokumentenpauschale (€)", value=0.0, step=0.50
            )
            post_telekom = col_a2.number_input(
                "Post/Telekom (€)", value=0.0, step=0.50
            )
            sonstige = st.number_input("Sonstige Auslagen (€)", value=0.0, step=1.0)

        # Bestätigung
        st.divider()
        confirmed = st.checkbox(
            "✅ Ich habe alle Positionen geprüft und bestätige die finale Rechnung.",
            value=False,
        )

        st.caption(
            "⚠️ **Haftungshinweis**: Die alleinige Verantwortung "
            "für die Richtigkeit und die Einhaltung des GNotKG liegt beim Notar."
        )

        if confirmed:
            if st.button("📄 Rechnung generieren", type="primary"):
                st.session_state.final_positions = edited_df.to_dict("records")
                st.session_state.workflow_step = "invoice"
                st.rerun()

# ---------------------------------------------------------------------------
# Tab 4: Rechnung & Export
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("📄 Honorarrechnung")

    if not st.session_state.final_positions:
        st.info("Bitte zuerst Positionen prüfen und bestätigen (Tab 3).")
    else:
        st.success("Rechnung zur Generierung bereit.")

        total_net = sum(p.get("fee_amount", 0) for p in st.session_state.final_positions)
        vat = total_net * settings.app_vat_rate
        total_gross = total_net + vat

        st.write("### Zusammenfassung")
        col1, col2, col3 = st.columns(3)
        col1.metric("Netto", f"{total_net:,.2f} €")
        col2.metric("USt (19 %)", f"{vat:,.2f} €")
        col3.metric("**Brutto**", f"**{total_gross:,.2f} €**")

        st.write("### Positionen")
        import pandas as pd

        st.dataframe(
            pd.DataFrame(st.session_state.final_positions),
            use_container_width=True,
            hide_index=True,
        )

        col_fmt, col_gen = st.columns([1, 1])
        output_format = col_fmt.selectbox(
            "Ausgabeformat", options=["docx", "rtf", "txt"], index=0
        )

        if col_gen.button("📥 Rechnung + Excel-Log erzeugen", type="primary"):
            with st.spinner("Rechnung wird erstellt …"):
                try:
                    from core.invoice_generator import generate_invoice
                    from core.excel_logger import create_audit_log

                    profile = st.session_state.notary_profile or {}
                    content, invoice = generate_invoice(
                        final_positions=st.session_state.final_positions,
                        notary=profile,
                        original_document=(
                            st.session_state.parsed_document.metadata.get(
                                "original_filename", ""
                            )
                            if st.session_state.parsed_document
                            else ""
                        ),
                        output_format=output_format,
                    )

                    audit_bytes = create_audit_log(invoice)

                    st.session_state.generated_invoice = invoice
                    st.session_state.generated_audit = audit_bytes

                    st.download_button(
                        label=f"⬇️ Rechnung herunterladen (.{output_format})",
                        data=content,
                        file_name=f"Rechnung_{datetime.now().strftime('%Y-%m-%d')}.{output_format}",
                        mime=(
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            if output_format == "docx"
                            else "text/richtext" if output_format == "rtf" else "text/plain"
                        ),
                    )

                    st.download_button(
                        label="📊 Excel-Traceability-Log herunterladen (.xlsx)",
                        data=audit_bytes,
                        file_name=f"Traceability_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                    st.success("✅ Rechnung und Audit-Log erfolgreich erstellt!")
                except Exception as e:
                    st.error(
                        "Fehler bei der Rechnungserstellung. "
                        "Bitte versuchen Sie es erneut."
                    )

        st.divider()
        st.caption(
            "⚠️ **Disclaimer**: Diese Rechnung wurde mit Unterstützung eines KI-Tools erstellt. "
            "Die alleinige Verantwortung für die Richtigkeit und die Einhaltung "
            "des Gerichts- und Notarkostengesetzes (GNotKG) liegt beim Notar."
        )
