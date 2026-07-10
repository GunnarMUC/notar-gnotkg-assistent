"""Sidebar-Komponenten der Streamlit-App."""

import streamlit as st

from core.config import get_settings
from ui.helpers import list_ollama_models, load_notary_profile, save_notary_profile

settings = get_settings()


def render_sidebar() -> None:
    """Rendert die gesamte Sidebar."""
    with st.sidebar:
        st.header("⚙️ Einstellungen")

        _render_profile_section()
        st.divider()
        _render_model_section()
        st.divider()
        _render_gnotkg_status_section()
        st.divider()
        st.caption("Notar GNotKG Assistent v0.1.0")
        st.caption("Alle Daten bleiben lokal. Keine Cloud.")


def _render_profile_section() -> None:
    expanded = st.session_state.notary_profile is None

    with st.expander("👤 Notar-Profil", expanded=expanded):
        # Wenn noch nicht geladen, Passwort-Abfrage anzeigen
        if st.session_state.notary_profile is None:
            password = st.text_input(
                "Master-Passwort (falls Profil verschlüsselt)",
                type="password",
                key="profile_load_password",
                help="Leer lassen, wenn das Profil unverschlüsselt ist.",
            )
            if st.button("🔓 Profil laden"):
                profile, error = load_notary_profile(password or None)
                if error:
                    st.error(error)
                else:
                    st.session_state.notary_profile = profile
                    st.success("Profil geladen" if profile else "Kein Profil vorhanden")
                    st.rerun()
            return

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

        st.divider()
        password = st.text_input(
            "Master-Passwort für Verschlüsselung",
            type="password",
            key="profile_save_password",
            help="Mindestens 8 Zeichen empfohlen. Ohne Passwort wird das Profil unverschlüsselt gespeichert.",
        )
        password_confirm = st.text_input(
            "Passwort wiederholen", type="password", key="profile_save_password_confirm"
        )

        if st.button("💾 Profil speichern"):
            if password and password != password_confirm:
                st.error("Passwörter stimmen nicht überein.")
                return

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
            save_notary_profile(new_profile, password or None)
            st.session_state.notary_profile = new_profile
            if password:
                st.success("Profil verschlüsselt gespeichert!")
            else:
                st.warning(
                    "Profil unverschlüsselt gespeichert. Bitte aus Sicherheitsgründen ein Passwort setzen."
                )


def _render_model_section() -> None:
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


def _render_gnotkg_status_section() -> None:
    with st.expander("📜 GNotKG-Status", expanded=False):
        status = st.session_state.gnotkg_status
        if status and status.is_current:
            st.success("✅ GNotKG aktuell")
        elif status and not status.is_current:
            st.warning(f"⚠️ GNotKG veraltet – Aktueller Stand: {status.remote_version}")
        else:
            st.info("ℹ️ Noch nicht geprüft")
