# CleanCraft

CleanCraft is a Flask application that supports an end-to-end dataset preparation flow:

- Generate synthetic datasets (category-based)
- Upload CSV files
- Analyze dataset quality metrics
- Apply configurable cleaning operations
- Get top 4 ML model recommendations (task heuristics)
- View a final report and download cleaned CSV

## Tech stack

- Python
- Flask
- Pandas
- Faker

## Run locally

1. Create/activate your Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python app.py
```

4. Open:

```text
http://127.0.0.1:5000
```

## Main workflow

Upload or generate data, then proceed:

Upload -> Analyze -> Clean -> Recommend -> Report

## Notes

- Cleaned CSV download becomes available after running cleaning at least once.
- PDF report export button is still a placeholder.
- This implementation is intended for local/prototype usage, not production deployment.
