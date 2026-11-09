/* ==========================================================================
   Layout Dashboard — Control del menú lateral móvil
   ========================================================================== */

(() => {
  const toggleBtn = document.querySelector('[data-sidebar-toggle]');
  const backdrop = document.querySelector('[data-sidebar-backdrop]');
  const sidebar = document.getElementById('app-sidebar');
  if (!toggleBtn || !sidebar) return;

  function setOpen(open) {
    document.body.classList.toggle('sidebar-open', open);
    toggleBtn.setAttribute('aria-expanded', String(open));
    if (backdrop) {
      backdrop.hidden = !open;
    }
  }

  toggleBtn.addEventListener('click', () => {
    setOpen(!document.body.classList.contains('sidebar-open'));
  });

  if (backdrop) {
    backdrop.addEventListener('click', () => setOpen(false));
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && document.body.classList.contains('sidebar-open')) {
      setOpen(false);
    }
  });
})();
