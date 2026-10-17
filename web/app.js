/* Carte jetable de la phase 1 : affiche le potentiel terrain T (PMTiles gris 8 bits) colorisé
 * côté client avec shared/palette.json. Aucune valeur de modèle ici : palette, seuils, encodage
 * des tuiles et noms d'espèces sont lus depuis le dépôt (servir la racine du dépôt, voir README). */

const TILE = 256;
const MIN_ZOOM = 6;
const MAX_ZOOM = 15;

const BASEMAPS = {
  plan: {
    tiles: [
      "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0" +
        "&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM" +
        "&FORMAT=image/png&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
    ],
    attribution: "© IGN — Plan IGN",
    maxzoom: 19,
  },
  ortho: {
    tiles: [
      "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0" +
        "&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM" +
        "&FORMAT=image/jpeg&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
    ],
    attribution: "© IGN — Orthophotos",
    maxzoom: 19,
  },
  osm: {
    tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
    attribution: "© OpenStreetMap contributors",
    maxzoom: 19,
  },
};

const $ = (id) => document.getElementById(id);

let palette; // shared/palette.json
let classes; // seuils triés décroissants avec rgb pré-parsé
const species = new Map(); // id → { pm, names, group }
let currentKey = null; // "s:<id>" ou "g:<group>"
const transparentTile = makeTransparentTile();

// ---------------------------------------------------------------- palette

async function loadPalette() {
  const r = await fetch("../shared/palette.json");
  if (!r.ok) throw new Error("palette.json introuvable : servir la racine du dépôt");
  palette = await r.json();
  classes = [...palette.thresholds]
    .sort((a, b) => b.min - a.min)
    .map((t) => ({ ...t, rgb: hexToRgb(t.hex) }));
  const legend = $("legend");
  legend.innerHTML = "";
  for (const c of [...classes].reverse()) {
    legend.insertAdjacentHTML(
      "beforeend",
      `<i style="background:${c.hex}"></i><span>${c.fr} (≥ ${c.min.toFixed(2)})</span>`
    );
  }
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1, 7), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function classify(t) {
  return classes.find((c) => t >= c.min) ?? classes[classes.length - 1];
}

// ---------------------------------------------------------------- tuiles

function makeTransparentTile() {
  const c = new OffscreenCanvas(TILE, TILE);
  c.getContext("2d");
  return c.convertToBlob({ type: "image/png" }).then((b) => b.arrayBuffer());
}

/** PNG gris+alpha → Float32Array de T (NaN = nodata). */
async function decodeT(buf) {
  const bmp = await createImageBitmap(new Blob([buf], { type: "image/png" }));
  const c = new OffscreenCanvas(TILE, TILE);
  const ctx = c.getContext("2d");
  ctx.drawImage(bmp, 0, 0);
  const px = ctx.getImageData(0, 0, TILE, TILE).data;
  const { scale, nodata } = palette.tile_encoding;
  const out = new Float32Array(TILE * TILE);
  for (let i = 0; i < out.length; i++) {
    const v = px[i * 4];
    out[i] = px[i * 4 + 3] === 0 || v === nodata ? NaN : v / scale;
  }
  return out;
}

function layerSpecies(key) {
  const [kind, name] = key.split(":");
  if (kind === "s") return [species.get(name)].filter(Boolean);
  return [...species.values()].filter((s) => s.group?.id === name);
}

/** T d'une couche sur une tuile : une espèce, ou max des espèces du groupe (règle 9 du modèle). */
async function layerT(key, z, x, y) {
  const arrays = [];
  for (const s of layerSpecies(key)) {
    const t = await s.pm.getZxy(z, x, y);
    if (t?.data) arrays.push(await decodeT(t.data));
  }
  if (arrays.length === 0) return null;
  const out = arrays[0];
  for (let k = 1; k < arrays.length; k++) {
    const a = arrays[k];
    for (let i = 0; i < out.length; i++) {
      if (Number.isNaN(out[i]) || a[i] > out[i]) out[i] = a[i];
    }
  }
  return out;
}

async function colorize(t) {
  const c = new OffscreenCanvas(TILE, TILE);
  const ctx = c.getContext("2d");
  const img = ctx.createImageData(TILE, TILE);
  for (let i = 0; i < t.length; i++) {
    if (Number.isNaN(t[i])) continue;
    const [r, g, b] = classify(t[i]).rgb;
    img.data.set([r, g, b, 255], i * 4);
  }
  ctx.putImageData(img, 0, 0);
  return (await c.convertToBlob({ type: "image/png" })).arrayBuffer();
}

maplibregl.addProtocol("champis", async (params) => {
  const m = params.url.match(/^champis:\/\/([^/]+)\/(\d+)\/(\d+)\/(\d+)$/);
  if (!m) throw new Error(`URL invalide : ${params.url}`);
  const t = await layerT(m[1], +m[2], +m[3], +m[4]);
  return { data: t ? await colorize(t) : await transparentTile };
});

// ---------------------------------------------------------------- carte

const map = new maplibregl.Map({
  container: "map",
  style: { version: 8, sources: {}, layers: [] },
  center: [6.35, 47.1], // Doubs
  zoom: 9,
  hash: true,
  attributionControl: { compact: false },
});
map.addControl(new maplibregl.NavigationControl(), "top-right");
map.addControl(new maplibregl.ScaleControl(), "bottom-right");

