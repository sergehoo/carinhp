const btn = document.createElement('button');
btn.textContent = 'Exporter CSV';
btn.className = 'btn btn-sm btn-success';
Object.assign(btn.style, {position: 'absolute', top: '60px', right: '20px', zIndex: 1001});
document.body.appendChild(btn);

export function downloadCSV(features) {
    const rows = [['ID', 'Patient', 'Date', 'Commune', 'Type', 'Gravité', 'Région']];
    features.forEach(f => rows.push([f.properties.id, f.properties.patient, f.properties.date, f.properties.commune || '', f.properties.type, f.properties.gravite || '', f.properties.region || '']));
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], {type: 'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cas_rage_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

btn.addEventListener('click', () => window.latestFeatures ? downloadCSV(window.latestFeatures) : alert('Aucune donnée à exporter.'));