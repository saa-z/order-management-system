// ============================================
// San Giorgio — helpers auth partagés (web)
// ============================================
const SG = {
  token() { return localStorage.getItem('sg_token'); },
  user() { try { return JSON.parse(localStorage.getItem('sg_user') || 'null'); } catch (e) { return null; } },
  setAuth(token, user) {
    localStorage.setItem('sg_token', token);
    localStorage.setItem('sg_user', JSON.stringify(user));
  },
  logout() {
    localStorage.removeItem('sg_token');
    localStorage.removeItem('sg_user');
    location.href = '/web/login.html';
  },
  requireAuth() {
    if (!this.token() || !this.user()) { location.href = '/web/login.html'; return false; }
    return true;
  },
  async api(path, opts = {}) {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    const t = this.token();
    if (t) headers['Authorization'] = 'Bearer ' + t;
    const res = await fetch(path, Object.assign({}, opts, { headers }));
    if (res.status === 401) { this.logout(); throw new Error('Session expirée'); }
    return res;
  },
  fmtPrice(v) { return (Number(v) || 0).toFixed(2) + ' €'; },
  fmtDate(s) {
    if (!s) return '—';
    const d = new Date(s);
    if (isNaN(d)) return String(s).slice(0, 16).replace('T', ' ');
    return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  },
  esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); },
};

// Renvoie l'en-tête d'app standard (logo, user, rôle, historique/POS, déconnexion)
function renderHeader(active) {
  const u = SG.user() || {};
  const roleLabel = u.role === 'admin' ? 'Admin' : 'Serveur';
  let nav = '';
  if (active === 'pos') nav = '<a class="hbtn" href="/web/history.html">Hist.</a>';
  else if (active === 'history') nav = '<a class="hbtn" href="/web/pos.html">+Cmd</a>';
  const back = (active === 'pos' || active === 'history')
    ? '<a class="hbtn back" id="btn-back" href="/web/menu.html" aria-label="Retour">‹</a>' : '';
  return `
    ${back}
    <a class="logo" href="/web/menu.html" style="text-decoration:none">SG</a>
    <span class="role-pill">${SG.esc(u.username || '')} · ${roleLabel}</span>
    <span class="spacer"></span>
    ${nav}
    <button class="hbtn danger" onclick="SG.logout()">Quitter</button>`;
}

const ORDER_TYPE_LABELS = { eat_in: 'Sur place', take_away: 'À emporter' };
const SEATING_LABELS = { indoor: 'Salle', outdoor: 'Terrasse' };
const STATUS_LABELS = { pending: 'En attente', paid: 'Payée', cancelled: 'Annulée' };
const STATUS_COLORS = { pending: '#B88647', paid: '#5cb85c', cancelled: '#e07a72' };