function setBasemap(name) {
  if (map.getLayer("basemap")) map.removeLayer("basemap");
  if (map.getSource("basemap")) map.removeSource("basemap");
  map.addSource("basemap", { type: "raster", tileSize: TILE, ...BASEMAPS[name] });
  map.addLayer({ id: "basemap", type: "raster", source: "basemap" }, map.getLayer("T") ? "T" : undefined);
}

function setLayer(key) {
  currentKey = key;
  if (map.getLayer("T")) map.removeLayer("T");
  if (map.getSource("T")) map.removeSource("T");
  if (!key) return;
  map.addSource("T", {
    type: "raster",
    tiles: [`champis://${key}/{z}/{x}/{y}`],
    tileSize: TILE,
    minzoom: MIN_ZOOM,
    maxzoom: MAX_ZOOM,
  });
  map.addLayer({
    id: "T",
    type: "raster",
    source: "T",
    paint: { "raster-opacity": +$("opacity").value, "raster-resampling": "nearest" },
  });
}

map.on("load", () => {
  setBasemap($("basemap").value);
  loadPalette().then(loadFromQuery).catch((e) => ($("status").textContent = e.message));
});

$("basemap").addEventListener("change", (e) => setBasemap(e.target.value));
$("opacity").addEventListener("input", (e) => {
  if (map.getLayer("T")) map.setPaintProperty("T", "raster-opacity", +e.target.value);
});
$("layer").addEventListener("change", (e) => setLayer(e.target.value));

// ---------------------------------------------------------------- chargement des PMTiles

async function addSource(src, label) {
  const id = label.match(/(?:^|\/)T-([a-z_]+)-/)?.[1];
  if (!id) throw new Error(`Nom inattendu (T-<espèce>-…pmtiles) : ${label}`);
  const pm = new pmtiles.PMTiles(src);
  const header = await pm.getHeader();
  const meta = await fetch(`../species/${id}.json`).then((r) => (r.ok ? r.json() : null));
  species.set(id, {
    pm,
    names: meta?.names ?? { fr: id, la: "" },
    group: meta?.group ?? null,
    bounds: [header.minLon, header.minLat, header.maxLon, header.maxLat],
  });
  return id;
}

async function addMany(items) {
  const first = species.size === 0;
  const errors = [];
  for (const { src, label } of items) {
    try {
      await addSource(src, label);
    } catch (e) {
      errors.push(e.message);
    }
  }
  refreshLayerList();
  if (first && species.size > 0) {
    const b = [...species.values()][0].bounds;
    map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 20, duration: 0 });
  }
  $("status").textContent = [
    `${species.size} espèce(s) : ${[...species.values()].map((s) => s.names.fr).join(", ")}`,
    ...errors,
  ].join("\n");
}

function refreshLayerList() {
  const sel = $("layer");
  sel.innerHTML = "";
  const groups = new Map();
  for (const s of species.values()) if (s.group) groups.set(s.group.id, s.group.fr);
  for (const [gid, fr] of groups) {
    sel.add(new Option(`${fr} — max du groupe`, `g:${gid}`));
  }
  for (const [id, s] of [...species].sort((a, b) => a[1].names.fr.localeCompare(b[1].names.fr))) {
    sel.add(new Option(`${s.names.fr} (${s.names.la})`, `s:${id}`));
  }
  sel.disabled = species.size === 0;
  if (species.size > 0 && (!currentKey || ![...sel.options].some((o) => o.value === currentKey))) {
    sel.value = sel.options[0].value;
    setLayer(sel.value);
  }
}

function loadFromQuery() {
  const q = new URLSearchParams(location.search).get("tiles");
  if (!q) return;
  return addMany(q.split(",").map((u) => ({ src: u, label: u })));
}

const drop = $("drop");
drop.addEventListener("click", () => $("files").click());
$("files").addEventListener("change", (e) => addFiles(e.target.files));
drop.addEventListener("dragover", (e) => {
  e.preventDefault();
  drop.classList.add("over");
});
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  drop.classList.remove("over");
  addFiles(e.dataTransfer.files);
});

function addFiles(files) {
  return addMany(
    [...files].map((f) => ({ src: new pmtiles.FileSource(f), label: f.name }))
  );
}

// ---------------------------------------------------------------- sonde au clic

const probe = $("probe");
map.on("click", async (e) => {
  if (!currentKey) return;
  const z = MAX_ZOOM;
  const n = TILE * 2 ** z;
  const lat = (e.lngLat.lat * Math.PI) / 180;
  const px = ((e.lngLat.lng + 180) / 360) * n;
  const py = ((1 - Math.log(Math.tan(lat) + 1 / Math.cos(lat)) / Math.PI) / 2) * n;
  const tx = Math.floor(px / TILE);
  const ty = Math.floor(py / TILE);
  const t = await layerT(currentKey, z, tx, ty);
  const v = t ? t[Math.floor(py % TILE) * TILE + Math.floor(px % TILE)] : NaN;
  probe.style.display = "block";
  if (Number.isNaN(v)) {
    probe.textContent = "Hors forêt / pas de donnée";
  } else {
    probe.textContent = `T = ${v.toFixed(3)} — ${classify(v).fr}`;
  }
});
