'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Copy voucher codes on click
  document.querySelectorAll('.voucher-code').forEach(el => {
    el.style.cursor = 'pointer';
    el.title = 'Click to copy';
    el.addEventListener('click', function() {
      copyToClipboard(this.textContent.trim());
      this.style.background = '#dcfce7';
      setTimeout(() => this.style.background = '', 1000);
    });
  });

  // Filter transaction history by type
  const typeFilter = document.getElementById('txn-type-filter');
  if (typeFilter) {
    typeFilter.addEventListener('change', function() {
      document.querySelectorAll('.txn-row').forEach(row => {
        row.style.display = (!this.value || row.dataset.type === this.value) ? '' : 'none';
      });
    });
  }

  // Balance chart (simple bar for each currency)
  const chartContainer = document.getElementById('balance-chart');
  if (chartContainer) {
    const balances = JSON.parse(chartContainer.dataset.balances || '[]');
    const max = Math.max(...balances.map(b => b.balance), 1);
    balances.forEach(b => {
      const bar = document.createElement('div');
      const pct = Math.round((b.balance / max) * 100);
      bar.innerHTML = `
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-medium text-gray-600 w-12">${b.code}</span>
          <div class="flex-1 bg-gray-100 rounded h-4 overflow-hidden">
            <div class="h-full bg-blue-500 rounded transition-all" style="width:${pct}%"></div>
          </div>
          <span class="text-xs text-gray-600 w-20 text-right">${formatCurrency(b.balance, b.symbol)}</span>
        </div>`;
      chartContainer.appendChild(bar);
    });
  }
});
