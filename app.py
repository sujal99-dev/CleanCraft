"""CleanCraft backend Flask app.

Provides:
- Synthetic dataset generation
- CSV upload and analysis
- Data cleaning operations
- Heuristic ML model recommendations
- Final report and cleaned CSV download
"""

from __future__ import annotations

import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from faker import Faker
from fpdf import FPDF
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cleancraft-dev-secret")

DATA_ROOT = Path(app.instance_path) / "workspace_data"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
faker = Faker()

DEFAULT_CLEANING_OPS = [
    "handle_missing",
    "remove_duplicates",
    "correct_types",
    "clean_mixed_values",
    "standardize_text",
    "flag_invalid",
    "detect_outliers",
]

MODEL_LIBRARY = {
    "classification": [
        (
            "Random Forest Classifier",
            "Classification",
            "Robust on mixed tabular features and nonlinear patterns.",
        ),
        (
            "Gradient Boosting Classifier",
            "Classification",
            "Strong performer for structured feature interactions.",
        ),
        (
            "Logistic Regression",
            "Classification",
            "Interpretable baseline and fast to validate.",
        ),
        (
            "Decision Tree Classifier",
            "Classification",
            "Simple to visualize and explain to stakeholders.",
        ),
    ],
    "regression": [
        (
            "Random Forest Regressor",
            "Regression",
            "Captures nonlinear relationships with low preprocessing burden.",
        ),
        (
            "Gradient Boosting Regressor",
            "Regression",
            "Often delivers high accuracy on tabular regression tasks.",
        ),
        (
            "HistGradientBoosting Regressor",
            "Regression",
            "Efficient for larger datasets with numerical features.",
        ),
        (
            "Linear Regression",
            "Regression",
            "Fast, interpretable baseline for trend estimation.",
        ),
    ],
}

OPERATION_LABELS = {
    "handle_missing": "Handle missing values",
    "remove_duplicates": "Remove duplicate rows",
    "correct_types": "Correct data types",
    "clean_mixed_values": "Clean mixed values",
    "standardize_text": "Standardize text categories",
    "flag_invalid": "Flag invalid values",
    "detect_outliers": "Detect potential outliers",
}


def _session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid4().hex
        session["sid"] = sid
    return sid


def _session_dir() -> Path:
    d = DATA_ROOT / _session_id()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _uploaded_path() -> Path:
    return _session_dir() / "uploaded.csv"


def _cleaned_path() -> Path:
    return _session_dir() / "cleaned.csv"


def _to_int(value: Any) -> int:
    if pd.isna(value):
        return 0
    try:
        return int(value)
    except Exception:
        return 0


def _load_frame(prefer_cleaned: bool = False) -> pd.DataFrame | None:
    path = _cleaned_path() if prefer_cleaned and _cleaned_path().exists() else _uploaded_path()
    if not path.exists():
        return None
    return pd.read_csv(path)


def _save_frame(df: pd.DataFrame, cleaned: bool = False) -> None:
    target = _cleaned_path() if cleaned else _uploaded_path()
    df.to_csv(target, index=False)


def _dataset_metrics(df: pd.DataFrame) -> dict[str, int]:
    dtype_count = int(df.dtypes.astype(str).nunique())
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "data_types": dtype_count,
    }


