from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "ml" / "outputs"


# ============================================================
# HELPERS
# ============================================================

def _read_csv(filename: str) -> pd.DataFrame:
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"ML evaluation file not found: {path}"
        )

    return pd.read_csv(path)


# ============================================================
# ML EVALUATION
# ============================================================

def get_model_evaluation() -> dict:
    """
    Load real ML evaluation artifacts generated during training.

    These results are used by the AgentReady dashboard to explain
    model quality, model selection, calibration, and generalization.
    """

    # --------------------------------------------------------
    # 1. Final model performance
    # --------------------------------------------------------

    final_summary = _read_csv(
        "regularized_final_model_summary.csv"
    )

    final = final_summary.iloc[0]

    # --------------------------------------------------------
    # 2. Model comparison
    # --------------------------------------------------------

    model_tuning = _read_csv(
        "v2_model_tuning_results.csv"
    )

    model_comparison = []

    for _, row in model_tuning.iterrows():
        model_comparison.append(
            {
                "model": row["model"],
                "accuracy": float(row["accuracy_mean"]),
                "precision": float(row["precision_mean"]),
                "recall": float(row["recall_mean"]),
                "f1": float(row["f1_mean"]),
                "roc_auc": float(row["roc_auc_mean"]),
                "pr_auc": float(row["pr_auc_mean"]),
                "brier_score": float(row["brier_score_mean"]),
                "roc_auc_gap": float(row["roc_auc_gap"]),
            }
        )

    # --------------------------------------------------------
    # 3. Probability calibration
    # --------------------------------------------------------

    calibration_df = _read_csv(
        "v2_calibration.csv"
    )

    calibration = []

    for _, row in calibration_df.iterrows():
        calibration.append(
            {
                "probability_bin": row["probability_bin"],
                "samples": int(row["samples"]),
                "predicted_probability": float(
                    row["predicted_probability"]
                ),
                "actual_recovery_rate": float(
                    row["actual_recovery_rate"]
                ),
            }
        )

    # --------------------------------------------------------
    # 4. Final response
    # --------------------------------------------------------

    return {
        "success": True,

        "model": {
            "name": "Logistic Regression",
            "C": float(final["C"]),
            "feature_count": int(final["feature_count"]),
        },

        "final_test": {
            "accuracy": float(final["final_test_accuracy"]),
            "precision": float(final["final_test_precision"]),
            "recall": float(final["final_test_recall"]),
            "f1": float(final["final_test_f1"]),
            "roc_auc": float(final["final_test_roc_auc"]),
            "pr_auc": float(final["final_test_pr_auc"]),
            "brier_score": float(final["final_test_brier"]),
        },

        "cross_validation": {
            "accuracy": float(final["cv_accuracy"]),
            "precision": float(final["cv_precision"]),
            "recall": float(final["cv_recall"]),
            "f1": float(final["cv_f1"]),
            "roc_auc": float(final["cv_roc_auc"]),
            "pr_auc": float(final["cv_pr_auc"]),
            "brier_score": float(final["cv_brier"]),
            "train_cv_gap": float(final["train_cv_gap"]),
        },

        "model_comparison": model_comparison,

        "calibration": calibration,

        "evaluation_note": (
            "Evaluation is based on synthetic/demo training data. "
            "Production performance may differ."
        ),
    }