#!/usr/bin/env python3
"""Validation des fichiers espèces et de la table BD Forêt.

Usage : python3 validate.py
Vérifie : JSON valide, clés obligatoires, plages trapézoïdales ordonnées,
poids sommant à 1, hôtes ⊂ vocabulaire, refs ⊂ references, 32 codes TFV couverts,
gel en rampe (`ramp_c` > 0),
bloc `about` (fiche en mots : confusions sourcées, photo libre créditée ou null).
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
# Licences acceptées pour la photo d'une fiche (Wikimedia Commons) : libres, attribution affichée.
PHOTO_LICENSES = {
    "CC0",
    "Public domain",
    "CC BY 2.0",
    "CC BY 3.0",
    "CC BY 4.0",
    "CC BY-SA 2.0",
    "CC BY-SA 2.5",
    "CC BY-SA 3.0",
    "CC BY-SA 4.0",
}

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


def _md_days(md: str) -> int:
    """Jour de l'année (année non bissextile) d'un `MM-DD` ; lève si la date n'existe pas."""
    m, d = (int(x) for x in md.split("-"))
    lengths = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not (1 <= m <= 12 and 1 <= d <= (29 if m == 2 else lengths[m - 1])):
        raise ValueError(md)
    return sum(lengths[: m - 1]) + min(d, lengths[m - 1])


def check_season(name: str, season: dict, peak: dict) -> None:
    """`season.start < season.end` dans l'année civile ; sinon la saison passe le 1er janvier et
    tout se mesure en jours depuis `season.start`, modulo 365 : le pic doit y tenir, dans l'ordre."""
    try:
        s0 = _md_days(season["start"])
        rel = {k: (_md_days(v) - s0) % 365 for k, v in (("end", season["end"]), ("ps", peak["start"]), ("pe", peak["end"]))}
    except (ValueError, KeyError, AttributeError) as exc:
        err(f"{name}: date MM-DD invalide dans phenology ({exc})")
        return
    if rel["end"] == 0:
        err(f"{name}: phenology.season start = end")
    if not rel["ps"] <= rel["pe"] <= rel["end"]:
        err(f"{name}: pic hors saison ou pic inversé (en jours depuis season.start)")


def check_weights(name: str, w: dict, expected: set, optional: set = frozenset()) -> None:
    """Clés attendues exactes, plus des clés optionnelles (facteurs optionnels, spec › Scoring ›
    Facteurs de sol et de paysage, 9 nov. 2026 : absent = poids 0) ; la somme reste 1."""
    if not expected <= set(w) <= expected | optional:
        err(f"{name}: clés {sorted(w)} ≠ attendues {sorted(expected)} (+ {sorted(optional)} optionnelles)")
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


def check_about(n: str, about: dict, refs_known: set) -> None:
    """Fiche en mots (lot 4) : résumé, habitat, saison, confusions sourcées, photo créditée ou null."""
    for k in ("summary", "habitat", "season", "confusions", "photo", "refs", "references"):
        if k not in about:
            err(f"{n}: about.{k} manquant")
    # la fiche est autoporteuse : ses sources vivent dans about.references, hors de l'empreinte
    refs_known = refs_known | set(about.get("references") or {})
    for k in ("summary", "habitat", "season"):
        if not isinstance(about.get(k), str) or len(about[k]) < 20:
            err(f"{n}: about.{k} trop court ou absent")
    confusions = about.get("confusions") or []
    if not confusions:
        err(f"{n}: about.confusions vide : au moins une confusion dangereuse")
    for i, c in enumerate(confusions):
        for k in ("name", "latin", "risk", "tell", "refs"):
            if not c.get(k):
                err(f"{n}: about.confusions[{i}].{k} manquant")
        for r in c.get("refs") or []:
            if r not in refs_known:
                err(f"{n}: about.confusions[{i}].refs → '{r}' absent de references")
    for r in about.get("refs") or []:
        if r not in refs_known:
            err(f"{n}: about.refs → '{r}' absent de references")
    photo = about.get("photo")
    if photo is not None:
        for k in ("url", "page", "author", "license"):
            if not photo.get(k):
                err(f"{n}: about.photo.{k} manquant")
        if photo.get("license") not in PHOTO_LICENSES:
            err(f"{n}: about.photo.license '{photo.get('license')}' hors licences libres acceptées")
        for k in ("url", "page"):
            if not str(photo.get(k, "")).startswith("https://"):
                err(f"{n}: about.photo.{k} doit être une URL https")


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
        # Une saison dont la fin précède le début passe le 1er janvier (décision d'Adrien du
        # 9 nov. 2026) : les bornes se comparent en jours depuis le début de saison, modulo l'année
        check_season(n, p["season"], p["peak"])
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
        # gel en rampe (spec › Scoring › gel en rampe, 4 nov. 2026) : sévérité linéaire sur
        # [tmin_c, tmin_c + ramp_c], cumulée sur la fenêtre et rapportée à `nights`
        fr = w["frost"]
        for k in ("tmin_c", "nights", "window_days", "factor", "ramp_c"):
            if k not in fr:
                err(f"{n}: weather.frost.{k} manquant")
        ramp = fr.get("ramp_c")
        if not isinstance(ramp, (int, float)) or isinstance(ramp, bool) or not ramp > 0:
            err(f"{n}: weather.frost.ramp_c doit être un nombre > 0, pas {ramp!r}")
        if not (isinstance(fr.get("nights"), int) and fr["nights"] >= 1):
            err(f"{n}: weather.frost.nights doit être un entier ≥ 1")
        if not 0 <= w["memory"]["floor"] <= 1:
            err(f"{n}: memory.floor hors [0,1]")
        if w["persistence"]["days"] < 0:
            err(f"{n}: persistence négative")
        check_weights(
            f"{n}.weather.weights",
            w["weights"],
            {"temp", "rain", "trigger", "soil_moisture"},
            optional={"soil_temp"},
        )
        # température du sol 0–7 cm (facteur optionnel, 9 nov. 2026) : bloc et poids vont ensemble
        st = w.get("soil_temp")
        st_w = w["weights"].get("soil_temp", 0)
        if st is not None:
            check_trapezoid(f"{n}.weather.soil_temp.c", st.get("c", {}))
            wd = st.get("window_days")
            if not (isinstance(wd, int) and not isinstance(wd, bool) and wd >= 1):
                err(f"{n}: weather.soil_temp.window_days doit être un entier ≥ 1, pas {wd!r}")
        elif st_w > 0:
            err(f"{n}: weights.soil_temp = {st_w} sans bloc weather.soil_temp")
        for block, rl in w.get("refs", {}).items():
            for r in rl:
                if r not in refs_known:
                    err(f"{n}: weather.refs.{block} → '{r}' absent")

        if "about" in sp:
            check_about(n, sp["about"], refs_known)
        else:
            err(f"{n}: bloc 'about' manquant (fiche de l'onglet Comprendre, lot 4)")

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
