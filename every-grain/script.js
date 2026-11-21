(function () {
  var root = document.documentElement;
  var btn = document.getElementById('theme');
  function paint() { if (btn) btn.textContent = root.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙'; }
  paint();
  if (btn) btn.addEventListener('click', function () {
    var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', t);
    try { localStorage.setItem('theme', t); } catch (e) {}
    paint();
  });
  var bar = document.getElementById('progress');
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    if (bar) bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  var f = document.getElementById('filter');
  if (f) {
    var cards = Array.prototype.slice.call(document.querySelectorAll('.chapter'));
    var count = document.getElementById('count');
    f.addEventListener('input', function () {
      var q = f.value.trim().toLowerCase(), shown = 0;
      cards.forEach(function (c) {
        var ok = !q || (c.getAttribute('data-s') || '').indexOf(q) !== -1;
        c.style.display = ok ? '' : 'none';
        if (ok) shown++;
      });
      document.querySelectorAll('.part').forEach(function (p) {
        p.style.display = p.querySelector('.chapter:not([style*="none"])') ? '' : 'none';
      });
      if (count) count.textContent = q ? shown + ' match' + (shown === 1 ? '' : 'es') : '';
    });
  }
})();
