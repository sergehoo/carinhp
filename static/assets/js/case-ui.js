export function createMarkerIcon(type) {
  const mapIc = { pre: { icon:'fa-syringe', color:'green' }, post:{icon:'fa-bandaid', color:'darkgreen'}, notification:{icon:'fa-skull-crossbones', color:'red'}};
  const s = mapIc[type] || {icon:'fa-circle', color:'blue'};
  return L.AwesomeMarkers.icon({ icon: s.icon, prefix:'fa', markerColor: s.color, iconColor:'#fff' });
}

export function createPopupContent(f) {
  const p = f.properties;
  return `
    <strong>${p.patient}</strong><br>
    <i class='fas fa-calendar'></i> ${p.date}<br>
    <i class='fas fa-map-marker-alt'></i> ${p.commune || 'N/A'}<br>
    <i class='fas fa-biohazard'></i> Gravité: ${p.gravite || 'N/A'}<br>
    <a href="/admin/rage/${getAdminPath(p.type)}/${p.id}/change/" target="_blank" class="btn btn-sm btn-primary mt-2">Voir fiche</a>
  `;
}

function getAdminPath(type) {
  return {pre:'preexposition', post:'postexposition', notification:'ragehumanenotification'}[type] || '';
}

export function updateSummary(features) {
  const counts = {pre:0, post:0, notification:0};
  features.forEach(f => counts[f.properties.type]++);
  document.getElementById('pre-count').textContent = counts.pre;
  document.getElementById('post-count').textContent = counts.post;
  document.getElementById('notification-count').textContent = counts.notification;
}

export function updateCaseList(features) {
  const c = document.getElementById('incident-list-container');
  if (!c) return;
  c.innerHTML = '';
  features.sort((a,b)=>new Date(b.properties.date)-new Date(a.properties.date)).slice(0,50)
    .forEach(f=>{
      const p=f.properties;
      const card=document.createElement('div');
      card.className='incident-card p-2 mb-2 border-start border-3';
      card.style.borderColor={'pre':'#5D9C59','post':'#009A44','notification':'#DF7861'}[p.type];
      card.innerHTML=`<div class="d-flex justify-content-between"><strong>${p.type.toUpperCase()}</strong><small>${p.date}</small></div><div><i class="fas fa-map-marker-alt"></i> ${p.commune||'Non précisé'}</div>`;
      card.addEventListener('click',()=>map.flyTo([f.geometry.coordinates[1],f.geometry.coordinates[0]],15));
      c.appendChild(card);
    });
}