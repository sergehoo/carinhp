// Utilisation du Chart global chargé via <script>
Chart.register(...Chart.registerables);
let chart;
const canvas = document.createElement('canvas');
Object.assign(canvas.style, {
    position: 'absolute', bottom: '20px', right: '20px', width: '300px', height: '150px', zIndex: 1001,
    background: '#fff', borderRadius: '5px', boxShadow: '0 0 5px rgba(0,0,0,0.2)'
});
document.body.appendChild(canvas);

export function updateChart(features) {
    const counts = {};
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(now.getDate() - i);
        counts[d.toISOString().split('T')[0]] = 0;
    }
    features.forEach(f => {
        const date = (f.properties.date || '').split('T')[0];
        if (counts[date] !== undefined) counts[date]++;
    });

    const labels = Object.keys(counts);
    const values = Object.values(counts);

    if (chart) chart.destroy();
    chart = new Chart(canvas, {
        type: 'line',
        data: {labels, datasets: [{label: 'Cas sur 30 jours', data: values, fill: true, tension: 0.3}]},
        options: {
            scales: {x: {display: false}, y: {beginAtZero: true, ticks: {precision: 0}}},
            plugins: {legend: {display: false}}, responsive: true, maintainAspectRatio: false
        }
    });
}