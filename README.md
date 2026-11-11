<<<<<<< HEAD
# CleanCraft — UI V2 (frontend first)

A Flask-powered, **UI-only** version of the approved Neo-Brutalism website. This is deliberately frontend only: **there is no data upload, Faker generation, actual cleaning, vector similarity execution, model training, or PDF/CSV export yet.** All metrics and recommendations are labeled sample/demo information.

## How to run on Windows

1. Open the `CleanCraft_UI_V2` folder in VS Code (not its `templates` subfolder).
2. In the VS Code terminal, run:
   ```powershell
   python -m pip install -r requirements.txt
   python app.py
   ```
3. Open **http://127.0.0.1:5000**.

Do **not** use `python -m http.server` here: the HTML contains Flask/Jinja URLs.

## Pages

- **Home:** headline, two paths, four feature cards, how it works, reasons to choose CleanCraft.
- **Generate:** category picker, record count, optional locality, illustrative output preview.
- **Upload:** drag/drop file selection with no file-size text.
- **Analysis:** exactly five metric cards, without data preview or column information tables.
- **Cleaning:** selected cleaning operations with an inline optional similarity check. No separate vector-similarity page.
- **Recommendations:** top four illustrative ranked models, sample target selector.
- **Report:** illustrative cleaning summary, models, download buttons marked unavailable pending backend.

Workflow: **Upload → Analyze → Clean → Recommend → Report**. Generator is a separate optional starting path.

## Integration later

Keep `templates/` and `static/` intact. Replace the demo values with real values returned by backend APIs only after processing succeeds. When ready, implement secure upload validation, safe data-cleaning decisions, similarity suggestions for approval, chosen-target-aware model recommendation, and actual downloads.
=======
# CleanCraft
An end-to-end data platform that automatically cleans messy datasets, generates synthetic data, and recommends optimal machine learning models.
>>>>>>> 486374ffea53bf2571f4d4ab407e0a59455483b1
