document.addEventListener('DOMContentLoaded', () => {
  // --------- NAVIGATION (SIDEBAR TABS) ----------
  const navItems = document.querySelectorAll('.nav-item');
  const sections = {
    overview: document.getElementById('section-overview'),
    cve: document.getElementById('section-cve'),
    voice: document.getElementById('section-voice'),
    settings: document.getElementById('section-settings')
  };

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const sectionKey = item.getAttribute('data-section');
      if (!sectionKey) return;

      // Set active nav
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      // Show selected section
      Object.keys(sections).forEach(key => {
        if (key === sectionKey) {
          sections[key].classList.add('active');
        } else {
          sections[key].classList.remove('active');
        }
      });
    });
  });

  // --------- CLOCK ----------
  function updateClock() {
    const el = document.getElementById('clock');
    if (!el) return;
    const now = new Date();
    el.textContent = 'Local time: ' + now.toLocaleString();
  }
  setInterval(updateClock, 1000);
  updateClock();

  // --------- OVERVIEW ----------
  let lastIngestSource = '–';
  let lastBatchMitreCount = 0;

  const btnIngest = document.getElementById('btn-ingest');
  const btnRefresh = document.getElementById('btn-refresh');
  const presetFeedSelect = document.getElementById('presetFeed');

  function setStatus(message, isError = false) {
    const statusEl = document.getElementById('status');
    if (!statusEl) return;
    statusEl.className = 'status-text' + (isError ? ' error' : '');
    statusEl.innerHTML = '<span class="dot"></span>' + message;
  }

  function applyPresetFeed() {
    const preset = presetFeedSelect.value;
    if (preset) {
      document.getElementById('rss').value = preset;
    }
  }

  if (presetFeedSelect) {
    presetFeedSelect.addEventListener('change', applyPresetFeed);
  }

  async function ingest() {
    const rss = document.getElementById('rss').value.trim();
    const count = parseInt(document.getElementById('count').value || '3', 10);

    if (!rss) {
      setStatus('Please provide a valid RSS URL.', true);
      return;
    }

    setStatus('Running pipeline: fetching, cleaning, summarising, extracting IOCs & mapping MITRE…');

    try {
      const res = await fetch('/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rss_url: rss,
          max_items: count,
          save: true
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || ('HTTP ' + res.status));
      }

      const data = await res.json();
      const itemCount = data.count ?? 0;

      lastIngestSource = tryExtractDomain(rss);
      lastBatchMitreCount = countMitreInBatch(data.items || []);
      updateStats(data.items || []);

      setStatus('Completed. Processed ' + itemCount + ' articles from feed.');
      await loadReports();
    } catch (err) {
      setStatus('Error during ingestion: ' + err.message, true);
    }
  }

  function tryExtractDomain(url) {
    try {
      const u = new URL(url);
      return u.hostname;
    } catch {
      return 'Custom Feed';
    }
  }

  function countMitreInBatch(items) {
    let total = 0;
    for (const r of items) {
      if (r.mitre && Array.isArray(r.mitre.techniques)) {
        total += r.mitre.techniques.length;
      }
    }
    const statMitre = document.getElementById('stat-mitre');
    if (statMitre) statMitre.textContent = total || '0';
    return total;
  }

  function updateStats(itemsFromIngest) {
    const sourceEl = document.getElementById('stat-source');
    if (sourceEl) sourceEl.textContent = lastIngestSource || '–';

    if (itemsFromIngest && itemsFromIngest.length > 0) {
      const statMitre = document.getElementById('stat-mitre');
      if (statMitre) statMitre.textContent = lastBatchMitreCount || '0';
    }
  }

  async function loadReports() {
    setStatus('Loading reports from local database…');

    try {
      const res = await fetch('/reports');
      if (!res.ok) {
        throw new Error('HTTP ' + res.status);
      }
      const data = await res.json();
      const items = data.items || [];

      const box = document.getElementById('reports');
      if (!box) return;

      box.innerHTML = '';

      const totalEl = document.getElementById('stat-total');
      if (totalEl) totalEl.textContent = data.count ?? items.length ?? 0;

      if (!items.length) {
        box.innerHTML =
          '<p style="font-size:12px; color:#9ca3af; margin-top:4px;">No reports found. Ingest a feed to see AI-generated summaries here.</p>';
        setStatus('No reports in database yet.');
        return;
      }

      if (lastIngestSource === '–') {
        const last = items[0];
        if (last && last.link) lastIngestSource = tryExtractDomain(last.link);
      }
      const sourceEl = document.getElementById('stat-source');
      if (sourceEl) sourceEl.textContent = lastIngestSource || '–';

      items.forEach(r => {
        const div = document.createElement('div');
        div.className = 'report-card';

        const mitreCount =
          r.mitre && Array.isArray(r.mitre.techniques) ? r.mitre.techniques.length : 0;

        div.innerHTML = `
          <div class="report-title-row">
            <div class="report-title">
              ${escapeHtml(r.title || '(untitled threat report)')}
            </div>
            <div class="report-meta">
              <div class="pill-mitre-count">
                🎯 MITRE: <strong>${mitreCount}</strong>
              </div>
              <div>${escapeHtml(r.published || 'Published: N/A')}</div>
              <div>Saved: ${escapeHtml(r.created_at || '')}</div>
            </div>
          </div>

          <div class="report-summary">
            <strong>AI Summary:</strong> ${escapeHtml(r.summary || 'No summary available.')}
          </div>

          <div class="mitre-tags">
            ${
              r.mitre && Array.isArray(r.mitre.techniques) && r.mitre.techniques.length
                ? r.mitre.techniques
                    .map(t => `<span class="mitre-tag">${escapeHtml(t)}</span>`)
                    .join('')
                : '<span style="font-size:11px; color:#9ca3af;">No MITRE techniques detected for this item.</span>'
            }
          </div>

          <div class="report-actions">
            <a class="link" href="${r.link || '#'}" target="_blank">
              🌐 <span>Open Original Article</span>
            </a>
            <a class="link" href="/report/${r.id}" target="_blank">
              🧾 <span>View Raw JSON</span>
            </a>
            <span class="details-toggle" data-id="${r.id}">
              ▶ Deep-dive NLP analysis
            </span>
          </div>

          <div class="report-details" id="details-${r.id}">
            <div style="font-size:11px;">Loading analysis…</div>
          </div>
        `;

        box.appendChild(div);
      });

      // Attach toggle handlers after rendering
      box.querySelectorAll('.details-toggle').forEach(el => {
        el.addEventListener('click', () => {
          const id = el.getAttribute('data-id');
          toggleDetails(id, el);
        });
      });

      setStatus('Loaded ' + items.length + ' reports from local database.');
    } catch (err) {
      setStatus('Error loading reports: ' + err.message, true);
    }
  }

  async function toggleDetails(id, el) {
    const details = document.getElementById('details-' + id);
    if (!details) return;

    const isVisible = details.style.display === 'block';
    if (isVisible) {
      details.style.display = 'none';
      el.textContent = '▶ Deep-dive NLP analysis';
      return;
    }

    if (!details.dataset.loaded) {
      try {
        const res = await fetch('/report/' + id);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        details.innerHTML = buildDetailsHtml(data);
        details.dataset.loaded = '1';
      } catch (err) {
        details.innerHTML =
          '<div style="color:#fca5a5;">Failed to load analysis: ' +
          escapeHtml(err.message) +
          '</div>';
      }
    }

    details.style.display = 'block';
    el.textContent = '▼ Hide deep-dive analysis';
  }

  function buildDetailsHtml(data) {
    const iocs = data.iocs || {};
    const entities = data.entities || {};

    const iocHtml = buildIocChips(iocs);
    const entHtml = buildEntityChips(entities);

    return `
      <div class="details-grid">
        <div>
          <div class="details-block-title">Indicators of Compromise (IOCs)</div>
          ${iocHtml}
        </div>
        <div>
          <div class="details-block-title">Named Entities (spaCy NER)</div>
          ${entHtml}
        </div>
      </div>
    `;
  }

  function buildIocChips(iocs) {
    const chips = [];
    const add = (label, arr, cls) => {
      if (!arr || !arr.length) return;
      arr.forEach(v => {
        chips.push(
          `<span class="chip ${cls}">${label}: ${escapeHtml(String(v))}</span>`
        );
      });
    };
    add('IP', iocs.ips, 'danger');
    add('Domain', iocs.domains, 'info');
    add('URL', iocs.urls, 'info');
    add('MD5', iocs.md5, 'muted');
    add('SHA1', iocs.sha1, 'muted');
    add('SHA256', iocs.sha256, 'muted');

    if (!chips.length) {
      return '<div class="chips"><span class="chip muted">No IOCs detected in this summary.</span></div>';
    }
    return '<div class="chips">' + chips.join('') + '</div>';
  }

  function buildEntityChips(entities) {
    const chips = [];
    Object.keys(entities).forEach(label => {
      const vals = entities[label] || [];
      vals.forEach(v => {
        chips.push(
          `<span class="chip">${escapeHtml(label)}: ${escapeHtml(String(v))}</span>`
        );
      });
    });
    if (!chips.length) {
      return '<div class="chips"><span class="chip muted">No named entities recognised (spaCy NER).</span></div>';
    }
    return '<div class="chips">' + chips.join('') + '</div>';
  }

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // --------- CVE ANALYZER ----------
  const btnCve = document.getElementById('btn-cve');

  function setCveStatus(msg, isError = false) {
    const el = document.getElementById('cve-status');
    if (!el) return;
    el.className = 'status-text' + (isError ? ' error' : '');
    el.innerHTML = '<span class="dot"></span>' + msg;
  }

  async function analyzeCVE() {
    const cveIdInput = document.getElementById('cve-id');
    const cveId = cveIdInput.value.trim().toUpperCase();

    if (!cveId || !cveId.startsWith('CVE-')) {
      setCveStatus('Please enter a valid CVE ID (e.g., CVE-2024-3094).', true);
      return;
    }

    setCveStatus('Fetching CVE details from NVD and generating AI explanation…');

    try {
      const res = await fetch('/cve/' + encodeURIComponent(cveId));
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || ('HTTP ' + res.status));
      }

      const data = await res.json();
      renderCveDetails(data);
      setCveStatus('CVE details and AI explanation loaded.');
    } catch (err) {
      const detailsEl = document.getElementById('cve-details');
      const aiEl = document.getElementById('cve-ai-text');
      if (detailsEl) detailsEl.innerHTML = '';
      if (aiEl) aiEl.textContent = 'No explanation available.';
      setCveStatus('Error analyzing CVE: ' + err.message, true);
    }
  }

  function renderCveDetails(res) {
    const details = res.details || {};
    const ai = res.ai_explanation || '';

    const sev = (details.severity || '').toUpperCase();
    let sevClass = 'sev-low';
    if (sev === 'CRITICAL') sevClass = 'sev-critical';
    else if (sev === 'HIGH') sevClass = 'sev-high';
    else if (sev === 'MEDIUM') sevClass = 'sev-medium';

    const cveDetailsEl = document.getElementById('cve-details');
    if (cveDetailsEl) {
      cveDetailsEl.innerHTML = `
        <div class="cve-result-card">
          <div class="cve-badge">
            🧩 <strong>${escapeHtml(details.id || res.cve_id || '')}</strong>
          </div>
          <div style="font-size:12px; margin-bottom:6px;">
            ${escapeHtml(details.description || 'No description available.')}
          </div>
          <div style="font-size:11px; color:#9ca3af; margin-bottom:6px;">
            <span class="severity-pill ${sevClass}">Severity: ${escapeHtml(
        details.severity || 'N/A'
      )}</span>
            &nbsp;• CVSS: <strong>${
              details.score != null ? details.score : 'N/A'
            }</strong>
            &nbsp;• Vector: ${escapeHtml(details.vector || 'N/A')}
          </div>
          <div style="font-size:11px; color:#9ca3af;">
            Published: ${escapeHtml(details.published || 'N/A')}<br/>
            Last Updated: ${escapeHtml(details.updated || 'N/A')}
          </div>
        </div>
      `;
    }

    const aiEl = document.getElementById('cve-ai-text');
    if (aiEl) aiEl.textContent = ai || 'AI model did not return an explanation.';
  }

  // ============================================================
  // REAL VOICE ASSISTANT (Browser Speech Recognition + Backend)
  // ============================================================

  const mic = document.getElementById("mic-btn");
  const voiceStatus = document.getElementById("voice-status");
  const recognized = document.getElementById("recognized-text");
  const aiResp = document.getElementById("response-text");

  let recognition;

  if ("webkitSpeechRecognition" in window) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      mic.classList.add("listening");
      voiceStatus.textContent = "Listening… Speak now!";
    };

    recognition.onend = () => {
      mic.classList.remove("listening");
      voiceStatus.textContent = "Click the microphone to speak again.";
    };

    recognition.onerror = () => {
      voiceStatus.textContent = "Error capturing voice.";
    };

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      recognized.textContent = transcript;

      voiceStatus.textContent = "Processing your query…";

      // Send to backend
      const res = await fetch("/voice_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: transcript })
      });

      const data = await res.json();
      aiResp.textContent = data.response;

      voiceStatus.textContent = "Ready for next query.";
    };
  }

  if (mic) {
    mic.addEventListener("click", () => {
      if (!recognition) {
        alert("Speech recognition is not supported in this browser.");
        return;
      }
      recognition.start();
    });
  }

  // Attach button handlers
  if (btnIngest) btnIngest.addEventListener('click', ingest);
  if (btnRefresh) btnRefresh.addEventListener('click', loadReports);
  if (btnCve) btnCve.addEventListener('click', analyzeCVE);

  // Initial load of reports
  loadReports();
});
