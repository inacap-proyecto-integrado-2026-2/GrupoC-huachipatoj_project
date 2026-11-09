/* ==========================================================================
   Historial Individual — Gráfico de Evolución en Canvas 2D (Tema Claro)
   ========================================================================== */

(() => {
  const dataEl = document.getElementById('chart-data');
  const canvas = document.getElementById('chart');
  const emptyMsg = document.getElementById('chart-empty');
  if (!dataEl || !canvas) return;

  const data = JSON.parse(dataEl.textContent);

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
        const x = 32 + (i * (w - 64)) / Math.max(data.length - 1, 1);
        const y = 220 - (d[key] - 1) * 21;
        if (started) ctx.lineTo(x, y);
        else ctx.moveTo(x, y);
        started = true;
      });
      ctx.stroke();

      data.forEach((d, i) => {
        if (d[key] === null) return;
        const x = 32 + (i * (w - 64)) / Math.max(data.length - 1, 1);
        const y = 220 - (d[key] - 1) * 21;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 3.6, 0, Math.PI * 2);
        ctx.fill();
      });
    });

    ctx.fillStyle = '#64748b';
    if (data.length) {
      ctx.fillText(data[0].fecha, 26, 250);
      if (data.length > 1) {
        ctx.fillText(data[data.length - 1].fecha, w - 100, 250);
      }
    }
  }

  if (!data.length && emptyMsg) {
    emptyMsg.textContent = 'Sin notas disponibles. Registra evaluaciones para ver la evolución.';
  }

  draw();
  window.addEventListener('resize', draw);
})();
