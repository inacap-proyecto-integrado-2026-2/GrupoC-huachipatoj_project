/* ==========================================================================
   Historial Individual — Gráfico de Evolución en Canvas 2D
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
    ctx.fillStyle = '#afc2d5';

    for (let n = 1; n <= 10; n++) {
      const y = 220 - (n - 1) * 21;
      ctx.fillText(n, 3, y + 4);
      ctx.strokeStyle = '#2a3e56';
      ctx.beginPath();
      ctx.moveTo(25, y);
      ctx.lineTo(w - 15, y);
      ctx.stroke();
    }

    const metrics = [
      ['frenado', '#38bdf8'],
      ['pase', '#34d399'],
      ['tiro', '#fbbf24'],
    ];

    metrics.forEach(([key, color]) => {
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.beginPath();

      let started = false;
      data.forEach((d, i) => {
        if (d[key] === null) {
          started = false;
          return;
        }
        const x = 30 + (i * (w - 60)) / Math.max(data.length - 1, 1);
        const y = 220 - (d[key] - 1) * 21;
        if (started) ctx.lineTo(x, y);
        else ctx.moveTo(x, y);
        started = true;
      });
      ctx.stroke();

      data.forEach((d, i) => {
        if (d[key] === null) return;
        const x = 30 + (i * (w - 60)) / Math.max(data.length - 1, 1);
        const y = 220 - (d[key] - 1) * 21;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      });
    });

    ctx.fillStyle = '#afc2d5';
    if (data.length) {
      ctx.fillText(data[0].fecha, 25, 250);
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
