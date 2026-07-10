"""Prüfungs- und Bearbeitungs-Tab der Streamlit-App."""

import pandas as pd
import streamlit as st

from core.config import get_settings
from core.fee_engine import FeeEngine

settings = get_settings()


def render_review_tab() -> None:
    """Rendert den Tab zur Prüfung und Bearbeitung der Positionen."""
    st.subheader("✏️ Positionen prüfen und bearbeiten")

    if not st.session_state.final_positions:
        st.info("Keine Positionen vorhanden. Bitte zuerst die Extraktion durchführen (Tab 2).")
        return

    df = _build_positions_dataframe()
    edited_df = _render_position_editor(df)

    _render_summary(edited_df)
    _render_auslagen()

    st.divider()
    confirmed = st.checkbox(
        "✅ Ich habe alle Positionen geprüft und bestätige die finale Rechnung.",
        value=False,
    )

    st.caption(
        "⚠️ **Haftungshinweis**: Die alleinige Verantwortung "
        "für die Richtigkeit und die Einhaltung des GNotKG liegt beim Notar."
    )

    if confirmed and st.button("📄 Rechnung generieren", type="primary"):
        st.session_state.final_positions = edited_df.to_dict("records")
        st.session_state.workflow_step = "invoice"
        st.rerun()


def _build_positions_dataframe() -> pd.DataFrame:
    df = pd.DataFrame(st.session_state.final_positions)

    try:
        engine = FeeEngine()
        for i, row in df.iterrows():
            if row["kv_number"] and row["business_value_eur"]:
                calc = engine.calculate_position(row["kv_number"], row["business_value_eur"])
                df.at[i, "fee_amount"] = calc.fee_amount
                df.at[i, "description"] = calc.description
    except (ImportError, ModuleNotFoundError):
        pass

    return df


def _render_position_editor(df: pd.DataFrame) -> pd.DataFrame:
    return st.data_editor(
        df,
        column_config={
            "kv_number": st.column_config.TextColumn("KV-Nr.", width="small"),
            "description": st.column_config.TextColumn("Beschreibung"),
            "business_value_eur": st.column_config.NumberColumn("Geschäftswert (€)", format="%.2f"),
            "fee_amount": st.column_config.NumberColumn("Gebühr (€)", format="%.2f", disabled=True),
            "source_reference": st.column_config.TextColumn("Fundstelle"),
            "confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0.0, max_value=1.0, format="%.0f%%"
            ),
            "reasoning": st.column_config.TextColumn("Begründung", width="medium"),
            "was_overridden": st.column_config.CheckboxColumn("Manuell geändert", disabled=True),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="position_editor",
        hide_index=True,
    )


def _render_summary(df: pd.DataFrame) -> None:
    total_net = df["fee_amount"].sum()
    vat = total_net * settings.app_vat_rate
    total_gross = total_net + vat

    col_sum, col_vat, col_gross = st.columns(3)
    col_sum.metric("Netto", f"{total_net:,.2f} €")
    col_vat.metric("USt (19 %)", f"{vat:,.2f} €")
    col_gross.metric("Brutto", f"{total_gross:,.2f} €")

    st.divider()


def _render_auslagen() -> None:
    with st.expander("💰 Auslagen & Pauschalen"):
        col_a1, col_a2 = st.columns(2)
        dokumentenpauschale = col_a1.number_input("Dokumentenpauschale (€)", value=0.0, step=0.50)
        post_telekom = col_a2.number_input("Post/Telekom (€)", value=0.0, step=0.50)
        st.number_input("Sonstige Auslagen (€)", value=0.0, step=1.0)

    # Auslagen werden aktuell noch nicht in die Rechnung übernommen; TODO
    _ = dokumentenpauschale
    _ = post_telekom
