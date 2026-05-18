'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Confirm cancel
  document.querySelectorAll('.cancel-order-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (!confirm('Cancel this order and reverse funds to client?')) {
        e.preventDefault();
      }
    });
  });

  // Copy order number
  document.querySelectorAll('.copy-order-num').forEach(el => {
    el.addEventListener('click', () => {
      copyToClipboard(el.textContent.trim());
    });
  });

  // Auto-refresh order detail page status
  const statusBadge = document.getElementById('order-status-badge');
  if (statusBadge && !['delivered','cancelled'].includes(statusBadge.dataset.status)) {
    setTimeout(() => window.location.reload(), 30000);
  }

  // Preview uploaded codes
  const codesTextarea = document.getElementById('codes-textarea');
  const previewDiv = document.getElementById('codes-preview');
  if (codesTextarea && previewDiv) {
    codesTextarea.addEventListener('input', debounce(function() {
      const lines = this.value.trim().split('\n').filter(l => l.trim());
      previewDiv.textContent = `${lines.length} codes detected`;
      previewDiv.className = lines.length > 0 ? 'text-green-600 text-xs mt-1' : 'text-gray-400 text-xs mt-1';
    }, 300));
  }
});
