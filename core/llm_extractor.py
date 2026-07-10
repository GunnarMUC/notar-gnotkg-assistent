"""LLM-gestützte Extraktion von Urkundeninhalten via Ollama."""

import json
from pathlib import Path

import ollama
from loguru import logger

from core.config import get_settings
from core.models import ExtractedPosition, ExtractionResult


_PROMPT_CACHE: str | None = None


def _load_prompt(version: str = "v1") -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE

    prompt_path = Path("prompts") / f"extraction_{version}.txt"
    if prompt_path.exists():
        _PROMPT_CACHE = prompt_path.read_text(encoding="utf-8")
    else:
        logger.warning(f"Prompt-Datei nicht gefunden: {prompt_path}")
        _PROMPT_CACHE = ""
    return _PROMPT_CACHE


def extract_from_text(
    text: str,
    model: str | None = None,
    temperature: float | None = None,
    max_retries: int = 2,
) -> ExtractionResult:
    """Extrahiert GNotKG-relevante Informationen per lokalem LLM.

    Args:
        text: Volltext der Urkunde.
        model: Ollama-Modellname. Default aus Config.
        temperature: LLM-Temperatur. Default aus Config.
        max_retries: Anzahl Wiederholungsversuche bei JSON-Fehlern.

    Returns:
        ExtractionResult mit extrahierten Positionen und Metadaten.
    """
    settings = get_settings()
    model = model or settings.ollama_default_model
    temperature = temperature or settings.llm_temperature

    system_prompt = _load_prompt()
    user_prompt = f"""Hier ist der Text der notariellen Urkunde:

--- BEGINN URKUNDE ---
{text}
--- ENDE URKUNDE ---

Extrahiere jetzt die relevanten Informationen für die GNotKG-Honorarrechnung."""

    client = ollama.Client(host=settings.ollama_url)

    for attempt in range(1, max_retries + 2):
        try:
            logger.info(
                f"LLM-Aufruf (Versuch {attempt}): Modell={model}, "
                f"Textlänge={len(text)} Zeichen"
            )

            response = client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                options={
                    "temperature": temperature,
                    "num_predict": 4096,
                },
                format="json",
            )

            raw = response.message.content
            logger.debug(f"LLM-Antwort (roh): {raw[:500]}...")

            # JSON extrahieren (ggf. aus Markdown-Codeblock)
            data = _parse_json_response(raw)

            positions = []
            for pos_data in data.get("extracted_positions", []):
                try:
                    positions.append(
                        ExtractedPosition(
                            kv_number=pos_data.get("kv_number"),
                            description=pos_data.get("description", ""),
                            business_value_eur=pos_data.get("business_value_eur"),
                            source_reference=pos_data.get("source_reference", ""),
                            confidence=float(pos_data.get("confidence", 0.0)),
                            reasoning=pos_data.get("reasoning", ""),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Position übersprungen (Validation): {e}")

            result = ExtractionResult(
                extracted_positions=positions,
                parties=data.get("parties", []),
                document_type=data.get("document_type", ""),
                overall_confidence=float(data.get("overall_confidence", 0.0)),
                notes=data.get("notes", ""),
            )

            logger.info(
                f"Extraktion erfolgreich: {len(positions)} Positionen, "
                f"Confidence={result.overall_confidence:.2f}"
            )
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON-Fehler (Versuch {attempt}/{max_retries + 1}): {e}")
            if attempt > max_retries:
                raise RuntimeError(
                    f"LLM konnte kein gültiges JSON liefern (nach {attempt} Versuchen). "
                    "Bitte anderes Modell oder manuelle Eingabe versuchen."
                ) from e

        except Exception as e:
            if "connection refused" in str(e).lower() or "connecterror" in str(e).lower():
                raise RuntimeError(
                    f"Ollama nicht erreichbar unter {settings.ollama_url}. "
                    "Bitte `ollama serve` ausführen."
                ) from e
            raise


def _parse_json_response(raw: str) -> dict:
    """Extrahiert JSON aus LLM-Antwort (ggf. in Markdown-Codeblock)."""
    raw = raw.strip()

    # JSON-Codeblock aus Markdown extrahieren
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Erste und letzte Zeile entfernen (```json und ```)
        if len(lines) > 2:
            lines = lines[1:-1]
        raw = "\n".join(lines)

    # Erstes { und letztes } finden (falls Text drumherum)
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]

    return json.loads(raw)
