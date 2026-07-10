"""Tests für den GNotKG-Checker."""

import pytest
from pytest_mock import MockerFixture

from core.gnotkg_checker import LOCAL_GNOTKG_DATE, check_gnotkg_version


@pytest.fixture
def enabled_settings(mocker: MockerFixture):
    settings = type(
        "Settings",
        (),
        {"app_gnotkg_check_enabled": True},
    )()
    mocker.patch("core.gnotkg_checker.get_settings", return_value=settings)
    return settings


class TestCheckGnotkgVersion:
    def test_remote_same_date(self, mocker: MockerFixture, enabled_settings):
        mock_response = mocker.MagicMock()
        mock_response.text = f"Stand der letzten Änderung: {LOCAL_GNOTKG_DATE.strftime('%d.%m.%Y')}"
        mocker.patch("core.gnotkg_checker.httpx.get", return_value=mock_response)

        status = check_gnotkg_version()

        assert status.is_current is True
        assert LOCAL_GNOTKG_DATE.strftime("%d.%m.%Y") in (status.remote_version or "")
        assert status.error is None

    def test_remote_older_date(self, mocker: MockerFixture, enabled_settings):
        mock_response = mocker.MagicMock()
        mock_response.text = "Stand: 01.01.2025"
        mocker.patch("core.gnotkg_checker.httpx.get", return_value=mock_response)

        status = check_gnotkg_version()

        assert status.is_current is True
        assert status.remote_version == "01.01.2025"
        assert status.error is None

    def test_remote_newer_date(self, mocker: MockerFixture, enabled_settings):
        mock_response = mocker.MagicMock()
        mock_response.text = "Stand: 15.07.2026"
        mocker.patch("core.gnotkg_checker.httpx.get", return_value=mock_response)

        status = check_gnotkg_version()

        assert status.is_current is False
        assert status.remote_version == "15.07.2026"
        assert status.error is None

    def test_no_date_found(self, mocker: MockerFixture, enabled_settings):
        mock_response = mocker.MagicMock()
        mock_response.text = "Kein Versionsdatum auf dieser Seite"
        mocker.patch("core.gnotkg_checker.httpx.get", return_value=mock_response)

        status = check_gnotkg_version()

        assert status.is_current is True  # Default
        assert status.remote_version is None
        assert status.error == "Konnte Versionsdatum nicht extrahieren"

    def test_disabled_in_settings(self, mocker: MockerFixture):
        settings = type("Settings", (), {"app_gnotkg_check_enabled": False})()
        mocker.patch("core.gnotkg_checker.get_settings", return_value=settings)
        mock_get = mocker.patch("core.gnotkg_checker.httpx.get")

        status = check_gnotkg_version()

        assert status.is_current is True
        mock_get.assert_not_called()

    def test_no_internet_connection(self, mocker: MockerFixture, enabled_settings):
        import httpx

        mocker.patch(
            "core.gnotkg_checker.httpx.get", side_effect=httpx.ConnectError("No connection")
        )

        status = check_gnotkg_version()

        assert status.is_current is True
        assert status.error == "Keine Internetverbindung"

    def test_timeout(self, mocker: MockerFixture, enabled_settings):
        import httpx

        mocker.patch("core.gnotkg_checker.httpx.get", side_effect=httpx.TimeoutException("Timeout"))

        status = check_gnotkg_version()

        assert status.is_current is True
        assert status.error == "Timeout – gesetze-im-internet.de nicht erreichbar"

    def test_alternative_regex(self, mocker: MockerFixture, enabled_settings):
        mock_response = mocker.MagicMock()
        mock_response.text = "Zuletzt geändert durch Artikel 5 vom 01.03.2025"
        mocker.patch("core.gnotkg_checker.httpx.get", return_value=mock_response)

        status = check_gnotkg_version()

        assert status.remote_version == "01.03.2025"
        assert status.is_current is True
