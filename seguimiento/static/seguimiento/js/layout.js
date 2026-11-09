/* ==========================================================================
   Layout Dashboard — Control del menú lateral móvil y confirmaciones seguras
   ========================================================================== */

(() => {
  const toggleBtn = document.querySelector('[data-sidebar-toggle]');
  const backdrop = document.querySelector('[data-sidebar-backdrop]');
  const sidebar = document.getElementById('app-sidebar');

  if (toggleBtn && sidebar) {
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
  }

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('button[data-confirm], a[data-confirm]');
    if (!trigger) return;
    if (!window.confirm(trigger.dataset.confirm)) {
      event.preventDefault();
    }
  });

  document.addEventListener('submit', (event) => {
    const form = event.target.closest('form[data-confirm]');
    if (!form) return;
    if (!window.confirm(form.dataset.confirm)) {
      event.preventDefault();
    }
  });
})();
