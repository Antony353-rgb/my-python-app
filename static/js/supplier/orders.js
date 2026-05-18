'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Filter orders by status
  const filter = document.getElementById('order-status-filter');
  if (filter) {
    filter.addEventListener('change', function() {
      document.querySelectorAll('.order-row').forEach(row => {
        row.style.display = (!this.value || row.dataset.status === this.value) ? '' : 'none';
      });
    });
  }

  // Auto-refresh pending orders
  const pendingCount = document.querySelectorAll('[data-status="ordered"]').length;
  if (pendingCount > 0) {
    setTimeout(() => window.location.reload(), 30000);
  }
});
