/**
 * BawdicSoft Visitor Tracker
 * Uses localStorage — persists across tabs, sessions, browser restart.
 * Combines with server-side IP tracking for robust user identification.
 */
(function() {
  const SESSION_KEY = 'bawdicsoft_session_id';
  const API_BASE = window.BAWDIC_API || 'http://localhost:8000';
  const DWELL_THRESHOLD_MS = 5000;
  const POLL_INTERVAL_MS = 2000;

  // ─── Use localStorage (persists across tabs & browser restart) ───
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now();
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  const currentPage = window.location.pathname;
  let pageEnterTime = performance.now();
  let popupShown = false;

  // ─── Send dwell time on page unload ───
  function sendDwellTime() {
    const dwellMs = Math.round(performance.now() - pageEnterTime);
    if (dwellMs < 1000) return;

    const payload = {
      session_id: sessionId,
      page: currentPage,
      dwell_ms: dwellMs,
      referrer: document.referrer || '',
    };

    const url = `${API_BASE}/track`;
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, JSON.stringify(payload));
    } else {
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
      });
    }
  }

  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') sendDwellTime();
  });
  window.addEventListener('beforeunload', sendDwellTime);

  // ─── Poll for trigger ───
  async function checkTrigger() {
    if (popupShown) return;
    try {
      const resp = await fetch(
        `${API_BASE}/check-trigger?session_id=${sessionId}&page=${encodeURIComponent(currentPage)}`
      );
      const data = await resp.json();
      if (data.trigger && !popupShown) {
        popupShown = true;
        showProactivePopup(data.message);
      }
    } catch (e) {
      // silent — server may be cold starting
    }
  }

  // ─── Popup UI ───
  function showProactivePopup(message) {
    const popup = document.createElement('div');
    popup.style.cssText = `
      position: fixed; bottom: 24px; right: 24px;
      max-width: 340px; background: #fff; border-radius: 12px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.15);
      padding: 16px 20px; z-index: 99999;
      font-family: system-ui, sans-serif;
      font-size: 14px; color: #111;
      display: flex; gap: 12px; align-items: flex-start;
      animation: bawdSlideUp 0.3s ease-out;
    `;

    if (!document.getElementById('bawdicsoft-popup-style')) {
      const style = document.createElement('style');
      style.id = 'bawdicsoft-popup-style';
      style.textContent = `
        @keyframes bawdSlideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .bawd-close:hover { opacity: 1 !important; }
      `;
      document.head.appendChild(style);
    }

    popup.innerHTML = `
      <div style="flex:1;">
        <div style="font-weight:600; margin-bottom:6px;">BawdicSoft Assistant</div>
        <div style="line-height:1.4; color:#444;">${message}</div>
      </div>
      <button class="bawd-close" aria-label="Close" style="
        background:none; border:none; cursor:pointer;
        font-size:18px; color:#999; opacity:0.6; padding:0; line-height:1;
      ">×</button>
    `;

    popup.querySelector('.bawd-close').addEventListener('click', () => popup.remove());
    document.body.appendChild(popup);
  }

  setInterval(checkTrigger, POLL_INTERVAL_MS);
  setTimeout(() => checkTrigger(), DWELL_THRESHOLD_MS + 500);
})();