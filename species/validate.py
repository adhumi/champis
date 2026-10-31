#!/usr/bin/env python3
"""Validation des fichiers espèces et de la table BD Forêt.

Usage : python3 validate.py
Vérifie : JSON valide, clés obligatoires, plages trapézoïdales ordonnées,
poids sommant à 1, hôtes ⊂ vocabulaire, refs ⊂ references, 32 codes TFV couverts.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECIES_DIR = ROOT / "species"
MAPPING = ROOT / "mapping" / "bdforet_to_hosts.json"

TFV_CODES = [
    "FF0",
    "FF1-00",
    "FF1G01-01",
    "FF1G06-06",
    "FF1-09-09",
    "FF1-10-10",
    "FF1-14-14",
    "FF1-49-49",
    "FF1-00-00",
    "FF2-00",
    "FF2-51-51",
    "FF2-52-52",
    "FF2G53-53",
    "FF2-57-57",
    "FF2G58-58",
    "FF2-81-81",
    "FF2-80-80",
    "FF2G61-61",
    "FF2-63-63",
    "FF2-64-64",
    "FF2-91-91",
    "FF2-90-90",
    "FF2-00-00",
    "FF31",
    "FF32",
    "FO0",
    "FO1",
    "FO2",
    "FO3",
    "FP",
    "LA4",
    "LA6",
]
ASPECTS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW", "flat"}

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def check_trapezoid(name: str, t: dict) -> None:
    keys = ["min", "opt_low", "opt_high", "max"]
    if any(k not in t for k in keys):
        err(f"{name}: clés manquantes {keys}")
        return
    v = [t[k] for k in keys]
    if not (v[0] <= v[1] <= v[2] <= v[3]):
        err(f"{name}: ordre min ≤ opt_low ≤ opt_high ≤ max violé : {v}")
    if v[1] == v[0] and v[0] != 0:
        pass  # rampe nulle autorisée (ex. pente dès 0)


def check_weights(name: str, w: dict, expected: set) -> None:
    if set(w) != expected:
        err(f"{name}: clés {sorted(w)} ≠ attendues {sorted(expected)}")
    s = sum(w.values())
    if abs(s - 1.0) > 1e-6:
        err(f"{name}: somme des poids = {s:.3f} ≠ 1")
    if any(x < 0 for x in w.values()):
        err(f"{name}: poids négatif")


def check_unit(name: str, d: dict, allowed: set | None = None) -> None:
    for k, v in d.items():
        if not isinstance(v, (int, float)) or not 0 <= v <= 1:
            err(f"{name}.{k}: valeur {v!r} hors [0,1]")
        if allowed is not None and k not in allowed:
            err(f"{name}.{k}: clé inconnue")


def main() -> int:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    vocab = set(mapping["hosts"]) | {"default"}
    covers = set(mapping["covers"])

    missing = [c for c in TFV_CODES if c not in mapping["bdforet_v2"]]
    extra = [c for c in mapping["bdforet_v2"] if c not in TFV_CODES]
    if missing:
        err(f"mapping: codes TFV manquants {missing}")
    if extra:
        err(f"mapping: codes TFV inconnus {extra}")
    for code, row in mapping["bdforet_v2"].items():
        if row["host"] not in vocab:
            err(f"mapping[{code}].host '{row['host']}' hors vocabulaire")
        if row["cover"] not in covers:
            err(f"mapping[{code}].cover '{row['cover']}' hors covers")
    for code, row in mapping["clc_2018_fallback"].items():
        if code == "description":
            continue
        if code == "default" and row["host"] != "herbacee":
            err("clc.default doit être 'herbacee' (hors forêt → T = 0)")
        if row["host"] not in vocab or row["cover"] not in covers:
            err(f"clc[{code}] hôte ou couvert inconnu")

    files = sorted(SPECIES_DIR.glob("*.json"))
    for f in files:
        sp = json.loads(f.read_text(encoding="utf-8"))
        n = f.stem
        if sp.get("id") != n:
            err(f"{n}: id '{sp.get('id')}' ≠ nom de fichier")
        for k in (
            "schema_version",
            "group",
            "names",
            "terrain",
            "phenology",
            "weather",
            "references",
        ):
            if k not in sp:
                err(f"{n}: section '{k}' manquante")
        refs_known = set(sp.get("references", {}))

        t = sp["terrain"]
        check_unit(f"{n}.terrain.hosts", t["hosts"], vocab)
        if "default" not in t["hosts"]:
            err(f"{n}: hosts.default manquant")
        for h in vocab - {"default"}:
            if h not in t["hosts"]:
                err(f"{n}: hôte '{h}' non pondéré (default s'appliquera)")
        check_unit(f"{n}.terrain.cover", t["cover"], covers)
        if set(t["cover"]) != covers:
            err(f"{n}: cover incomplet {sorted(covers - set(t['cover']))}")
        check_trapezoid(f"{n}.terrain.ph", t["ph"])
        check_trapezoid(f"{n}.terrain.altitude_m", t["altitude_m"])
        check_trapezoid(f"{n}.terrain.slope_deg", t["slope_deg"])
        check_unit(f"{n}.terrain.aspect", t["aspect"], ASPECTS)
        if set(t["aspect"]) != ASPECTS:
            err(f"{n}: aspect incomplet")
        check_weights(
            f"{n}.terrain.weights", t["weights"], {"cover", "ph", "altitude", "aspect", "slope"}
        )
        for block, rl in t.get("refs", {}).items():
            for r in rl:
                if r not in refs_known:
                    err(f"{n}: terrain.refs.{block} → '{r}' absent de references")

        p = sp["phenology"]
        for k in ("season", "peak"):
            s, e = p[k]["start"], p[k]["end"]
            if not (s < e):
                err(f"{n}: phenology.{k} start ≥ end")
        if not (
            p["season"]["start"] <= p["peak"]["start"] <= p["peak"]["end"] <= p["season"]["end"]
        ):
            err(f"{n}: pic hors saison")
        for r in p.get("refs", []):
            if r not in refs_known:
                err(f"{n}: phenology.refs → '{r}' absent")

        w = sp["weather"]
        check_trapezoid(f"{n}.weather.temp_mean.c", w["temp_mean"]["c"])
        check_trapezoid(f"{n}.weather.rain.mm", w["rain"]["mm"])
        check_trapezoid(f"{n}.weather.trigger.lag_days", w["trigger"]["lag_days"])
        check_trapezoid(f"{n}.weather.soil_moisture_pct", w["soil_moisture_pct"])
        wb = w["water_balance"]
        if not (wb["severe_mm"] < wb["moderate_mm"] < 0):
            err(f"{n}: water_balance seuils incohérents")
        if not (0 <= wb["severe_factor"] <= wb["moderate_factor"] <= 1):
            err(f"{n}: water_balance facteurs incohérents")
        sh = p["altitude_shift"]
        for k in ("reference_m", "start_days_per_100m", "end_days_per_100m", "max_days"):
            if k not in sh:
                err(f"{n}: altitude_shift.{k} manquant")
        check_trapezoid(f"{n}.weather.memory.mm", w["memory"]["mm"])
        for k in ("frost", "heat"):
            if not 0 <= w[k]["factor"] <= 1:
                err(f"{n}: weather.{k}.factor hors [0,1]")
        if not 0 <= w["memory"]["floor"] <= 1:
            err(f"{n}: memory.floor hors [0,1]")
        if w["persistence"]["days"] < 0:
            err(f"{n}: persistence négative")
        check_weights(
            f"{n}.weather.weights", w["weights"], {"temp", "rain", "trigger", "soil_moisture"}
        )
        for block, rl in w.get("refs", {}).items():
            for r in rl:
                if r not in refs_known:
                    err(f"{n}: weather.refs.{block} → '{r}' absent")

        print(f"ok  {n}: {len(t['hosts'])} hôtes, {len(refs_known)} références")

    if errors:
        print("\nECHEC :")
        for e in errors:
            print(" -", e)
        return 1
    print(f"\nok  {len(files)} fichiers espèces, {len(mapping['bdforet_v2'])} codes TFV")
    return 0


if __name__ == "__main__":
    sys.exit(main())
