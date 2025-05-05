export let map;
export let markerCluster;

export function initMap() {
    console.log("✅ initMap() démarre");
    map = L.map('map').setView([7.54, -5.55], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    markerCluster = L.markerClusterGroup({
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 80
    }).addTo(map);
}

// Auto-exécution
initMap();