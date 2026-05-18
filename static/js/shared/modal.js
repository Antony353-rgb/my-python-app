'use strict';

// Generic modal management
const Modal = {
  open(id) {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      el.querySelector('input, select, textarea')?.focus();
    }
  },
  close(id) {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('hidden');
      document.body.style.overflow = '';
    }
  },
  closeAll() {
    document.querySelectorAll('[id$="-modal"], [id="modal"]').forEach(m => {
      m.classList.add('hidden');
    });
    document.body.style.overflow = '';
  }
};

// Close modal on backdrop click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop') ||
      (e.target.id && e.target.id.endsWith('modal') && e.target === e.currentTarget)) {
    Modal.closeAll();
  }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') Modal.closeAll();
});
