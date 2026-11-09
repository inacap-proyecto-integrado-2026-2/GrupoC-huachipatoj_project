/* ==========================================================================
   Evaluación en Pista — Guardado asíncrono, cola local sin red y filtro rápido
   ========================================================================== */

(() => {
  const table = document.querySelector('.pista-table');
  const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
  if (!table || !csrfInput) return;

  const QUEUE_KEY = 'cdh_pista_queue_v1';
  const saveUrl = table.dataset.saveUrl;
  const token = csrfInput.value;
  const pending = new Set();
  const rows = [...table.querySelectorAll('tr.player')];
  const progressEl = document.querySelector('[data-pista-progress]');
  const filterInput = document.querySelector('[data-pista-filter]');
  const emptyFilterRow = table.querySelector('[data-pista-empty-filter]');
  const markAllBtn = document.querySelector('[data-mark-all-present]');
  const offlineBanner = document.querySelector('[data-offline-banner]');
  const offlineCountEl = document.querySelector('[data-offline-count]');
  const syncBtn = document.querySelector('[data-sync-queue]');
  const rowControllers = [];
  const controllerByKey = new Map();
  let syncingQueue = false;

  function readQueue() {
    try {
      const raw = window.localStorage.getItem(QUEUE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (_) {
      return {};
    }
  }

  function writeQueue(queue) {
    try {
      const keys = Object.keys(queue);
      if (!keys.length) {
        window.localStorage.removeItem(QUEUE_KEY);
      } else {
        window.localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
      }
    } catch (_) {
      // Ignora restricciones de almacenamiento privado.
    }
    refreshOfflineBanner(queue);
  }

  function refreshOfflineBanner(queue = readQueue()) {
    const count = Object.keys(queue).length;
    if (offlineCountEl) {
      offlineCountEl.textContent = String(count);
    }
    if (offlineBanner) {
      offlineBanner.hidden = count === 0;
    }
  }

  function queueKey(sessionId, playerId) {
    return `${sessionId}_${playerId}`;
  }

  function enqueuePayload(payload) {
    const queue = readQueue();
    queue[queueKey(payload.sesion, payload.jugador)] = payload;
    writeQueue(queue);
  }

  function dequeuePayload(sessionId, playerId) {
    const queue = readQueue();
    const key = queueKey(sessionId, playerId);
    if (Object.hasOwn(queue, key)) {
      delete queue[key];
      writeQueue(queue);
    }
  }

  window.addEventListener('beforeunload', (event) => {
    if (pending.size || Object.keys(readQueue()).length) {
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

  async function postScore(payload) {
    const response = await fetch(saveUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': token,
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10000),
    });

    let body = {};
    try {
      body = await response.json();
    } catch (_) {
      body = {};
    }

    if (!response.ok || body.ok !== true) {
      const err = new Error(body.error || 'No guardado');
      err.httpStatus = response.status;
      throw err;
    }
    return body;
  }

  function isNetworkFailure(err) {
    if (!navigator.onLine) return true;
    if (!err) return false;
    if (typeof err.httpStatus === 'number') {
      return err.httpStatus >= 500;
    }
    return err.name === 'TypeError' || err.name === 'TimeoutError' || err.name === 'AbortError';
  }

  rows.forEach((row) => {
    let busy = false;
    const attendance = row.querySelector('.attendance');
    const status = row.querySelector('.status');
    const retry = row.querySelector('.retry');
    const key = queueKey(row.dataset.session, row.dataset.player);

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

    function applySavedResult(result) {
      status.textContent = 'Guardado';
      status.classList.remove('error');
      retry.hidden = true;
      const link = row.querySelector('.observation');
      if (link && result.evaluacion) {
        link.href = `/evaluaciones/${result.evaluacion}/observacion/`;
        link.hidden = false;
      }
      pending.delete(row);
      dequeuePayload(row.dataset.session, row.dataset.player);
      updateProgress();
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
        const result = await postScore(data);
        applySavedResult(result);
        return true;
      } catch (err) {
        if (isNetworkFailure(err)) {
          enqueuePayload(data);
          status.textContent = 'En cola local (sin red)';
        } else {
          dequeuePayload(row.dataset.session, row.dataset.player);
          status.textContent = err.message || 'No guardado. Reintenta.';
        }
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

    const initialQueue = readQueue();
    if (Object.hasOwn(initialQueue, key) && row.dataset.locked !== '1' && attendance.value !== 'J') {
      const queued = initialQueue[key];
      attendance.value = queued.asistencia || attendance.value;
      row.querySelectorAll('.scores').forEach((group) => {
        const val = queued[group.dataset.key];
        if (typeof val === 'number') {
          group.dataset.value = val;
        }
      });
      status.textContent = 'En cola local (sin red)';
      status.classList.add('error');
      retry.hidden = false;
    }

    paint();

    const ctrl = {
      row,
      attendance,
      isBusy: () => busy,
      save,
      applySavedResult,
    };
    rowControllers.push(ctrl);
    controllerByKey.set(key, ctrl);
  });

  async function syncQueue() {
    if (syncingQueue) return;
    const queue = readQueue();
    const entries = Object.entries(queue);
    if (!entries.length) {
      refreshOfflineBanner(queue);
      return;
    }

    syncingQueue = true;
    if (syncBtn) {
      syncBtn.disabled = true;
      syncBtn.textContent = 'Sincronizando…';
    }

    try {
      for (const [key, payload] of entries) {
        try {
          const result = await postScore(payload);
          const ctrl = controllerByKey.get(key);
          if (ctrl) {
            ctrl.applySavedResult(result);
          } else {
            dequeuePayload(payload.sesion, payload.jugador);
          }
        } catch (err) {
          if (typeof err.httpStatus === 'number' && err.httpStatus >= 400 && err.httpStatus < 500) {
            dequeuePayload(payload.sesion, payload.jugador);
          }
        }
      }
    } finally {
      syncingQueue = false;
      if (syncBtn) {
        syncBtn.disabled = false;
        syncBtn.textContent = 'Reintentar sincronización';
      }
      refreshOfflineBanner();
    }
  }

  if (syncBtn) {
    syncBtn.addEventListener('click', syncQueue);
  }
  window.addEventListener('online', syncQueue);
  refreshOfflineBanner();
  updateProgress();

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
