"""UI-Hilfsfunktionen für die Streamlit-App."""

import json
from pathlib import Path

import ollama

from core.config import get_settings
from core.profile_crypto import (
    ProfileCryptoError,
    decrypt_profile,
    encrypt_profile,
    is_encrypted_profile,
)

settings = get_settings()


def load_notary_profile(password: str | None = None) -> tuple[dict | None, str | None]:
    """Lädt das Notar-Profil aus der lokalen JSON-Datei.

    Args:
        password: Master-Passwort, falls das Profil verschlüsselt ist.

    Returns:
        Tuple (profil, fehler). Bei Erfolg ist fehler None.
    """
    path = Path(settings.app_data_dir) / "notary_profile.json"
    if not path.exists():
        return None, None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, f"Profil-Datei ist kein gültiges JSON: {e}"

    if is_encrypted_profile(raw):
        if password is None:
            return None, "Profil ist verschlüsselt. Bitte Master-Passwort eingeben."
        try:
            return decrypt_profile(raw, password), None
        except ProfileCryptoError as e:
            return None, str(e)

    return raw, None


def save_notary_profile(profile: dict, password: str | None = None) -> dict[str, str]:
    """Speichert das Notar-Profil lokal.

    Args:
        profile: Das zu speichernde Profil.
        password: Optional: Master-Passwort für Verschlüsselung.

    Returns:
        Dictionary mit dem gespeicherten Dateiinhalt.
    """
    path = Path(settings.app_data_dir) / "notary_profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    data = encrypt_profile(profile, password) if password else {**profile, "encrypted": "false"}

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def list_ollama_models() -> list[str]:
    """Listet verfügbare Ollama-Modelle auf."""
    try:
        client = ollama.Client(host=settings.ollama_url)
        models = client.list()
        return [str(m.model) for m in models]  # type: ignore[attr-defined]
    except Exception:
        return [settings.ollama_default_model]
