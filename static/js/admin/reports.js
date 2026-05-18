'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Calculate report totals
  function calcTotal(selector) {
    let total = 0;
    document.querySelectorAll(selector).forEach(cell => {
      total += parseFloat(cell.dataset.value || cell.textContent.replace(/[^0-9.-]/g,'')) || 0;
    });
    return total;
  }

  // Show totals row
  const totalRow = document.getElementById('report-total-row');
  if (totalRow) {
    const revenueTotal = calcTotal('.revenue-cell');
    const profitTotal = calcTotal('.profit-cell');
    document.getElementById('total-revenue').textContent = formatCurrency(revenueTotal);
    document.getElementById('total-profit').textContent = formatCurrency(profitTotal);
  }

  // Export button state
  const exportBtn = document.getElementById('export-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', function() {
      this.textContent = 'Preparing...';
      this.disabled = true;
      setTimeout(() => {
        this.textContent = 'Export Excel';
        this.disabled = false;
      }, 3000);
    });
  }

  // Set date range shortcuts
  const shortcuts = { '7d': 7, '30d': 30, '90d': 90 };
  Object.entries(shortcuts).forEach(([id, days]) => {
    const btn = document.getElementById(`range-${id}`);
    if (btn) {
      btn.addEventListener('click', () => {
        const to = new Date();
        const from = new Date();
        from.setDate(from.getDate() - days);
        const fmt = d => d.toISOString().split('T')[0];
        document.querySelector('[name="date_from"]').value = fmt(from);
        document.querySelector('[name="date_to"]').value = fmt(to);
      });
    }
  });
});
