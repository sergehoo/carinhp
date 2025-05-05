import {map} from './map-init.js';

let heatLayer;

export function renderHeatmap(features) {
    if (heatLayer) map.removeLayer(heatLayer);
    const data = features.map(f => [f.geometry.coordinates[1], f.geometry.coordinates[0], 1]);
    heatLayer = L.heatLayer(data, {radius: 25, blur: 15, maxZoom: 11}).addTo(map);
}

const btn = document.createElement('button');
btn.textContent = 'Activer Heatmap';
btn.className = 'btn btn-sm btn-outline-danger';
btn.style.position = 'absolute';
btn.style.top = '20px';
btn.style.right = '20px';
btn.style.zIndex = '1001';
document.body.appendChild(btn);
let active = false;
btn.addEventListener('click', () => {
    active = !active;
    btn.textContent = active ? 'Désactiver Heatmap' : 'Activer Heatmap';
    if (active) renderHeatmap(window.latestFeatures || []); else if (heatLayer) map.removeLayer(heatLayer);
});

export function toggleHeatIfActive(features) {
    if (active) renderHeatmap(features);
}