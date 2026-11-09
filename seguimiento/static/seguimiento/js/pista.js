/* ==========================================================================
   Evaluación en Pista — Guardado asíncrono, filtro rápido y conteo en vivo
   ========================================================================== */

(() => {
  const table = document.querySelector('.pista-table');
  const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
  if (!table || !csrfInput) return;

  const saveUrl = table.dataset.saveUrl;
  const token = csrfInput.value;
  const pending = new Set();
  const rows = [...table.querySelectorAll('tr.player')];
  const progressEl = document.querySelector('[data-pista-progress]');
  const filterInput = document.querySelector('[data-pista-filter]');
  const emptyFilterRow = table.querySelector('[data-pista-empty-filter]');
  const markAllBtn = document.querySelector('[data-mark-all-present]');
  const rowControllers = [];

  window.addEventListener('beforeunload', (event) => {
    if (pending.size) {
      event.preventDefault();
      event.returnValue = '';
    }
  });

  function updateProgress() {
    if (!progressEl) return;
    const evaluated = rows.filter((row) => {
      const sel = row.querySelector('.attendance');
      return sel && sel.value !== '';
    }).length;
    progressEl.textContent = `${evaluated} de ${rows.length}`;
  }

  function applyFilter() {
    if (!filterInput) return;
    const rawQuery = filterInput.value.trim().toLowerCase();
    const compactQuery = rawQuery.replace(/[\s.\-]/g, '');
    let visibleCount = 0;

    rows.forEach((row) => {
      const text = (row.dataset.search || '').toLowerCase();
      const compactText = text.replace(/[\s.\-]/g, '');
      const matches = !rawQuery || text.includes(rawQuery) || (compactQuery && compactText.includes(compactQuery));
      row.hidden = !matches;
      if (matches) visibleCount++;
    });

    if (emptyFilterRow) {
      emptyFilterRow.hidden = !(rawQuery && visibleCount === 0);
    }
  }

  rows.forEach((row) => {
    let busy = false;
    const attendance = row.querySelector('.attendance');
    const status = row.querySelector('.status');
    const retry = row.querySelector('.retry');

    function paint() {
      const absent = ['A', 'J'].includes(attendance.value);
      const locked = row.dataset.locked === '1';

      row.classList.toggle('absent', absent);
      row.querySelectorAll('.scores').forEach((group) => {
        group.querySelectorAll('button').forEach((btn) => {
          const isSelected = Number(btn.dataset.score) === Number(group.dataset.value);
          btn.classList.toggle('selected', isSelected);
          btn.setAttribute('aria-pressed', String(isSelected));
          btn.disabled = busy || absent || !attendance.value || locked;
        });
      });

      attendance.disabled = busy || attendance.value === 'J' || locked;
    }

    async function save() {
      if (busy) return false;
      busy = true;
      pending.add(row);
      paint();

      status.textContent = 'Guardando…';
      status.classList.remove('error');
      retry.hidden = true;

      const data = {
        jugador: Number(row.dataset.player),
        sesion: Number(row.dataset.session),
        asistencia: attendance.value,
      };
      row.querySelectorAll('.scores').forEach((group) => {
        data[group.dataset.key] = Number(group.dataset.value);
      });

      try {
        const response = await fetch(saveUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token,
          },
          body: JSON.stringify(data),
          signal: AbortSignal.timeout(10000),
        });

        if (!response.ok) throw new Error('No guardado');
        const result = await response.json();
        if (result.ok !== true) throw new Error('No guardado');

        status.textContent = 'Guardado';
        const link = row.querySelector('.observation');
        if (link) {
          link.href = `/evaluaciones/${result.evaluacion}/observacion/`;
          link.hidden = false;
        }
        pending.delete(row);
        updateProgress();
        return true;
      } catch (err) {
        status.textContent = 'No guardado. Reintenta.';
        status.classList.add('error');
        retry.hidden = false;
        return false;
      } finally {
        busy = false;
        paint();
      }
    }

    row.querySelectorAll('.scores').forEach((group) => {
      for (let n = 1; n <= 10; n++) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = n;
        btn.dataset.score = n;
        btn.className = n <= 4 ? 'low' : n <= 7 ? 'mid' : 'high';
        btn.setAttribute('aria-label', `${group.getAttribute('aria-label')} ${n}`);
        btn.addEventListener('click', () => {
          group.dataset.value = n;
          save();
        });
        group.appendChild(btn);
      }
    });

    attendance.addEventListener('change', () => {
      if (!attendance.value) return;
      if (attendance.value === 'A') {
        row.querySelectorAll('.scores').forEach((group) => {
          group.dataset.value = 0;
        });
      }
      save();
    });

    retry.addEventListener('click', save);
    paint();

    rowControllers.push({
      row,
      attendance,
      isBusy: () => busy,
      save,
    });
  });

  if (filterInput) {
    filterInput.addEventListener('input', applyFilter);
  }

  if (markAllBtn) {
    markAllBtn.addEventListener('click', async () => {
      const targets = rowControllers.filter(
        (ctrl) => !ctrl.row.hidden && ctrl.row.dataset.locked !== '1' && ctrl.attendance.value === '' && !ctrl.isBusy(),
      );
      if (!targets.length) return;
      const originalText = markAllBtn.textContent;
      markAllBtn.disabled = true;
      markAllBtn.textContent = 'Marcando presentes…';
      try {
        for (const ctrl of targets) {
          ctrl.attendance.value = 'P';
          await ctrl.save();
        }
      } finally {
        markAllBtn.disabled = false;
        markAllBtn.textContent = originalText;
      }
    });
  }
})();
