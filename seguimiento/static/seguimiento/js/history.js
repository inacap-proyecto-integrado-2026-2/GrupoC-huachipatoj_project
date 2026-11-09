/* ==========================================================================
   Historial Individual — Gráfico Canvas 2D con etiquetas e inspección táctil
   ========================================================================== */

(() => {
  const dataEl = document.getElementById('chart-data');
  const canvas = document.getElementById('chart');
  const emptyMsg = document.getElementById('chart-empty');
  const hoverMsg = document.getElementById('chart-hover');
  if (!dataEl || !canvas) return;

  const data = JSON.parse(dataEl.textContent);
  let activeIndex = null;

  function xFor(index, width) {
    if (data.length <= 1) return Math.round(width / 2);
    return 32 + (index * (width - 64)) / (data.length - 1);
  }

  function updateHoverText(index) {
    if (!hoverMsg) return;
    if (index === null || !data[index]) {
      hoverMsg.textContent = data.length
        ? 'Toca o pasa el cursor sobre un punto del gráfico para ver las notas de esa fecha.'
        : '';
      return;
    }
    const row = data[index];
    const f = row.frenado ?? '—';
    const p = row.pase ?? '—';
    const t = row.tiro ?? '—';
    hoverMsg.textContent = `${row.fecha} · Frenado: ${f} · Pase: ${p} · Tiro: ${t}`;
  }

  function draw() {
    canvas.width = canvas.clientWidth * 2;
    canvas.height = 520;

    const ctx = canvas.getContext('2d');
    ctx.scale(2, 2);

    const w = canvas.clientWidth;
    ctx.font = '12px system-ui';
    ctx.fillStyle = '#64748b';

    for (let n = 1; n <= 10; n++) {
      const y = 220 - (n - 1) * 21;
      ctx.fillText(n, 4, y + 4);
      ctx.strokeStyle = '#e2e8f0';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(26, y);
      ctx.lineTo(w - 14, y);
      ctx.stroke();
    }

    if (activeIndex !== null && data[activeIndex]) {
      const hx = xFor(activeIndex, w);
      ctx.strokeStyle = '#94a3b8';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(hx, 20);
      ctx.lineTo(hx, 228);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    const metrics = [
      ['frenado', '#0284c7'],
      ['pase', '#059669'],
      ['tiro', '#d97706'],
    ];

    metrics.forEach(([key, color]) => {
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = 2.2;
      ctx.beginPath();

      let started = false;
      data.forEach((d, i) => {
        if (d[key] === null) {
          started = false;
          return;
        }
        const x = xFor(i, w);
        const y = 220 - (d[key] - 1) * 21;
        if (started) ctx.lineTo(x, y);
        else ctx.moveTo(x, y);
        started = true;
      });
      ctx.stroke();

      data.forEach((d, i) => {
        if (d[key] === null) return;
        const x = xFor(i, w);
        const y = 220 - (d[key] - 1) * 21;
        const isActive = i === activeIndex;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, isActive ? 7 : 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, isActive ? 5 : 3.6, 0, Math.PI * 2);
        ctx.fill();
      });
    });

    ctx.fillStyle = '#64748b';
    if (data.length === 1) {
      ctx.fillText(data[0].fecha, Math.max(24, xFor(0, w) - 34), 250);
    } else if (data.length > 1) {
      const maxTicks = w < 440 ? 3 : 5;
      const tickIndices = new Set([0, data.length - 1]);
      if (data.length <= maxTicks) {
        for (let i = 0; i < data.length; i++) tickIndices.add(i);
      } else {
        for (let s = 1; s < maxTicks - 1; s++) {
          tickIndices.add(Math.round((s * (data.length - 1)) / (maxTicks - 1)));
        }
      }
      tickIndices.forEach((i) => {
        const x = xFor(i, w);
        const label = data[i].fecha;
        const drawX = i === 0 ? 24 : i === data.length - 1 ? Math.max(24, w - 76) : Math.max(24, x - 34);
        ctx.fillText(label, drawX, 250);
      });
    }
  }

  function findNearestIndex(clientX) {
    if (!data.length) return null;
    const rect = canvas.getBoundingClientRect();
    const relX = clientX - rect.left;
    const w = canvas.clientWidth;
    let bestIndex = 0;
    let bestDist = Infinity;
    data.forEach((_, i) => {
      const dist = Math.abs(relX - xFor(i, w));
      if (dist < bestDist) {
        bestDist = dist;
        bestIndex = i;
      }
    });
    return bestIndex;
  }

  canvas.addEventListener('mousemove', (event) => {
    const idx = findNearestIndex(event.clientX);
    if (idx !== activeIndex) {
      activeIndex = idx;
      updateHoverText(idx);
      draw();
    }
  });

  canvas.addEventListener('click', (event) => {
    const idx = findNearestIndex(event.clientX);
    activeIndex = idx;
    updateHoverText(idx);
    draw();
  });

  canvas.addEventListener('mouseleave', () => {
    activeIndex = null;
    updateHoverText(null);
    draw();
  });

  if (!data.length && emptyMsg) {
    emptyMsg.textContent = 'Sin notas disponibles. Registra evaluaciones para ver la evolución.';
  }
  updateHoverText(null);
  draw();
  window.addEventListener('resize', draw);
})();
