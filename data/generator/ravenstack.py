"""Download RavenStack from Kaggle or synthesize RavenStack-shaped CSVs."""

from __future__ import annotations

import csv
import os
import random
from pathlib import Path

from .constants import (
    DEFAULT_N_ACCOUNTS,
    DEFAULT_SEED,
    INDUSTRIES,
    KAGGLE_DATASET,
    PLAN_TIERS,
    RAW_DIR,
)


RAVEN_COLUMNS = [
    "customer_id",
    "company_name",
    "industry",
    "plan",
    "mrr",
    "seats",
    "tenure_months",
    "churned",
    "churn_reason",
    "signup_date",
]


def try_download_kaggle(dest: Path = RAW_DIR) -> Path | None:
    dest.mkdir(parents=True, exist_ok=True)
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        return None
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi  # type: ignore

        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(KAGGLE_DATASET, path=str(dest), unzip=True)
        csvs = list(dest.glob("*.csv"))
        return csvs[0] if csvs else None
    except Exception as exc:  # noqa: BLE001
        print(f"[ravenstack] Kaggle download failed: {exc}")
        return None


def synthesize_ravenstack(
    path: Path,
    n: int = DEFAULT_N_ACCOUNTS,
    seed: int = DEFAULT_SEED,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RAVEN_COLUMNS)
        writer.writeheader()
        for i in range(n):
            churned = rng.random() < 0.18
            writer.writerow(
                {
                    "customer_id": f"rs_{i:04d}",
                    "company_name": f"Company {i:04d}",
                    "industry": rng.choice(INDUSTRIES),
                    "plan": rng.choice(PLAN_TIERS),
                    "mrr": round(rng.uniform(200, 25000), 2),
                    "seats": rng.randint(3, 500),
                    "tenure_months": rng.randint(1, 48),
                    "churned": int(churned),
                    "churn_reason": rng.choice(["price", "product", "support", ""]) if churned else "",
                    "signup_date": f"2023-{(i % 12) + 1:02d}-15",
                }
            )
    return path


def load_or_create_ravenstack(n: int = DEFAULT_N_ACCOUNTS, seed: int = DEFAULT_SEED) -> Path:
    existing = list(RAW_DIR.glob("*.csv")) if RAW_DIR.exists() else []
    if existing:
        return existing[0]
    downloaded = try_download_kaggle()
    if downloaded:
        return downloaded
    out = RAW_DIR / "ravenstack_synthetic.csv"
    print("[ravenstack] No Kaggle credentials — writing synthetic RavenStack CSV")
    return synthesize_ravenstack(out, n=n, seed=seed)
