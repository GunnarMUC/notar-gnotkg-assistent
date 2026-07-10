"""Verschlüsselung für das Notar-Profil.

Das Profil wird mit einem vom Nutzer vergebenen Master-Passwort per Fernet
(PBKDF2HMAC-Schlüsselableitung) verschlüsselt. Ohne Passwort wird es als
Klartext gespeichert, aber mit Warnung.
"""

import base64
import json
import os
from typing import Any, cast

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class ProfileCryptoError(ValueError):
    """Fehler bei der Ver- oder Entschlüsselung des Profils."""


SALT_LENGTH = 16
ITERATIONS = 480_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Leitet einen Fernet-Schlüssel aus Passwort und Salt ab."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_profile(profile: dict[str, Any], password: str) -> dict[str, str]:
    """Verschlüsselt ein Profil-Dictionary mit einem Passwort.

    Args:
        profile: Das zu verschlüsselnde Profil.
        password: Master-Passwort.

    Returns:
        Dictionary mit salt (base64) und ciphertext (base64).
    """
    salt = os.urandom(SALT_LENGTH)
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    plaintext = json.dumps(profile, ensure_ascii=False).encode("utf-8")
    ciphertext = fernet.encrypt(plaintext)
    return {
        "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
        "ciphertext": base64.urlsafe_b64encode(ciphertext).decode("ascii"),
        "encrypted": "true",
    }


def decrypt_profile(encrypted_profile: dict[str, Any], password: str) -> dict[str, Any]:
    """Entschlüsselt ein mit `encrypt_profile` verschlüsseltes Profil.

    Args:
        encrypted_profile: Verschlüsseltes Profil mit salt/ciphertext.
        password: Master-Passwort.

    Returns:
        Entschlüsseltes Profil-Dictionary.

    Raises:
        ProfileCryptoError: Bei falschem Passwort oder ungültigem Format.
    """
    try:
        salt = base64.urlsafe_b64decode(encrypted_profile["salt"].encode("ascii"))
        ciphertext = base64.urlsafe_b64decode(encrypted_profile["ciphertext"].encode("ascii"))
    except (KeyError, ValueError, TypeError) as e:
        raise ProfileCryptoError("Ungültiges verschlüsseltes Profilformat") from e

    key = _derive_key(password, salt)
    fernet = Fernet(key)
    try:
        plaintext = fernet.decrypt(ciphertext)
    except InvalidToken as e:
        raise ProfileCryptoError("Falsches Master-Passwort oder beschädigte Datei") from e

    return cast(dict[str, Any], json.loads(plaintext.decode("utf-8")))


def is_encrypted_profile(profile: dict[str, Any]) -> bool:
    """Prüft, ob ein Profil als verschlüsselte Datei vorliegt."""
    return profile.get("encrypted") == "true" and "ciphertext" in profile
