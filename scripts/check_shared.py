#!/usr/bin/env python3
"""Contrôle du référentiel hors fichiers espèces (ceux-là : species/validate.py).

Usage : python3 scripts/check_shared.py
Vérifie : chaque JSON se lit ; l'index des textes du Guide (shared/texts/index.json) et les
fichiers Markdown se correspondent un pour un, sans id en double ; chaque illustration
(shared/illustrations/<id>.jpg) porte l'id d'une espèce ; chaque fichier de vecteurs
(shared/vectors/) porte `generated_by` (scoring_version, species_hash) et des cas, et tous la même
empreinte. Que les vecteurs soient à jour se vérifie dans la CI de champis-api
(`champis-vectors --check`), qui a le code du scoring.

Bibliothèque standard seulement : le référentiel n'a pas d'environnement Python.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXTS = ROOT / "shared" / "texts"
VECTORS = ROOT / "shared" / "vectors"
VECTOR_FILES = ("trapezoid", "phi", "m", "group", "palette", "interp")
SPECIES = ROOT / "species"
ILLUSTRATIONS = ROOT / "shared" / "illustrations"


NOTES: list[str] = []  # constats sans échec (planche absente : espèce incomplète)


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

    # illustrations (shared/illustrations/README.md) : une <id>.jpg par fichier espèce, rien d'autre.
    # Une planche absente n'est pas une erreur (décision d'Adrien du 9 nov. 2026) : l'espèce est
    # incomplète et l'API ne la sert pas au site ni à l'app tant que la planche manque ; on le dit
    species_ids = {p.stem for p in SPECIES.glob("*.json")}
    for sid in sorted(species_ids):
        if not (ILLUSTRATIONS / f"{sid}.jpg").is_file():
            NOTES.append(f"shared/illustrations/{sid}.jpg : absente, espèce incomplète, non servie par /species")
    for image in sorted(ILLUSTRATIONS.glob("*.*")):
        if image.suffix == ".md":
            continue
        if image.suffix != ".jpg":
            errors.append(f"shared/illustrations/{image.name} : format inattendu (attendu <id>.jpg)")
        elif image.stem not in species_ids:
            errors.append(f"shared/illustrations/{image.name} : aucune espèce de ce nom")

    return errors


def main() -> int:
    errors = check()
    for note in NOTES:
        print(f"note   {note}")
    for error in errors:
        print(f"ECHEC  {error}")
    if errors:
        return 1
    print("ok  JSON lisibles, index des textes, vecteurs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
