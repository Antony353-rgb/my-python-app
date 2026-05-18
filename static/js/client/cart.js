'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Live cart total update
  function recalcTotal() {
    let total = 0;
    document.querySelectorAll('.cart-row').forEach(row => {
      const price = parseFloat(row.dataset.price || 0);
      const qty = parseInt(row.querySelector('.cart-qty')?.value || 1);
      const lineTotal = price * qty;
      row.querySelector('.cart-line-total').textContent = formatCurrency(lineTotal);
      total += lineTotal;
    });
    const totalEl = document.getElementById('cart-total');
    if (totalEl) totalEl.textContent = formatCurrency(total);
  }

  document.querySelectorAll('.cart-qty').forEach(input => {
    input.addEventListener('change', recalcTotal);
  });

  // Confirm remove
  document.querySelectorAll('.remove-item-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (!confirm('Remove this item from cart?')) e.preventDefault();
    });
  });

  // Checkout validation
  const checkoutBtn = document.getElementById('checkout-btn');
  if (checkoutBtn) {
    checkoutBtn.addEventListener('click', (e) => {
      const items = document.querySelectorAll('.cart-row');
      if (items.length === 0) {
        e.preventDefault();
        showToast('Your cart is empty', 'error');
      }
    });
  }
});
