/* ==========================================================================
   Evaluación en Pista — Guardado asíncrono on-click
   ========================================================================== */

(() => {
  const table = document.querySelector('.pista-table');
  const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
  if (!table || !csrfInput) return;

  const saveUrl = table.dataset.saveUrl;
  const token = csrfInput.value;
  const pending = new Set();

  window.addEventListener('beforeunload', (event) => {
    if (pending.size) {
      event.preventDefault();
      event.returnValue = '';
    }
  });

  document.querySelectorAll('.player').forEach((row) => {
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
      if (busy) return;
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
        link.href = `/evaluaciones/${result.evaluacion}/observacion/`;
        link.hidden = false;
        pending.delete(row);
      } catch (err) {
        status.textContent = 'No guardado. Reintenta.';
        status.classList.add('error');
        retry.hidden = false;
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
  });
})();
