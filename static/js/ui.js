/* CleanCraft UI interactions with backend-compatible progressive enhancement. */
(() => {
  const toast = document.getElementById('ui-toast');
  let toastTimeout;
  function notify(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => { toast.hidden = true; }, 6500);
  }

  const categoryList = document.getElementById('dataset-categories');
  const datasetType = document.getElementById('dataset-type');
  if (categoryList && datasetType) {
    categoryList.querySelectorAll('[data-category]').forEach(button => {
      button.addEventListener('click', () => {
        categoryList.querySelectorAll('[data-category]').forEach(other => {
          other.classList.remove('selected');
          other.setAttribute('aria-pressed', 'false');
        });
        button.classList.add('selected');
        button.setAttribute('aria-pressed', 'true');
        datasetType.value = button.dataset.category;
      });
    });
  }
  const generatorForm = document.getElementById('generator-form');
  generatorForm?.addEventListener('submit', event => {
    const records = document.getElementById('record-count');
    if (!records?.checkValidity()) {
      event.preventDefault();
      records?.reportValidity();
      return;
    }
  });

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('csv-file');
  const fileName = document.getElementById('selected-file');
  const showSelectedFile = (file) => {
    if (!fileName) return;
    fileName.textContent = file
      ? (/\.csv$/i.test(file.name) ? `Selected: ${file.name}` : 'Please choose a CSV (.csv) file.')
      : 'No file selected';
  };
  if (dropzone && fileInput) {
    fileInput.addEventListener('change', () => showSelectedFile(fileInput.files[0]));
    ['dragenter', 'dragover'].forEach(type => dropzone.addEventListener(type, event => {
      event.preventDefault();
      dropzone.classList.add('drag-over');
    }));
    ['dragleave', 'drop'].forEach(type => dropzone.addEventListener(type, event => {
      event.preventDefault();
      dropzone.classList.remove('drag-over');
    }));
    dropzone.addEventListener('drop', event => {
      const file = event.dataTransfer?.files?.[0];
      if (!file) return;
      if (/\.csv$/i.test(file.name)) {
        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
      }
      showSelectedFile(file);
    });
  }
  document.getElementById('preview-upload')?.addEventListener('click', event => {
    if (!fileInput?.files?.length) return notify('Choose a CSV file first.');
    if (!/\.csv$/i.test(fileInput.files[0].name)) {
      event.preventDefault();
      return notify('Please select a file ending in .csv.');
    }
  });

  const targetSelect = document.getElementById('target-select');
  targetSelect?.addEventListener('change', () => {
    const form = targetSelect.closest('form');
    form?.submit();
  });
})();
