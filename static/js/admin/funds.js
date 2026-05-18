'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Live balance preview in topup/topdown modal
  const amountInput = document.getElementById('fund-amount');
  const balanceDisplay = document.getElementById('current-balance');
  const previewDisplay = document.getElementById('balance-preview');

  if (amountInput && balanceDisplay && previewDisplay) {
    const currentBal = parseFloat(balanceDisplay.dataset.balance || 0);
    const txnType = document.getElementById('fm-type');

    amountInput.addEventListener('input', function() {
      const amount = parseFloat(this.value) || 0;
      const type = txnType ? txnType.value : 'topup';
      const newBal = type === 'topup' ? currentBal + amount : Math.max(0, currentBal - amount);
      previewDisplay.textContent = formatCurrency(newBal);
      previewDisplay.className = newBal >= 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold';
    });
  }

  // Filter transactions by currency
  const currencyFilter = document.getElementById('currency-filter');
  if (currencyFilter) {
    currencyFilter.addEventListener('change', function() {
      document.querySelectorAll('.txn-row').forEach(row => {
        row.style.display = (!this.value || row.dataset.currency === this.value) ? '' : 'none';
      });
    });
  }
});
