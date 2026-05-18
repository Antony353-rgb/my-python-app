'use strict';

function loadNotificationCount() {
  const badge = document.getElementById('notif-badge');
  if (!badge) return;
  fetch('/client/notifications/count', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
      if (data.count > 0) {
        badge.textContent = data.count;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    })
    .catch(() => {});
}

// Poll every 60 seconds
document.addEventListener('DOMContentLoaded', () => {
  loadNotificationCount();
  setInterval(loadNotificationCount, 60000);
});
