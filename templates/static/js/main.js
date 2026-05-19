/* Foodie Junction - Main JavaScript */

// ── CSRF Cookie ──────────────────────────────────
function getCookie(name) {
  let v = null;
  document.cookie.split(';').forEach(c => {
    c = c.trim();
    if (c.startsWith(name + '=')) v = decodeURIComponent(c.slice(name.length + 1));
  });
  return v;
}

// ── Toast Notification ───────────────────────────
function showToast(msg, duration = 3000) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

// ── Cart Badge ───────────────────────────────────
function updateCartBadge(count) {
  const badge = document.getElementById('cartBadge');
  if (!badge) return;
  badge.textContent = count;
  if (count > 0) badge.classList.remove('hidden');
  else badge.classList.add('hidden');
}

// ── City Change ──────────────────────────────────
function changeCity(city) {
  const params = new URLSearchParams(window.location.search);
  params.set('city', city);
  window.location.href = '/?' + params.toString();
}

// ── Profile Menu ─────────────────────────────────
function toggleProfileMenu() {
  document.getElementById('profileMenu')?.classList.toggle('open');
}
document.addEventListener('click', e => {
  if (!e.target.closest('.nav-profile'))
    document.getElementById('profileMenu')?.classList.remove('open');
});

// ── Live Search ──────────────────────────────────
let searchTimer = null;
const globalSearch = document.getElementById('globalSearch');
const searchDropdown = document.getElementById('searchDropdown');

if (globalSearch) {
  globalSearch.addEventListener('input', e => {
    clearTimeout(searchTimer);
    const q = e.target.value.trim();
    if (q.length < 2) { searchDropdown?.classList.remove('active'); return; }
    searchTimer = setTimeout(() => doSearch(q), 300);
  });
  document.addEventListener('click', e => {
    if (!e.target.closest('.nav-search')) searchDropdown?.classList.remove('active');
  });
}

async function doSearch(q) {
  const city = document.getElementById('citySelect')?.value || 'bangalore';
  const res  = await fetch('/api/search/?q=' + encodeURIComponent(q) + '&city=' + city);
  const data = await res.json();
  const dd   = document.getElementById('searchDropdown');
  if (!dd) return;
  let html = '';
  if (data.restaurants?.length) {
    html += '<div style="padding:8px 16px;font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;">Restaurants</div>';
    html += data.restaurants.map(r =>
      `<a href="/restaurant/${r.id}/" class="search-result-item">
        <span>🏪</span>
        <div><strong>${r.name}</strong><br><small style="color:#6b7280">${r.city} · ⭐${r.rating}</small></div>
      </a>`
    ).join('');
  }
  if (data.food_items?.length) {
    html += '<div style="padding:8px 16px;font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;">Food Items</div>';
    html += data.food_items.map(f =>
      `<a href="/restaurant/${f.restaurant_id}/" class="search-result-item">
        <span>🍽️</span>
        <div><strong>${f.name}</strong><br><small style="color:#6b7280">${f.restaurant} · ₹${f.price}</small></div>
      </a>`
    ).join('');
  }
  if (!html) html = '<div style="padding:20px;text-align:center;color:#6b7280;">No results found</div>';
  dd.innerHTML = html;
  dd.classList.add('active');
}

// ── Sticky Navbar shadow ─────────────────────────
window.addEventListener('scroll', () => {
  const nav = document.getElementById('navbar');
  if (nav) nav.style.boxShadow = window.scrollY > 10 ? '0 4px 20px rgba(0,0,0,.1)' : '0 2px 12px rgba(0,0,0,.06)';
});

// ── Lazy image fallback ───────────────────────────
document.querySelectorAll('img[onerror]').forEach(img => {
  img.addEventListener('error', function() {
    this.src = '/static/images/food_default.jpg';
  });
});