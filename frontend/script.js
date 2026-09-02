let phones = [];
let sortKey = null;
let sortAsc = true;

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(this.dataset.tab).classList.add('active');
        if (this.dataset.tab === 'compare') populateCompareSelects();
    });
});

// Load phones on page load
document.addEventListener('DOMContentLoaded', loadPhones);

function showToast(msg, isError = false) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = isError ? 'show error' : 'show';
    setTimeout(() => t.classList.remove('show'), 3000);
}

// ---- PHONE TABLE ----
async function loadPhones() {
    document.getElementById('loading-text').style.display = 'block';
    try {
        const res = await fetch('/api/phones');
        const data = await res.json();
        phones = data.phones;
        document.getElementById('phone-count').textContent = phones.length;
        document.getElementById('loading-text').style.display = 'none';
        renderTable();
    } catch (e) {
        document.getElementById('loading-text').textContent = 'Failed to load phones. Is the server running?';
    }
}

function renderTable() {
    const search = (document.getElementById('search-input').value || '').toLowerCase();
    let filtered = phones.filter(p => p.name.toLowerCase().includes(search));

    // Sort
    if (sortKey) {
        filtered.sort((a, b) => {
            let va = (a[sortKey] || '').toString().toLowerCase();
            let vb = (b[sortKey] || '').toString().toLowerCase();
            if (sortKey === 'name') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
            // Numeric sort for specs
            let na = parseFloat(va) || 0;
            let nb = parseFloat(vb) || 0;
            return sortAsc ? na - nb : nb - na;
        });
    }

    const tbody = document.getElementById('phone-tbody');
    tbody.innerHTML = filtered.map(p => `
        <tr>
            <td><strong>${p.name}</strong></td>
            <td><span class="spec-cell" title="${escapeHtml(p.display_size)}">${escapeHtml(p.display_size || '')}</span></td>
            <td><span class="spec-cell" title="${escapeHtml(p.processor)}">${escapeHtml(p.processor || '')}</span></td>
            <td>${escapeHtml(p.ram || '')}</td>
            <td>${escapeHtml(p.battery || '')}</td>
            <td><span class="spec-cell" title="${escapeHtml(p.main_camera)}">${escapeHtml(p.main_camera || '')}</span></td>
            <td>${escapeHtml(p.price || '')}</td>
            <td><button class="delete-btn" onclick="deletePhone('${escapeHtml(p.name)}', ${p.id})">Delete</button></td>
        </tr>
    `).join('');
}

function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function filterTable() { renderTable(); }

// Sort on header click
document.querySelectorAll('#phone-table thead th[data-sort]').forEach(th => {
    th.addEventListener('click', function() {
        const key = this.dataset.sort;
        if (sortKey === key) sortAsc = !sortAsc;
        else { sortKey = key; sortAsc = true; }
        renderTable();
    });
});

// ---- CRUD ----
async function deletePhone(name, id) {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
        const res = await fetch(`/api/phone/${encodeURIComponent(name)}`, { method: 'DELETE' });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail); }
        showToast(`Deleted ${name}`);
        loadPhones();
    } catch (e) {
        showToast(e.message, true);
    }
}

async function deleteAllPhones() {
    if (!confirm('Delete ALL phones from the database?')) return;
    try {
        const res = await fetch('/api/phones', { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);
        showToast(data.message);
        loadPhones();
    } catch (e) {
        showToast(e.message, true);
    }
}

async function scrapeData() {
    showToast('Scraping GSMArena... (may take a minute)');
    document.getElementById('btn-scrape').disabled = true;
    document.getElementById('btn-scrape').textContent = 'Scraping...';
    try {
        const res = await fetch('/api/scrape', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);
        showToast(data.message);
        loadPhones();
    } catch (e) {
        showToast('Scrape failed: ' + e.message, true);
    }
    document.getElementById('btn-scrape').disabled = false;
    document.getElementById('btn-scrape').textContent = 'Scrape GSMArena';
}

async function seedData() {
    try {
        const res = await fetch('/api/seed', { method: 'POST' });
        const data = await res.json();
        showToast(data.message);
        loadPhones();
    } catch (e) {
        showToast('Seed failed: ' + e.message, true);
    }
}

// ---- COMPARE ----
async function populateCompareSelects() {
    const s1 = document.getElementById('compare-phone1');
    const s2 = document.getElementById('compare-phone2');
    s1.innerHTML = phones.map(p => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}</option>`).join('');
    s2.innerHTML = s1.innerHTML;
    // Select different defaults
    if (phones.length >= 2) {
        s1.value = phones[0].name;
        s2.value = phones[1].name;
    }
}

async function comparePhones() {
    const n1 = document.getElementById('compare-phone1').value;
    const n2 = document.getElementById('compare-phone2').value;
    const div = document.getElementById('compare-result');
    div.textContent = 'Comparing...';
    try {
        const res = await fetch('/api/compare', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: `compare ${n1} and ${n2}`})
        });
        const data = await res.json();
        div.textContent = data.comparison || 'No comparison available';
    } catch (e) {
        div.textContent = 'Error: ' + e.message;
    }
}

// ---- CHAT ----
async function askQuery() {
    const input = document.getElementById('chat-input');
    const q = input.value.trim();
    if (!q) return;
    const div = document.getElementById('chat-result');
    div.innerHTML = '<em>Thinking...</em>';
    try {
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: q})
        });
        const data = await res.json();
        div.textContent = data.answer || 'No answer';
    } catch (e) {
        div.textContent = 'Error: ' + e.message;
    }
}

function quickQuery(q) {
    document.getElementById('chat-input').value = q;
    askQuery();
}

// ---- REVIEW ----
async function getReview() {
    const input = document.getElementById('review-input');
    const q = input.value.trim();
    if (!q) return;
    const div = document.getElementById('review-result');
    div.innerHTML = '<em>Generating review...</em>';
    try {
        const res = await fetch('/api/review', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: q})
        });
        const data = await res.json();
        div.textContent = data.answer || 'No review generated';
    } catch (e) {
        div.textContent = 'Error: ' + e.message;
    }
}