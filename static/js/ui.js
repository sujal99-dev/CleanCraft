/* CleanCraft UI V2: interaction previews only. No files are uploaded or processed. */
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
    event.preventDefault();
    const records = document.getElementById('record-count');
    if (!records?.checkValidity()) {
      records?.reportValidity();
      return;
    }
    notify('Generator UI is ready. Faker will be connected next; no dataset was created.');
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
  document.getElementById('preview-upload')?.addEventListener('click', () => {
    if (!fileInput?.files?.length) return notify('Choose a CSV file first. This preview does not upload it.');
    if (!/\.csv$/i.test(fileInput.files[0].name)) return notify('Please select a file ending in .csv.');
    notify('Your CSV is selected. The upload/analysis backend will be connected next. No file was transmitted.');
  });
  document.getElementById('clean-demo')?.addEventListener('click', () => {
    notify('Cleaning controls are ready. No changes were applied; backend processing is not connected yet.');
  });

  const targetSelect = document.getElementById('target-select');
  const rows = document.getElementById('model-rows');
  const demoModels = {
    classification: [
      ['Random Forest Classifier', 'Classification', 'Handles nonlinear relationships in tabular features'],
      ['Gradient Boosting Classifier', 'Classification', 'Strong candidate for structured datasets'],
      ['Logistic Regression', 'Classification', 'Interpretable, practical baseline'],
      ['Decision Tree Classifier', 'Classification', 'Easy to explain and visualize']
    ],
    regression: [
      ['Random Forest Regressor', 'Regression', 'Captures nonlinear patterns in tabular data'],
      ['Gradient Boosting Regressor', 'Regression', 'Strong candidate for complex relationships'],
      ['HistGradientBoosting Regressor', 'Regression', 'Efficient option for larger numeric datasets'],
      ['Linear Regression', 'Regression', 'Simple and interpretable baseline']
    ]
  };
  const medals = ['🥇 1','🥈 2','🥉 3','④ 4'];
  targetSelect?.addEventListener('change', () => {
    if (!rows) return;
    rows.replaceChildren();
    demoModels[targetSelect.value].forEach(([model, task, why], index) => {
      const tr = document.createElement('tr');
      [medals[index], model, task, why].forEach((value, cellIndex) => {
        const td = document.createElement('td');
        td.textContent = value;
        if (cellIndex === 0) td.className = 'rank-cell';
        tr.appendChild(td);
      });
      rows.appendChild(tr);
    });
  });
})();
