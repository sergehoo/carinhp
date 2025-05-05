console.log('📦 case-loader.js chargé');

import { map, markerCluster } from './map-init.js';
import { createMarkerIcon, createPopupContent, updateSummary, updateCaseList } from './case-ui.js';
import { toggleHeatIfActive } from './heatmap-module.js';
import { updateChart } from './chart-module.js';
import { downloadCSV } from './export-csv-module.js';

// Lancement immédiat
fetchAndUpdateCases();

export async function fetchAndUpdateCases() {
  const filters = collectFilters();
  const query = new URLSearchParams(filters).toString();
  showLoading(true);
  try {
    const res = await fetch(`/cartographie/?${query}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const all = [ ...data.pre_expositions, ...data.post_expositions, ...data.notifications ];
    window.latestFeatures = all;
    updateMap(all);
    updateSummary(all);
    updateCaseList(all);
    toggleHeatIfActive(all);
    updateChart(all);
  } catch (err) {
    console.error('Erreur de chargement :', err);
  } finally {
    showLoading(false);
  }
}

function collectFilters() {
  const keys = ['pole', 'region', 'district', 'type', 'gravite'];
  const f = {};
  keys.forEach(k => {
    const el = document.getElementById(`${k}-filter`);
    if (el && el.value && el.value !== 'all') f[k] = el.value;
  });
  const start = document.getElementById('start-date').value;
  const end = document.getElementById('end-date').value;
  if (start) f.start_date = start;
  if (end) f.end_date = end;
  return f;
}

function updateMap(features) {
  markerCluster.clearLayers();
  features.forEach(f => {
    const coords = f.geometry?.coordinates;
    if (!coords) return;
    const [lng, lat] = coords;
    const m = L.marker([lat, lng], { icon: createMarkerIcon(f.properties.type) });
    m.bindPopup(createPopupContent(f));
    markerCluster.addLayer(m);
  });
}

function showLoading(active) {
  document.getElementById('loading').style.display = active ? 'flex' : 'none';
}

document.getElementById('apply-filters')?.addEventListener('click', fetchAndUpdateCases);