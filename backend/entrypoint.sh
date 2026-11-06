#!/bin/sh
# If no model is present and PHISHLENS_AUTO_TRAIN_DEMO=true, train the SYNTHETIC demo model so a fresh
# checkout works immediately. Never use that model for real decisions or results.
set -e
MODEL_DIR="${PHISHLENS_MODEL_DIR:-./models}"
if [ ! -f "$MODEL_DIR/active/meta.json" ] && [ "${PHISHLENS_AUTO_TRAIN_DEMO:-false}" = "true" ]; then
  echo "[entrypoint] no model found -> training demo model on SYNTHETIC data"
  python -m training.train --source synthetic --n 2400 --out "$MODEL_DIR" --reports ./reports
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
