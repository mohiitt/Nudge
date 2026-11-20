# Data generator

Produces RavenStack-shaped base data plus synthetic CRM, billing, usage,
support, and intervention tables aligned with `db/singlestore/schema.sql`.

## Run

```bash
# from repo root
python data/generator/generate.py
# or
python -m data.generator.generate
```

Outputs:

- `data/output/*.csv` — full seed set
- `data/fixtures/` — small demo sample + `meta.json`
- `data/raw/ravenstack/` — Kaggle download or synthetic RavenStack CSV

If `KAGGLE_USERNAME` / `KAGGLE_KEY` are missing, synthetic RavenStack is used
automatically. Edge cases: see `EDGE_CASES.md`.
