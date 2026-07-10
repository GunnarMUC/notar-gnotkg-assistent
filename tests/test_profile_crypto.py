"""Tests für die Profil-Verschlüsselung."""

import pytest

from core.profile_crypto import (
    ProfileCryptoError,
    decrypt_profile,
    encrypt_profile,
    is_encrypted_profile,
)


class TestProfileCrypto:
    def test_roundtrip(self):
        profile = {"name": "Max Mustermann", "iban": "DE123456789"}
        encrypted = encrypt_profile(profile, "sicheres-passwort-123")
        decrypted = decrypt_profile(encrypted, "sicheres-passwort-123")
        assert decrypted == profile

    def test_wrong_password_raises(self):
        profile = {"name": "Max Mustermann"}
        encrypted = encrypt_profile(profile, "richtig")
        with pytest.raises(ProfileCryptoError, match="Falsches Master-Passwort"):
            decrypt_profile(encrypted, "falsch")

    def test_is_encrypted_profile(self):
        encrypted = encrypt_profile({"name": "x"}, "pw")
        assert is_encrypted_profile(encrypted) is True

    def test_plain_profile_not_encrypted(self):
        assert is_encrypted_profile({"name": "x", "encrypted": "false"}) is False
        assert is_encrypted_profile({"name": "x"}) is False

    def test_invalid_format_raises(self):
        with pytest.raises(ProfileCryptoError, match="Ungültiges verschlüsseltes"):
            decrypt_profile({"salt": "abc"}, "pw")
