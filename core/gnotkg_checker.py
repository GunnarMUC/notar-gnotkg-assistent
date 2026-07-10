"""GNotKG-Aktualitätsprüfung via gesetze-im-internet.de."""

import re
from datetime import datetime, timezone

import httpx
from loguru import logger

from core.config import get_settings
from core.models import GnotkgStatus


def check_gnotkg_version() -> GnotkgStatus:
    """Prüft die aktuelle GNotKG-Version via gesetze-im-internet.de.

    Returns:
        GnotkgStatus mit Vergleichsergebnis.
    """
    settings = get_settings()
    status = GnotkgStatus(
        local_version="GNotKG_Stand_2026-01-01_v1",
        checked_at=datetime.now(timezone.utc),
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

        # Suche nach "Stand:" gefolgt von Datum oder Änderungsinfo
        match = re.search(
            r"Stand(?: der letzten Änderung)?[:\s]+.*?(\d{2}\.\d{2}\.\d{4})",
            response.text,
        )
        if match:
            status.remote_version = match.group(1)
        else:
            # Alternative: "Zuletzt geändert durch ... vom DD.MM.YYYY"
            match = re.search(
                r"zuletzt geändert.*?(\d{1,2}\.\d{1,2}\.\d{4})",
                response.text,
                re.IGNORECASE,
            )
            if match:
                status.remote_version = match.group(1)
            else:
                logger.warning("Konnte GNotKG-Version nicht aus der Webseite extrahieren")
                status.error = "Konnte Versionsdatum nicht extrahieren"
                return status

        # Versionsvergleich (vereinfacht)
        if status.remote_version:
            local_year = 2026
            remote_year = _extract_year(status.remote_version)
            status.is_current = remote_year >= local_year
            logger.info(
                f"GNotKG-Check: lokal={local_year}, "
                f"remote={status.remote_version}, aktuell={status.is_current}"
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


def _extract_year(date_str: str) -> int:
    """Extrahiert das Jahr aus einem Datumstring (DD.MM.YYYY)."""
    try:
        parts = date_str.strip().split(".")
        if len(parts) >= 3:
            return int(parts[-1])
    except (ValueError, IndexError):
        pass
    return 0
