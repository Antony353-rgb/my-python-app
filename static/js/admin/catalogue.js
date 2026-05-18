'use strict';

// Filter products table by brand
function filterByBrand(brandName) {
  document.querySelectorAll('.product-row').forEach(row => {
    const brand = row.dataset.brand || '';
    row.style.display = (!brandName || brand === brandName) ? '' : 'none';
  });
}

// Update rate value inputs based on rate type
function updateRateInputs(selectEl, prefix) {
  const type = selectEl.value;
  const label = document.getElementById(prefix + '-rate-label');
  if (!label) return;
  if (type.includes('pct')) label.textContent = '%';
  else if (type === 'fixed') label.textContent = 'Price';
  else label.textContent = 'Amt';
}

// Confirm product removal from catalogue
function confirmRemove(cpId, productName) {
  if (confirm(`Remove "${productName}" from this catalogue?`)) {
    window.location.href = `/admin/catalogue/product/${cpId}/toggle`;
  }
}

// Search products in modal
const productSearch = document.getElementById('product-search');
if (productSearch) {
  productSearch.addEventListener('input', debounce(function() {
    const q = this.value.toLowerCase();
    document.querySelectorAll('.product-option').forEach(opt => {
      opt.style.display = opt.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  }, 200));
}
