// ==========================
// ThreatIntelGPT Frontend JS
// ==========================

// ------- SECTION NAVIGATION -------
const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('section');

navItems.forEach(item => {
  item.addEventListener('click', () => {
    navItems.forEach(i => i.classList.remove('active'));
    item.classList.add('active');

    const target = item.getAttribute('data-section');
    sections.forEach(sec => {
      sec.style.display = sec.id === target ? 'block' : 'none';
    });
  });
});

// ------- STATUS HANDLER -------
function setStatus(msg, isError = false) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.style.color = isError ? '#f87171' : '#9ca3af';
}

// ------- PRESET FEED -------
const preset = document.getElementById('presetFeed');
preset.addEventListener('change', () => {
  if (preset.value) {
    document.getElementById('rss').value = preset.value;
  }
});

// ------- INGEST PIPELINE CALL -------
async function ingest() {
  const rss = document.getElementById('rss').value.trim();
  const count = parseInt(document.getElementById('count').value) || 3;

  if (!rss) return setStatus('Please enter a valid RSS URL.', true);

  setStatus('Processing feed... Running NLP pipeline...');

  try {
    const res = await fetch('/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rss_url: rss, max_items: count, save: true })
    });

    if (!res.ok) throw new Error('Failed to ingest feed.');

    const data = await res.json();
    setStatus(`Successfully processed ${data.count} items.`);
    loadReports();
  } catch (err) {
    setStatus('Error: ' + err.message, true);
  }
}

// ------- LOAD SAVED REPORTS -------
async function loadReports() {
  setStatus('Loading saved reports...');

  try {
    const res = await fetch('/reports');
    if (!res.ok) throw new Error('Failed to fetch reports');

    const data = await res.json();
    const box = document.getElementById('reports');
    box.innerHTML = '';

    if (!data.items.length) {
      box.innerHTML = '<p style="color:#9ca3af">No reports found. Run ingestion first.</p>';
      return setStatus('No reports available.');
    }

    data.items.forEach(r => {
      const card = document.createElement('div');
      card.className = 'report-card';
      card.innerHTML = `
        <h4>${r.title || '(Untitled report)'}</h4>
        <p><strong>Summary:</strong> ${r.summary || 'No summary available.'}</p>
        <a href="${r.link}" target="_blank" style="color:#38bdf8;">Open Source</a>
      `;
      box.appendChild(card);
    });

    setStatus('Reports loaded.');
  } catch (err) {
    setStatus('Error loading reports: ' + err.message, true);
  }
}

// Initial load
loadReports();