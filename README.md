# Champis

Où et quand cueillir des champignons en France, à l'échelle de la parcelle forestière. Outil personnel, gratuit, construit sur de l'open data (IGN BD Forêt V2, Copernicus DEM, SoilGrids, Open-Meteo) et sur la littérature mycologique.

Score d'un pixel de 25 m pour une espèce et un jour : `S = T × M × Φ` — potentiel terrain (statique, ce dépôt le calcule), indice météo (dynamique, API), fenêtre phénologique. Le modèle complet est dans `species/SCHEMA.md`.

## Phase 1 — faire tourner le pipeline sur le Doubs

Prérequis : Python 3.12+, [uv](https://docs.astral.sh/uv/), ~5 Go de disque pour un département. Pas de GDAL système à installer : rasterio embarque le sien.

```bash
uv sync --group dev
uv run pytest                      # 45 tests, dont une chaîne complète sur un département synthétique
uv run champis-pipeline all --dept 25
```

`all` enchaîne :

1. **download** — BD Forêt V2 du Doubs (31 Mo, flux Géoplateforme IGN), pH SoilGrids (WCS ISRIC, découpe sur l'emprise), dalles Copernicus DEM 30 m (bucket public AWS). Tout va dans `data/raw/`, rien n'est retéléchargé s'il est présent.
2. **grid** — rasters alignés 25 m Lambert-93 dans `data/grid/25/` : `host.tif` (essence dominante), `cover.tif`, `ph.tif`, `alt.tif`, `slope.tif`, `aspect.tif`.
3. **terrain** — `data/T/<espèce>/25-<hash>.tif`, un par espèce (7 au départ). Quelques secondes par espèce.
4. **tiles** — `data/tiles/T-<espèce>-<hash>-p1.0.0.pmtiles`, niveaux 6–15. Quelques minutes par espèce pour un département (z15 ≈ 7 000 tuiles).

Puis `uv run champis-pipeline summary --dept 25` donne la surface par classe (excellent → très faible) par espèce : premier regard sur la crédibilité avant toute carte.

Pour regarder le résultat sans attendre le site : ouvrir un PMTiles dans [pmtiles.io](https://pmtiles.io) (glisser-déposer) ; les tuiles sont des PNG gris, 0 = noir = T 0, 254 = blanc = T 1.

## Ce qui n'est pas encore là

- L'API (FastAPI) : `api/champis_api/scoring.py` contient déjà M et Φ, testés ; le service HTTP et le client Open-Meteo viennent en phase 2.
- La carte web jetable de la phase 1 (`web/`), qui lira les PMTiles et appellera Open-Meteo.
- Le contrôle GBIF et le recalibrage pH (`pipeline/check/`).
- Les pixels de contrôle du Doubs (`pipeline/tests/control_pixels.json`) : à fournir par un cueilleur qui connaît le terrain.

## Licences des données

BD Forêt V2 © IGN, Licence Ouverte 2.0 · Copernicus DEM © ESA/Airbus · SoilGrids © ISRIC, CC-BY 4.0 · Weather data by Open-Meteo.com, CC-BY 4.0 · Observations GBIF, CC-BY / CC-BY-NC selon jeu.
