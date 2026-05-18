'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Drag-drop upload zone
  const uploadZone = document.getElementById('upload-zone');
  const fileInput = document.getElementById('csv-file-input');
  if (uploadZone && fileInput) {
    uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadZone.classList.add('drag-over');
    });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file && file.name.endsWith('.csv')) {
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        document.getElementById('file-name-display').textContent = file.name;
        parseCSVPreview(file);
      } else {
        showToast('Please upload a CSV file', 'error');
      }
    });
    uploadZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', function() {
      if (this.files[0]) {
        document.getElementById('file-name-display').textContent = this.files[0].name;
        parseCSVPreview(this.files[0]);
      }
    });
  }

  function parseCSVPreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const lines = e.target.result.trim().split('\n').filter(l => l.trim());
      const preview = document.getElementById('csv-preview');
      if (preview) {
        preview.textContent = `${lines.length - 1} codes found in CSV`;
        preview.className = 'text-green-600 text-sm mt-2 font-medium';
      }
    };
    reader.readAsText(file);
  }

  // Filter inventory by status
  const statusFilter = document.getElementById('status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', function() {
      document.querySelectorAll('.code-row').forEach(row => {
        row.style.display = (!this.value || row.dataset.status === this.value) ? '' : 'none';
      });
    });
  }
});
