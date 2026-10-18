"""Occurrences GBIF d'une espèce sur une emprise : API occurrence/search, cache disque.

Filtres (spec › Validation) : France, coordonnées présentes sans problème géospatial, précision
≤ `MAX_UNCERTAINTY_M`, datées. Jamais retéléchargé si le fichier de cache existe (`force`).
Licence des jeux : CC-BY / CC-BY-NC selon jeu, conservée par enregistrement.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx

from ..config import RAW_DIR

log = logging.getLogger(__name__)

API = "https://api.gbif.org/v1"
PAGE = 300
MAX_OFFSET = 100_000  # limite de l'API search ; au-delà il faudrait l'API download
MAX_UNCERTAINTY_M = 100
GBIF_DIR = RAW_DIR / "gbif"


@dataclass(frozen=True)
class Occurrence:
    lat: float
    lon: float
    date: str  # AAAA-MM-JJ (eventDate tronqué)
    uncertainty_m: float | None
    dataset: str
    license: str


def taxon_key(name_la: str, http: httpx.Client) -> int:
    """usageKey GBIF du nom latin (règne Fungi) ; erreur si aucune correspondance."""
    r = http.get(f"{API}/species/match", params={"name": name_la, "kingdom": "Fungi"})
    r.raise_for_status()
    body = r.json()
    if body.get("matchType") == "NONE" or "usageKey" not in body:
        raise ValueError(f"GBIF ne connaît pas « {name_la} » : {body.get('note')}")
    return int(body["usageKey"])


def occurrences(
    species_id: str,
    name_la: str,
    bbox_4326: tuple[float, float, float, float],
    http: httpx.Client,
    cache_dir: Path = GBIF_DIR,
    force: bool = False,
) -> list[Occurrence]:
    """Occurrences filtrées dans l'emprise (w, s, e, n), depuis le cache si présent."""
    w, s, e, n = bbox_4326
    cache = cache_dir / f"{species_id}_{w:.2f}_{s:.2f}_{e:.2f}_{n:.2f}.json"
    if cache.exists() and not force:
        rows = json.loads(cache.read_text(encoding="utf-8"))["occurrences"]
        return [Occurrence(**r) for r in rows]

    key = taxon_key(name_la, http)
    params: dict[str, Any] = {
        "taxonKey": key,
        "country": "FR",
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "coordinateUncertaintyInMeters": f"0,{MAX_UNCERTAINTY_M}",
        "decimalLatitude": f"{s},{n}",
        "decimalLongitude": f"{w},{e}",
        "limit": PAGE,
    }
    out: list[Occurrence] = []
    offset = 0
    while offset < MAX_OFFSET:
        r = http.get(f"{API}/occurrence/search", params={**params, "offset": offset})
        r.raise_for_status()
        body = r.json()
        for rec in body.get("results", []):
            o = _parse(rec)
            if o is not None:
                out.append(o)
        if body.get("endOfRecords", True):
            break
        offset += PAGE
    log.info("GBIF %s : %d occurrences datées et précises (taxonKey %d)", species_id, len(out), key)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "species": species_id,
                "taxon_key": key,
                "bbox": list(bbox_4326),
                "occurrences": [asdict(o) for o in out],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return out


def _parse(rec: dict[str, Any]) -> Occurrence | None:
    date = rec.get("eventDate")
    lat, lon = rec.get("decimalLatitude"), rec.get("decimalLongitude")
    if not date or lat is None or lon is None:
        return None
    return Occurrence(
        lat=float(lat),
        lon=float(lon),
        date=str(date)[:10],
        uncertainty_m=rec.get("coordinateUncertaintyInMeters"),
        dataset=str(rec.get("datasetKey", "")),
        license=str(rec.get("license", "")),
    )
