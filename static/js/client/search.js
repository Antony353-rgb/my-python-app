'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Save last selected currency to localStorage
  const currencySelect = document.getElementById('currency-select');
  if (currencySelect) {
    const saved = localStorage.getItem('lastCurrency');
    if (saved) currencySelect.value = saved;
    currencySelect.addEventListener('change', function() {
      localStorage.setItem('lastCurrency', this.value);
    });
  }

  // Filter search results client-side
  const filterInput = document.getElementById('result-filter');
  if (filterInput) {
    filterInput.addEventListener('input', debounce(function() {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.product-card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(q) ? '' : 'none';
      });
    }, 200));
  }

  // Sort results
  const sortSelect = document.getElementById('result-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', function() {
      const cards = [...document.querySelectorAll('.product-card')];
      const container = document.getElementById('results-container');
      if (!container) return;
      cards.sort((a, b) => {
        const pa = parseFloat(a.dataset.price || 0);
        const pb = parseFloat(b.dataset.price || 0);
        return this.value === 'price-asc' ? pa - pb : pb - pa;
      });
      cards.forEach(c => container.appendChild(c));
    });
  }

  // Qty input validation - don't exceed stock
  document.querySelectorAll('.qty-input').forEach(input => {
    const max = parseInt(input.getAttribute('max') || 9999);
    input.addEventListener('change', function() {
      if (parseInt(this.value) > max) {
        this.value = max;
        showToast(`Max available: ${max}`, 'error');
      }
      if (parseInt(this.value) < 1) this.value = 1;
    });

    // Live price preview
    const priceEl = input.closest('.product-card')?.querySelector('.unit-price');
    const totalEl = input.closest('.product-card')?.querySelector('.total-price');
    if (priceEl && totalEl) {
      const unitPrice = parseFloat(priceEl.dataset.price || 0);
      input.addEventListener('input', function() {
        const qty = parseInt(this.value) || 1;
        totalEl.textContent = formatCurrency(unitPrice * qty);
      });
    }
  });
});
