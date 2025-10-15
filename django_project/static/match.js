// CSRF for Django
function getCookie(name){
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? m.pop() : '';
}
const headers = {'Content-Type':'application/json'};
const csrftoken = getCookie('csrftoken');
if (csrftoken) headers['X-CSRFToken'] = csrftoken;

// Load existing events into the select
async function loadEvents(){
  const r = await fetch('/api/events/');
  const data = await r.json();
  const sel = document.getElementById('event-select');
  sel.innerHTML = '';
  data.events.forEach(e=>{
    const opt = document.createElement('option');
    opt.value = e.id;
    opt.textContent = `${e.id} — ${e.title}`;
    sel.appendChild(opt);
  });
}
loadEvents();

// Render matches
function renderMatches(payload){
  const box = document.getElementById('matches');
  const rows = (payload.matches || []).map(m=>{
    const v = m.volunteer;
    const skills = Array.from(v.skills || []);
    return `<li><b>${v.name}</b> | score=${m.score} | skills=[${skills.join(', ')}]</li>`;
  }).join('');
  box.innerHTML = rows ? `<ul>${rows}</ul>` : '<i>No matches</i>';
}

// Match existing event by id
document.getElementById('match-existing').addEventListener('click', async ()=>{
  const id = document.getElementById('event-select').value;
  if(!id) return;
  const r = await fetch('/api/match/', {method:'POST', headers, body: JSON.stringify({event_id: Number(id)})});
  const payload = await r.json();
  if(!r.ok){ alert('Match error'); return; }
  renderMatches(payload);
});

// Convert form to JSON the way backend expects
function formToObject(form){
  const fd = new FormData(form);
  const obj = {};
  for (const [k,v] of fd.entries()){
    if (obj[k] !== undefined){
      if (!Array.isArray(obj[k])) obj[k] = [obj[k]];
      obj[k].push(v);
    } else obj[k] = v;
  }
  ['id','slots','max_radius_miles'].forEach(k=>{ if (k in obj) obj[k] = Number(obj[k]); });
  ['required_skills','languages','time_blocks','requires'].forEach(k=>{
    if (obj[k] === undefined) obj[k] = [];
    if (!Array.isArray(obj[k])) obj[k] = [obj[k]];
  });
  return obj;
}

// Validate then match new event
document.getElementById('event-form').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const data = formToObject(e.target);

  const vr = await fetch('/api/validate/event/', {method:'POST', headers, body: JSON.stringify(data)});
  if(!vr.ok){
    const err = await vr.json();
    alert('Validation errors:\n' + JSON.stringify(err.errors));
    return;
  }
  const mr = await fetch('/api/match/', {method:'POST', headers, body: JSON.stringify(data)});
  const payload = await mr.json();
  if(!mr.ok){ alert('Match error'); return; }
  renderMatches(payload);
});
