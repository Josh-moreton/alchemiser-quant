# Environment configuration for DSL strategy files

This project supports listing DSL `.clj` files and their per-file weights via environment variables. These variables are used both locally (from `.env`) and in AWS Lambda (via CloudFormation parameters in `template.yaml`).

## Recommended formats

You can use any of the following formats for convenience. The config loader normalizes them automatically.

- JSON (preferred for parity with the SAM template)
  - `STRATEGY__DSL_FILES=["1-KMLM.clj","2-Nuclear.clj"]`
  - `STRATEGY__DSL_ALLOCATIONS={"1-KMLM.clj":0.6,"2-Nuclear.clj":0.4}`
- CSV / newline separated (handy for quick edits)
  - `STRATEGY__DSL_FILES=1-KMLM.clj,2-Nuclear.clj`
  - `STRATEGY__DSL_ALLOCATIONS=1-KMLM.clj=0.6,2-Nuclear.clj=0.4`

Notes

- Whitespace and surrounding quotes are tolerated.
- Weights are normalized downstream; they don’t need to sum to exactly 1.0 but should be close.

## AWS Lambda specifics

CloudFormation parameters are strings, so JSON must be passed as a single line. The deployment script now ensures this by:

- Minifying JSON values found in `.env` (even if you format them across multiple lines) using `scripts/extract_env_json.py`.
- Passing the result safely to `sam deploy` parameter overrides.

If you see only `{` or `[` in the Lambda console for these variables, it means the value wasn’t quoted/minified correctly. Re-deploy with the updated script, or ensure values are single-line JSON strings.

## Local usage from `.env`

Keep either JSON or CSV forms. Examples:

```
# JSON
STRATEGY__DSL_FILES=["1-KMLM.clj","2-Nuclear.clj","6-TQQQ-FLT.clj"]
STRATEGY__DSL_ALLOCATIONS={"1-KMLM.clj":0.5,"2-Nuclear.clj":0.25,"6-TQQQ-FLT.clj":0.25}

# or CSV
STRATEGY__DSL_FILES=1-KMLM.clj,2-Nuclear.clj,6-TQQQ-FLT.clj
STRATEGY__DSL_ALLOCATIONS=1-KMLM.clj=0.5,2-Nuclear.clj=0.25,6-TQQQ-FLT.clj=0.25
```

## Future alternatives (optional)

For larger configurations you can:

- Store a JSON config in S3 and reference it with a single env var (e.g., `STRATEGY__DSL_CONFIG_S3=s3://bucket/path.json`).
- Use SSM Parameter Store (StringList for files + String for JSON allocations) and have the function fetch them at cold start.

Both options trade simplicity for centralization and auditability.
