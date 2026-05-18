'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Animate stat numbers on load
  document.querySelectorAll('.stat-number').forEach(el => {
    const target = parseInt(el.dataset.value || el.textContent.replace(/[^0-9.]/g,''), 10);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.ceil(target / 40);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 20);
  });

  // Auto-refresh dashboard every 2 minutes
  setTimeout(() => window.location.reload(), 120000);
});
