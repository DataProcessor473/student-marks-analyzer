"""
ML Predictions for Student Marks Analyzer.
Uses scikit-learn for grade prediction and at-risk detection.
"""
import os
import json
from pathlib import Path
from datetime import datetime

try:
    import numpy as np
    import joblib
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

GRADE_MODEL_PATH = MODEL_DIR / "grade_predictor.pkl"
RISK_MODEL_PATH  = MODEL_DIR / "risk_classifier.pkl"
META_PATH        = MODEL_DIR / "model_meta.json"


def is_available():
    return ML_AVAILABLE


def is_trained():
    return GRADE_MODEL_PATH.exists() and RISK_MODEL_PATH.exists()


def get_meta():
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text())
        except Exception:
            return {}
    return {}


def _extract_features(rows):
    """
    rows: list of dicts with 'marks', 'subjects', 'attendance_rate', 'assignment_rate'
    Returns (X, y_grade, y_risk)
    """
    X, y_grade, y_risk = [], [], []

    for r in rows:
        marks = r.get("marks") or []
        if not marks:
            continue

        avg = sum(marks) / len(marks)
        high = max(marks)
        low = min(marks)
        spread = high - low
        std = float(np.std(marks)) if len(marks) > 1 else 0.0

        attendance = float(r.get("attendance_rate", 1.0))
        assignments = float(r.get("assignment_rate", 1.0))

        X.append([avg, high, low, spread, std, attendance, assignments, len(marks)])
        y_grade.append(avg)

        # At-risk = average below 45 OR any subject below 30
        at_risk = 1 if (avg < 45 or low < 30) else 0
        y_risk.append(at_risk)

    return np.array(X), np.array(y_grade), np.array(y_risk)


def train_model(training_data):
    """Train grade + risk models. Returns metrics."""
    if not ML_AVAILABLE:
        return {"error": "scikit-learn not installed"}

    X, y_grade, y_risk = _extract_features(training_data)

    if len(X) < 5:
        return {"error": f"Need at least 5 students with marks, got {len(X)}"}

    # Grade regression
    grade_model = RandomForestRegressor(
        n_estimators=100, max_depth=8, random_state=42
    )

    # Risk classification
    risk_model = RandomForestClassifier(
        n_estimators=100, max_depth=6, random_state=42
    )

    # Train grade model with holdout if enough data
    if len(X) >= 10:
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y_grade, test_size=0.2, random_state=42
        )
        grade_model.fit(X_tr, y_tr)
        y_pred = grade_model.predict(X_te)
        mae = float(mean_absolute_error(y_te, y_pred))
        r2 = float(r2_score(y_te, y_pred))
    else:
        grade_model.fit(X, y_grade)
        mae, r2 = 0.0, 1.0

    # Risk model
    risk_model.fit(X, y_risk)
    train_acc = float(accuracy_score(y_risk, risk_model.predict(X)))

    joblib.dump(grade_model, GRADE_MODEL_PATH)
    joblib.dump(risk_model, RISK_MODEL_PATH)

    meta = {
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(X),
        "grade_mae": round(mae, 2),
        "grade_r2": round(r2, 3),
        "risk_accuracy": round(train_acc, 3),
        "features": ["avg", "high", "low", "spread", "std",
                     "attendance", "assignments", "num_subjects"],
    }
    META_PATH.write_text(json.dumps(meta, indent=2))

    return {"ok": True, **meta}


def predict_grade(student_data):
    """Predict next exam score from student marks/attendance."""
    if not ML_AVAILABLE:
        return {"error": "scikit-learn not installed"}
    if not is_trained():
        return {"error": "Model not trained. Call POST /ml/train first."}

    grade_model = joblib.load(GRADE_MODEL_PATH)
    X, _, _ = _extract_features([student_data])

    if len(X) == 0:
        return {"error": "No valid marks data"}

    pred = float(grade_model.predict(X)[0])
    low = max(0, pred - 5)
    high = min(100, pred + 5)

    marks = student_data.get("marks", [])
    if len(marks) >= 2:
        half = len(marks) // 2
        first_half = sum(marks[:half]) / max(1, half)
        second_half = sum(marks[half:]) / max(1, len(marks) - half)
        trend = "improving" if second_half > first_half + 3 else \
                "declining" if second_half < first_half - 3 else "stable"
    else:
        trend = "unknown"

    return {
        "predicted_score": round(pred, 1),
        "confidence_low": round(low, 1),
        "confidence_high": round(high, 1),
        "trend": trend,
        "current_average": round(sum(marks) / len(marks), 1) if marks else 0,
    }


def predict_risk(student_data):
    """Returns at_risk bool + probability."""
    if not ML_AVAILABLE or not is_trained():
        return {"at_risk": False, "probability": 0.0}

    risk_model = joblib.load(RISK_MODEL_PATH)
    X, _, _ = _extract_features([student_data])

    if len(X) == 0:
        return {"at_risk": False, "probability": 0.0}

    prob = float(risk_model.predict_proba(X)[0][1])
    return {
        "at_risk": prob > 0.5,
        "probability": round(prob, 3),
    }


def generate_recommendations(student_data):
    """Return list of recommendation strings."""
    marks = student_data.get("marks", [])
    subjects = student_data.get("subjects", [])
    attendance = float(student_data.get("attendance_rate", 1.0))

    recs = []
    if not marks:
        return ["Not enough data for recommendations."]

    avg = sum(marks) / len(marks)

    # Weakest subject
    if subjects and len(subjects) == len(marks):
        weakest_idx = marks.index(min(marks))
        weakest_subj = subjects[weakest_idx]
        weakest_mark = marks[weakest_idx]

        if weakest_mark < 40:
            recs.append(f"🚨 **{weakest_subj}** is critical ({weakest_mark:.0f}%) — needs immediate focus.")
        elif weakest_mark < 60:
            recs.append(f"📚 **{weakest_subj}** needs improvement ({weakest_mark:.0f}%) — aim for 70%+.")
        elif weakest_mark < 75:
            recs.append(f"💡 Push **{weakest_subj}** to 80%+ to reach distinction.")

        # Strongest subject
        strongest_idx = marks.index(max(marks))
        strongest_subj = subjects[strongest_idx]
        if max(marks) >= 85:
            recs.append(f"🏆 Excelling in **{strongest_subj}** ({max(marks):.0f}%) — consider advanced material.")

    # Attendance
    if attendance < 0.7:
        recs.append(f"📅 Attendance is **{attendance*100:.0f}%** — aim for 85%+ for better outcomes.")
    elif attendance >= 0.9:
        recs.append(f"✅ Attendance is strong ({attendance*100:.0f}%) — keep it up.")

    # Overall
    if avg >= 85:
        recs.append("🌟 Overall performance is excellent — maintain consistency.")
    elif avg >= 70:
        recs.append("📈 Good progress — focus on weakest subject to reach top tier.")
    elif avg >= 50:
        recs.append("⚠️ Average performance — study schedule needs tightening.")
    else:
        recs.append("🚨 Below passing threshold — request tutoring support.")

    return recs
