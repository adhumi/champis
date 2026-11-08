#!/usr/bin/env python3
"""Contrôle du référentiel hors fichiers espèces (ceux-là : species/validate.py).

Usage : python3 scripts/check_shared.py
Vérifie : chaque JSON se lit ; l'index des textes du Guide (shared/texts/index.json) et les
fichiers Markdown se correspondent un pour un, sans id en double ; chaque fichier de vecteurs
(shared/vectors/) porte `generated_by` (scoring_version, species_hash) et des cas, et tous la même
empreinte ; chaque espèce a son illustration shared/illustrations/<id>.svg, SVG bien formé au cadre
commun, listée dans shared/illustrations/index.json. Que les vecteurs soient à jour se vérifie dans
la CI de champis-api (`champis-vectors --check`), qui a le code du scoring ; que les illustrations
soient celles du générateur, par `scripts/draw_illustrations.py --check` (cible `make shared`).

Bibliothèque standard seulement : le référentiel n'a pas d'environnement Python.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXTS = ROOT / "shared" / "texts"
VECTORS = ROOT / "shared" / "vectors"
VECTOR_FILES = ("trapezoid", "phi", "m", "group", "palette")
SPECIES = ROOT / "species"
ILLUSTRATIONS = ROOT / "shared" / "illustrations"
SVG_NS = "{http://www.w3.org/2000/svg}"


def check() -> list[str]:
    errors: list[str] = []

    parsed: dict[Path, object] = {}
    for path in sorted(ROOT.glob("**/*.json")):
        if ".git" in path.parts:
            continue
        try:
            parsed[path] = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)} : JSON illisible ({exc})")

    index = parsed.get(TEXTS / "index.json")
    if not isinstance(index, dict) or not isinstance(index.get("articles"), list):
        errors.append("shared/texts/index.json : clé `articles` absente")
    else:
        ids = [a.get("id") for a in index["articles"]]
        files = [a.get("file") for a in index["articles"]]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            errors.append(f"shared/texts/index.json : id en double « {dup} »")
        for article in index["articles"]:
            for key in ("id", "title", "file"):
                if not article.get(key):
                    errors.append(f"shared/texts/index.json : article sans `{key}` ({article})")
            if article.get("file") and not (TEXTS / article["file"]).is_file():
                errors.append(f"shared/texts/index.json : fichier absent « {article['file']} »")
        for md in sorted(p.name for p in TEXTS.glob("*.md")):
            if md not in files:
                errors.append(f"shared/texts/{md} : absent de index.json")

    hashes = set()
    for name in VECTOR_FILES:
        data = parsed.get(VECTORS / f"{name}.json")
        if data is None:
            errors.append(f"shared/vectors/{name}.json : absent")
            continue
        gen = data.get("generated_by") if isinstance(data, dict) else None
        if not isinstance(gen, dict) or not gen.get("scoring_version") or not gen.get("species_hash"):
            errors.append(f"shared/vectors/{name}.json : `generated_by` incomplet")
        else:
            hashes.add((gen["scoring_version"], gen["species_hash"]))
        if not isinstance(data, dict) or not data.get("cases"):
            errors.append(f"shared/vectors/{name}.json : aucun cas")
    if len(hashes) > 1:
        errors.append(f"shared/vectors/ : empreintes différentes d'un fichier à l'autre {sorted(hashes)}")

    errors.extend(check_illustrations(parsed))
    return errors


def check_illustrations(parsed: dict[Path, object]) -> list[str]:
    """Une illustration par espèce, même cadre, index complet (décision du 8 nov. 2026)."""
    errors: list[str] = []
    species_ids = sorted(
        d["id"] for p, d in parsed.items() if p.parent == SPECIES and isinstance(d, dict) and d.get("id")
    )
    index = parsed.get(ILLUSTRATIONS / "index.json")
    if not isinstance(index, dict) or not isinstance(index.get("illustrations"), list):
        errors.append("shared/illustrations/index.json : clé `illustrations` absente")
        return errors
    if not index.get("license"):
        errors.append("shared/illustrations/index.json : `license` absente")
    listed = {e.get("species"): e.get("file") for e in index["illustrations"] if isinstance(e, dict)}
    view_boxes: set[str] = set()
    for sid in species_ids:
        svg = ILLUSTRATIONS / f"{sid}.svg"
        if not svg.is_file():
            errors.append(f"shared/illustrations/{sid}.svg : absent (python3 scripts/draw_illustrations.py)")
            continue
        if listed.get(sid) != svg.name:
            errors.append(f"shared/illustrations/index.json : « {sid} » absent ou mal nommé")
        try:
            root = ET.fromstring(svg.read_text(encoding="utf-8"))
        except ET.ParseError as exc:
            errors.append(f"shared/illustrations/{sid}.svg : SVG illisible ({exc})")
            continue
        if root.tag != f"{SVG_NS}svg":
            errors.append(f"shared/illustrations/{sid}.svg : racine {root.tag} au lieu de <svg>")
            continue
        view_boxes.add(root.get("viewBox", ""))
        if root.find(f"{SVG_NS}title") is None:
            errors.append(f"shared/illustrations/{sid}.svg : sans <title> (accessibilité)")
    for sid in listed:
        if sid not in species_ids:
            errors.append(f"shared/illustrations/index.json : « {sid} » n'est pas une espèce")
    for svg in sorted(ILLUSTRATIONS.glob("*.svg")):
        if svg.stem not in species_ids:
            errors.append(f"shared/illustrations/{svg.name} : aucune espèce de ce nom")
    expected = index.get("viewBox")
    if len(view_boxes) > 1 or (expected and view_boxes and view_boxes != {expected}):
        errors.append(f"shared/illustrations/ : cadres différents {sorted(view_boxes)} (attendu {expected})")
    return errors


def main() -> int:
    errors = check()
    for error in errors:
        print(f"ECHEC  {error}")
    if errors:
        return 1
    print("ok  JSON lisibles, index des textes, vecteurs, illustrations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
