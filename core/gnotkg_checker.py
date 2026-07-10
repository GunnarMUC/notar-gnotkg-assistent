"""GNotKG-Aktualitätsprüfung via gesetze-im-internet.de."""

import re
from datetime import UTC, date, datetime

import httpx
from loguru import logger

from core.config import get_settings
from core.models import GnotkgStatus

# Lokaler GNotKG-Stand (aus der implementierten Gebührentabelle)
LOCAL_GNOTKG_DATE = date(2026, 1, 1)


def check_gnotkg_version() -> GnotkgStatus:
    """Prüft die aktuelle GNotKG-Version via gesetze-im-internet.de.

    Returns:
        GnotkgStatus mit Vergleichsergebnis.
    """
    settings = get_settings()
    status = GnotkgStatus(
        local_version=f"GNotKG_Stand_{LOCAL_GNOTKG_DATE.isoformat()}_v1",
        checked_at=datetime.now(UTC),
    )

    if not settings.app_gnotkg_check_enabled:
        logger.info("GNotKG-Check deaktiviert (Config)")
        return status

    try:
        response = httpx.get(
            "https://www.gesetze-im-internet.de/gnotkg/",
            timeout=10.0,
            follow_redirects=True,
        )
        response.raise_for_status()

        remote_date_str = _extract_remote_date(response.text)
        if remote_date_str is None:
            logger.warning("Konnte GNotKG-Version nicht aus der Webseite extrahieren")
            status.error = "Konnte Versionsdatum nicht extrahieren"
            return status

        status.remote_version = remote_date_str
        remote_date = _parse_date(remote_date_str)

        if remote_date is None:
            status.error = f"Ungültiges Datumformat: {remote_date_str}"
            return status

        # Aktuell = remote Stand ist nicht neuer als lokaler Stand
        status.is_current = remote_date <= LOCAL_GNOTKG_DATE
        logger.info(
            f"GNotKG-Check: lokal={LOCAL_GNOTKG_DATE}, "
            f"remote={remote_date}, aktuell={status.is_current}"
        )

    except httpx.ConnectError:
        logger.warning("Keine Internetverbindung – GNotKG-Check übersprungen")
        status.error = "Keine Internetverbindung"
    except httpx.TimeoutException:
        logger.warning("Timeout beim GNotKG-Check")
        status.error = "Timeout – gesetze-im-internet.de nicht erreichbar"
    except Exception as e:
        logger.error(f"Fehler beim GNotKG-Check: {e}")
        status.error = str(e)

    return status


def _extract_remote_date(html: str) -> str | None:
    """Extrahiert das Versionsdatum aus der gesetze-im-internet.de-Seite."""
    match = re.search(
        r"Stand(?: der letzten Änderung)?[:\s]+.*?(\d{2}\.\d{2}\.\d{4})",
        html,
    )
    if match:
        return match.group(1)

    match = re.search(
        r"zuletzt geändert.*?(\d{1,2}\.\d{1,2}\.\d{4})",
        html,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)

    return None


def _parse_date(date_str: str) -> date | None:
    """Parst ein Datum im Format DD.MM.YYYY."""
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None
