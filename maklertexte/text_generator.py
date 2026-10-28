"""Generiert den Makler-Vorstellungstext über die OpenAI Responses-API.

Der Prompt verlangt Informationen "die du im Internet finden kannst", daher
wird das Web-Search-Tool aktiviert. Das Impressum des Maklers wird mitgegeben,
damit das Modell den Makler eindeutig identifizieren kann.

Wichtig: Da Regionalimmobilien24 selbst Finanzdienstleister ist, darf der
Finanzdienstleistungs-Bereich der Makler NICHT beworben werden — der Text
stellt den Anbieter ausschließlich als Immobilienmakler vor.
"""

from __future__ import annotations

import re

from openai import OpenAI

# Modell mit Web-Search-Unterstützung. Bei Bedarf anpassen.
MODEL = "gpt-4o"

# Kern-Vorgabe (wörtlich wie gewünscht) …
BASE_PROMPT = (
    "Erstelle einen Text mit 300 Wörtern als Vorstellungstext dieses Maklers "
    "mit Informationen, die du im Internet finden kannst."
)

# … plus Format- und Inhaltsvorgaben.
FORMAT_RULES = (
    "Formatvorgaben:\n"
    "- Reiner, zusammenhängender Fließtext auf Deutsch.\n"
    "- KEIN Markdown, KEINE Überschriften, KEINE Aufzählungen.\n"
    "- KEINE Quellenangaben, Fußnoten, Zitate oder Links (auch keine URLs).\n"
    "- Möglichst genau 300 Wörter.\n"
    "- Sachlich-werblicher Vorstellungstext in der dritten Person.\n"
    "- Gib ausschließlich den Vorstellungstext aus, ohne Vor- oder Nachbemerkung.\n\n"
    "Inhaltsvorgaben:\n"
    "- Stelle den Anbieter AUSSCHLIESSLICH als Immobilienmakler vor.\n"
    "- Erwähne oder bewirb KEINE Finanzdienstleistungen, Finanz- oder "
    "Vermögensberatung, Baufinanzierung, Finanzierungen, Versicherungen, "
    "Kredite oder Bankprodukte des Anbieters — auch dann nicht, wenn er solche "
    "Leistungen tatsächlich anbietet.\n"
    "- Der Firmenname darf genannt werden; die genannten Geschäftsbereiche "
    "dürfen inhaltlich jedoch nicht thematisiert werden.\n"
    "- Fokus auf Immobilienvermittlung, Verkauf, Vermietung, Bewertung, "
    "regionale Marktkenntnis und Service rund um Immobilien."
)

# Begriffe, die auf unerwünschte Finanz-/Versicherungsinhalte hindeuten.
_FORBIDDEN = [
    "finanzberat", "finanzdienst", "baufinanz", "finanzierung", "versicher",
    "vermögensberat", "kreditberat", "bankprodukt", "geldanlage",
]


def _trim_to_sentence(text: str, target: int = 300, tol: int = 15) -> str:
    """Kürzt zu langen Text auf ~target Wörter an der letzten Satzgrenze."""
    words = text.split()
    if len(words) <= target + tol:
        return text
    cut = " ".join(words[: target + tol])
    m = list(re.finditer(r"[.!?](?=\s|$)", cut))
    if m:
        return cut[: m[-1].end()].strip()
    return cut.strip()


def _sanitize(text: str) -> str:
    """Entfernt etwaige Markdown-/Zitat-Reste als Sicherheitsnetz."""
    text = re.sub(r"\s*\(\[[^\]]+\]\([^)]*\)\)", "", text)       # Zitat-Cluster
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)          # [Text](url)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)    # Überschriften
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _has_forbidden(text: str, makler_name: str) -> bool:
    """Prüft auf Finanz-/Versicherungsbegriffe — ohne den Firmennamen selbst."""
    haystack = text.lower()
    if makler_name:
        haystack = haystack.replace(makler_name.lower(), " ")
    return any(term in haystack for term in _FORBIDDEN)


def generate_makler_text(
    openai_key: str, impressum: str, region: str = "", makler_name: str = ""
) -> str:
    """Erzeugt den Vorstellungstext. `impressum` dient der Identifikation."""
    client = OpenAI(api_key=openai_key)

    region_hint = f"\n\nRegion des Maklers: {region}" if region else ""

    # Identifikationsblock: immer mit Name, ergänzt durch Impressum wenn vorhanden.
    # So kann die AI den richtigen Makler finden, auch wenn das Impressum fehlt.
    if impressum:
        id_block = (
            f"Name des Maklers: {makler_name}\n\n"
            "Zur eindeutigen Identifikation das folgende Impressum seines "
            f"Anbieterprofils:\n\n{impressum}"
        ) if makler_name else (
            "Zur eindeutigen Identifikation des Maklers das folgende Impressum "
            f"seines Anbieterprofils:\n\n{impressum}"
        )
    else:
        id_block = (
            f"Name des Maklers: {makler_name}"
        ) if makler_name else ""

    prompt = (
        f"{BASE_PROMPT}\n\n{FORMAT_RULES}\n\n"
        f"{id_block}{region_hint}"
    )

    response = client.responses.create(
        model=MODEL, input=prompt, tools=[{"type": "web_search_preview"}]
    )
    text = _sanitize(response.output_text)

    # Sicherheitsnetz: enthält der Text doch Finanz-/Versicherungsinhalte,
    # einmalig neutral umschreiben (rein auf Immobilien fokussiert).
    if _has_forbidden(text, makler_name):
        rewrite = client.responses.create(
            model=MODEL,
            input=(
                "Schreibe den folgenden Vorstellungstext um. Entferne JEDE "
                "Erwähnung und Bewerbung von Finanzdienstleistungen, Finanz- "
                "oder Vermögensberatung, Baufinanzierung, Finanzierungen, "
                "Versicherungen, Krediten oder Bankprodukten vollständig. "
                "Stelle den Anbieter ausschließlich als Immobilienmakler dar "
                "(Vermittlung, Verkauf, Vermietung, Bewertung, regionale "
                "Marktkenntnis). Möglichst genau 300 Wörter, reiner Fließtext "
                "auf Deutsch, KEIN Markdown, KEINE Quellen/Links. Gib nur den "
                "Text aus.\n\n" + text
            ),
        )
        text = _sanitize(rewrite.output_text)

    # Das Modell unterschreitet die 300 Wörter oft; einmalig nachschärfen.
    if len(text.split()) < 285:
        followup = client.responses.create(
            model=MODEL,
            input=(
                "Erweitere den folgenden Vorstellungstext auf möglichst genau "
                "300 Wörter (mindestens 290). Behalte Inhalt, Stil und Sprache "
                "bei und führe KEINE Finanzdienstleistungen, Finanzierungen "
                "oder Versicherungen ein. Reiner Fließtext auf Deutsch, KEIN "
                "Markdown, KEINE Quellen/Links. Gib nur den Text aus.\n\n" + text
            ),
        )
        text = _sanitize(followup.output_text)

    return _trim_to_sentence(text)