def _parse_series_to_numeric_if_mostly_numeric(series: pd.Series) -> tuple[pd.Series, bool]:
    if pd.api.types.is_numeric_dtype(series):
        return series, False

    sample = series.dropna().astype(str)
    if sample.empty:
        return series, False

    stripped = sample.str.replace(r"[^0-9.\-]", "", regex=True)
    converted = pd.to_numeric(stripped, errors="coerce")
    ratio = converted.notna().mean()
    if ratio >= 0.7:
        full = pd.to_numeric(series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")
        return full, True
    return series, False


def _clean_dataset(df: pd.DataFrame, operations: list[str]) -> tuple[pd.DataFrame, dict[str, int]]:
    cleaned = df.copy()
    summary = {
        "missing_values_addressed": 0,
        "duplicate_rows_removed": 0,
        "data_types_corrected": 0,
        "inconsistent_values_handled": 0,
        "invalid_values_flagged": 0,
        "outliers_flagged": 0,
    }

    if "remove_duplicates" in operations:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        summary["duplicate_rows_removed"] = before - len(cleaned)

    if "clean_mixed_values" in operations:
        mixed_fix_count = 0
        for col in cleaned.columns:
            series = cleaned[col]
            if pd.api.types.is_object_dtype(series):
                stripped = series.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
                mixed_fix_count += int((series.fillna("") != stripped.fillna("")).sum())
                cleaned[col] = stripped
        summary["inconsistent_values_handled"] += mixed_fix_count

    if "correct_types" in operations:
        corrected = 0
        for col in cleaned.columns:
            converted, was_converted = _parse_series_to_numeric_if_mostly_numeric(cleaned[col])
            if was_converted:
                cleaned[col] = converted
                corrected += 1
            else:
                try:
                    dt = pd.to_datetime(cleaned[col], errors="coerce")
                    if dt.notna().mean() >= 0.8:
                        cleaned[col] = dt
                        corrected += 1
                except Exception:
                    pass
        summary["data_types_corrected"] = corrected

    if "standardize_text" in operations:
        standardized = 0
        for col in cleaned.columns:
            if pd.api.types.is_object_dtype(cleaned[col]):
                before = cleaned[col].copy()
                cleaned[col] = cleaned[col].astype(str).str.strip().str.title()
                standardized += int((before.fillna("") != cleaned[col].fillna("")).sum())
        summary["inconsistent_values_handled"] += standardized

    if "handle_missing" in operations:
        before_missing = int(cleaned.isna().sum().sum())
        for col in cleaned.columns:
            if cleaned[col].isna().sum() == 0:
                continue
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                cleaned[col] = cleaned[col].fillna(cleaned[col].median())
            else:
                mode = cleaned[col].mode(dropna=True)
                fill_val = mode.iloc[0] if not mode.empty else "Unknown"
                cleaned[col] = cleaned[col].fillna(fill_val)
        after_missing = int(cleaned.isna().sum().sum())
        summary["missing_values_addressed"] = before_missing - after_missing

    if "flag_invalid" in operations:
        invalid_count = 0
        for col in cleaned.columns:
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                invalid_count += int((cleaned[col] < 0).sum())
                cleaned.loc[cleaned[col] < 0, col] = pd.NA
        summary["invalid_values_flagged"] = invalid_count

    if "detect_outliers" in operations:
        outliers = 0
        for col in cleaned.select_dtypes(include=["number"]).columns:
            q1 = cleaned[col].quantile(0.25)
            q3 = cleaned[col].quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers += int(((cleaned[col] < lower) | (cleaned[col] > upper)).sum())
        summary["outliers_flagged"] = outliers

    # A second pass resolves invalid negative values turned into NA in flagging stage.
    if "handle_missing" in operations:
        after_flag_missing = int(cleaned.isna().sum().sum())
        if after_flag_missing > 0:
            for col in cleaned.columns:
                if cleaned[col].isna().sum() == 0:
                    continue
                if pd.api.types.is_numeric_dtype(cleaned[col]):
                    cleaned[col] = cleaned[col].fillna(cleaned[col].median())
                else:
                    mode = cleaned[col].mode(dropna=True)
                    fill_val = mode.iloc[0] if not mode.empty else "Unknown"
                    cleaned[col] = cleaned[col].fillna(fill_val)

    return cleaned, summary


def _guess_target_column(df: pd.DataFrame) -> str | None:
    for name in ["target", "label", "class", "result", "price", "y"]:
        if name in [c.lower() for c in df.columns]:
            for col in df.columns:
                if col.lower() == name:
                    return col
    if len(df.columns) > 0:
        return df.columns[-1]
    return None


def _target_task(df: pd.DataFrame, target_col: str | None) -> str:
    if not target_col or target_col not in df.columns:
        return "classification"
    series = df[target_col]
    if pd.api.types.is_numeric_dtype(series):
        unique = series.nunique(dropna=True)
        if unique > 12:
            return "regression"
    return "classification"


def _make_house_price(records: int, locality: str | None) -> pd.DataFrame:
    city = locality.strip() if locality else "Kolkata"
    neighborhoods = [
        "Salt Lake",
        "New Town",
        "Ballygunge",
        "Tollygunge",
        "Behala",
        "Dum Dum",
    ]
    rows = []
    for _ in range(records):
        area = faker.random_int(min=550, max=3600)
        beds = faker.random_int(min=1, max=5)
        baths = faker.random_int(min=1, max=4)
        age = faker.random_int(min=0, max=28)
        dist = round(faker.pyfloat(min_value=0.5, max_value=22.0, right_digits=1), 1)
        price = int(2200 * area + 450000 * beds + 180000 * baths - 15000 * age - 12000 * dist)
        rows.append(
            {
                "city": city,
                "locality": faker.random_element(neighborhoods),
                "area_sqft": area,
                "bedrooms": beds,
                "bathrooms": baths,
                "property_age_years": age,
                "distance_to_centre_km": dist,
                "price_inr": max(price, 1500000),
            }
        )
    return pd.DataFrame(rows)


def _make_student_performance(records: int, locality: str | None) -> pd.DataFrame:
    school = locality.strip() if locality else "Central High"
    rows = []
    for _ in range(records):
        attendance = faker.random_int(min=60, max=100)
        study = faker.random_int(min=1, max=8)
        sleep = faker.random_int(min=4, max=9)
        score = max(min(int(0.4 * attendance + 5 * study + 2 * sleep + faker.random_int(-12, 12)), 100), 0)
        rows.append(
            {
                "school": school,
                "age": faker.random_int(min=15, max=19),
                "attendance_pct": attendance,
                "study_hours_per_day": study,
                "sleep_hours": sleep,
                "internet_access": faker.random_element(["Yes", "No"]),
                "final_score": score,
                "pass": "Yes" if score >= 40 else "No",
            }
        )
    return pd.DataFrame(rows)


def _make_email_spam(records: int) -> pd.DataFrame:
    rows = []
    for _ in range(records):
        links = faker.random_int(min=0, max=8)
        caps_ratio = round(faker.pyfloat(min_value=0.0, max_value=0.9, right_digits=2), 2)
        exclam = faker.random_int(min=0, max=7)
        spam = "Spam" if (links + exclam > 7 or caps_ratio > 0.45) else "Ham"
        rows.append(
            {
                "sender_domain": faker.free_email_domain(),
                "subject_length": faker.random_int(min=12, max=95),
                "contains_offer": faker.random_element([0, 1]),
                "link_count": links,
                "caps_ratio": caps_ratio,
                "exclamation_count": exclam,
                "label": spam,
            }
        )
    return pd.DataFrame(rows)


def _make_generic(records: int, category: str, locality: str | None) -> pd.DataFrame:
    location = locality.strip() if locality else faker.city()
    rows = []
    for _ in range(records):
        rows.append(
            {
                "category": category,
                "record_id": faker.uuid4(),
                "location": location,
                "score": faker.random_int(min=1, max=100),
                "amount": round(faker.pyfloat(min_value=100.0, max_value=90000.0, right_digits=2), 2),
                "status": faker.random_element(["Low", "Medium", "High"]),
                "created_on": faker.date_between(start_date="-2y", end_date="today"),
            }
        )
    return pd.DataFrame(rows)


def _build_synthetic_dataset(category: str, records: int, locality: str | None) -> pd.DataFrame:
    if category == "House Price":
        return _make_house_price(records, locality)
    if category == "Student Performance":
        return _make_student_performance(records, locality)
    if category == "Email Spam":
        return _make_email_spam(records)
    return _make_generic(records, category, locality)


def _pdf_bytes(
    metrics: dict[str, int],
    summary: dict[str, int],
    selected_ops: list[str],
    models: list[list[str] | tuple[str, str, str]],
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    content_w = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "CleanCraft Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, "Dataset overview, cleaning summary, and model recommendations.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Dataset Overview", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for label, key in [
        ("Rows", "rows"),
        ("Columns", "cols"),
        ("Missing values", "missing_values"),
        ("Duplicate rows", "duplicate_rows"),
        ("Data types", "data_types"),
    ]:
        pdf.cell(0, 7, f"- {label}: {metrics.get(key, 0)}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Cleaning Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for label, key in [
        ("Missing values addressed", "missing_values_addressed"),
        ("Duplicate rows removed", "duplicate_rows_removed"),
        ("Data types corrected", "data_types_corrected"),
        ("Inconsistent values handled", "inconsistent_values_handled"),
        ("Invalid values flagged", "invalid_values_flagged"),
        ("Outliers flagged", "outliers_flagged"),
    ]:
        pdf.cell(0, 7, f"- {label}: {summary.get(key, 0)}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Applied Operations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    if selected_ops:
        for op in selected_ops:
            pdf.cell(0, 7, f"- {OPERATION_LABELS.get(op, op)}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 7, "- No explicit operations selected.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Top Model Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for index, model in enumerate(models[:4], start=1):
        model_name = model[0]
        model_task = model[1] if len(model) > 1 else ""
        reason = model[2] if len(model) > 2 else ""
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(content_w, 7, f"{index}. {model_name} ({model_task}) - {reason}")

    return bytes(pdf.output(dest="S"))


@app.route("/")
@app.route("/index.html")
def home():
    return render_template("index.html", page="home")


@app.route("/generate", methods=["GET", "POST"])
@app.route("/generate.html", methods=["GET", "POST"])
def generate():
    preview_rows: list[dict[str, Any]] = []
    generated_columns: list[str] = []
    generated_meta: dict[str, Any] = {}
    selected_category = request.form.get("category", "House Price")
    selected_records = request.form.get("records", "5000")
    selected_locality = request.form.get("locality", "")

    if request.method == "POST":
        try:
            records = int(selected_records)
            if records < 1 or records > 100000:
                raise ValueError
        except ValueError:
            flash("Record count must be between 1 and 100000.", "error")
            return redirect(url_for("generate"))

        dataset = _build_synthetic_dataset(selected_category, records, selected_locality)
        _save_frame(dataset, cleaned=False)
        if _cleaned_path().exists():
            _cleaned_path().unlink()

        metrics = _dataset_metrics(dataset)
        session["analysis_metrics"] = metrics
        session["last_clean_summary"] = {
            "missing_values_addressed": 0,
            "duplicate_rows_removed": 0,
            "data_types_corrected": 0,
            "inconsistent_values_handled": 0,
            "invalid_values_flagged": 0,
            "outliers_flagged": 0,
        }

        preview_rows = dataset.head(6).fillna("").to_dict(orient="records")
        generated_columns = list(dataset.columns)
        generated_meta = {
            "category": selected_category,
            "records": metrics["rows"],
            "locality": selected_locality.strip() or "N/A",
        }
        flash("Synthetic dataset generated and loaded into the workflow.", "success")

    return render_template(
        "generate.html",
        page="generate",
        preview_rows=preview_rows,
        generated_columns=generated_columns,
        generated_meta=generated_meta,
        selected_category=selected_category,
        selected_records=selected_records,
        selected_locality=selected_locality,
    )


@app.route("/upload", methods=["GET", "POST"])
@app.route("/upload.html", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Please choose a CSV file first.", "error")
            return redirect(url_for("upload"))
        if not file.filename.lower().endswith(".csv"):
            flash("Only .csv files are supported.", "error")
            return redirect(url_for("upload"))

        try:
            df = pd.read_csv(file)
        except Exception as exc:
            flash(f"Unable to read CSV: {exc}", "error")
            return redirect(url_for("upload"))

        _save_frame(df, cleaned=False)
        if _cleaned_path().exists():
            _cleaned_path().unlink()

        session["analysis_metrics"] = _dataset_metrics(df)
        session["last_clean_summary"] = {
            "missing_values_addressed": 0,
            "duplicate_rows_removed": 0,
            "data_types_corrected": 0,
            "inconsistent_values_handled": 0,
            "invalid_values_flagged": 0,
            "outliers_flagged": 0,
        }
        session["uploaded_filename"] = file.filename
        flash(f"Uploaded {file.filename} successfully.", "success")
        return redirect(url_for("analysis"))

    uploaded_name = session.get("uploaded_filename")
    return render_template("upload.html", page="upload", uploaded_name=uploaded_name)


@app.route("/analysis")
@app.route("/analysis.html")
def analysis():
    df = _load_frame(prefer_cleaned=False)
    if df is None:
        flash("Upload or generate a dataset first.", "error")
        return redirect(url_for("upload"))

    metrics = _dataset_metrics(df)
    session["analysis_metrics"] = metrics
    return render_template("analysis.html", page="analysis", metrics=metrics)


@app.route("/cleaning", methods=["GET", "POST"])
@app.route("/cleaning.html", methods=["GET", "POST"])
def cleaning():
    df = _load_frame(prefer_cleaned=False)
    if df is None:
        flash("Upload or generate a dataset first.", "error")
        return redirect(url_for("upload"))

    selected_ops = request.form.getlist("operations") or DEFAULT_CLEANING_OPS
    summary = session.get("last_clean_summary") or {
        "missing_values_addressed": 0,
        "duplicate_rows_removed": 0,
        "data_types_corrected": 0,
        "inconsistent_values_handled": 0,
        "invalid_values_flagged": 0,
        "outliers_flagged": 0,
    }

    if request.method == "POST":
        cleaned, summary = _clean_dataset(df, selected_ops)
        _save_frame(cleaned, cleaned=True)
        session["last_clean_summary"] = summary
        session["cleaning_operations"] = selected_ops
        flash("Dataset cleaned with selected operations.", "success")

    return render_template(
        "cleaning.html",
        page="cleaning",
        selected_ops=selected_ops,
        summary=summary,
    )


@app.route("/recommendations", methods=["GET", "POST"])
@app.route("/recommendations.html", methods=["GET", "POST"])
def recommendations():
    df = _load_frame(prefer_cleaned=True)
    if df is None:
        flash("Upload or generate a dataset first.", "error")
        return redirect(url_for("upload"))

    columns = list(df.columns)
    target_column = request.form.get("target_column") if request.method == "POST" else None
    target_column = target_column or session.get("selected_target") or _guess_target_column(df)
    task = _target_task(df, target_column)
    ranked_models = MODEL_LIBRARY[task]

    session["selected_target"] = target_column
    session["recommended_models"] = [list(row) for row in ranked_models]
    session["recommendation_task"] = task

    return render_template(
        "recommendations.html",
        page="recommendations",
        target_column=target_column,
        target_columns=columns,
        task=task,
        models=ranked_models,
    )


@app.route("/report")
@app.route("/report.html")
def report():
    uploaded_df = _load_frame(prefer_cleaned=False)
    if uploaded_df is None:
        flash("Upload or generate a dataset first.", "error")
        return redirect(url_for("upload"))

    cleaned_df = _load_frame(prefer_cleaned=True)
    final_df = cleaned_df if cleaned_df is not None else uploaded_df
    metrics = _dataset_metrics(final_df)

    summary = session.get("last_clean_summary") or {
        "missing_values_addressed": 0,
        "duplicate_rows_removed": 0,
        "data_types_corrected": 0,
        "inconsistent_values_handled": 0,
        "invalid_values_flagged": 0,
        "outliers_flagged": 0,
    }
    selected_ops = session.get("cleaning_operations") or DEFAULT_CLEANING_OPS
    models = session.get("recommended_models") or [list(row) for row in MODEL_LIBRARY["classification"]]

    return render_template(
        "report.html",
        page="report",
        metrics=metrics,
        summary=summary,
        selected_ops=selected_ops,
        models=models,
        can_download=cleaned_df is not None,
        can_export_pdf=True,
    )


@app.route("/download/cleaned.csv")
def download_cleaned_csv():
    cleaned = _cleaned_path()
    if not cleaned.exists():
        flash("Run cleaning first to download the cleaned dataset.", "error")
        return redirect(url_for("cleaning"))
    return send_file(cleaned, as_attachment=True, download_name="cleaned_dataset.csv", mimetype="text/csv")


@app.route("/download/report.pdf")
def download_report_pdf():
    uploaded_df = _load_frame(prefer_cleaned=False)
    if uploaded_df is None:
        flash("Upload or generate a dataset first.", "error")
        return redirect(url_for("upload"))

    cleaned_df = _load_frame(prefer_cleaned=True)
    final_df = cleaned_df if cleaned_df is not None else uploaded_df
    metrics = _dataset_metrics(final_df)

    summary = session.get("last_clean_summary") or {
        "missing_values_addressed": 0,
        "duplicate_rows_removed": 0,
        "data_types_corrected": 0,
        "inconsistent_values_handled": 0,
        "invalid_values_flagged": 0,
        "outliers_flagged": 0,
    }
    selected_ops = session.get("cleaning_operations") or DEFAULT_CLEANING_OPS
    models = session.get("recommended_models") or [list(row) for row in MODEL_LIBRARY["classification"]]

    pdf_data = _pdf_bytes(metrics=metrics, summary=summary, selected_ops=selected_ops, models=models)
    return send_file(
        BytesIO(pdf_data),
        as_attachment=True,
        download_name="cleancraft_report.pdf",
        mimetype="application/pdf",
    )


@app.template_filter("pretty")
def pretty(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{int(value):,}"
    return str(value)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
