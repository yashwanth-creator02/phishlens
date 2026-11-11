# Released models

This directory holds the model the backend serves. It is copied into the Docker image as
`/app/models/active/`, so anything placed here ships with every deployment.

## What may go in here

`model/`, a directory produced by `python -m training.train` (the four files `model.joblib`,
`calibrator.joblib`, `background.npy`, `meta.json`) plus a `release.json` note. The Docker image
copies `model/` to `/app/models/active/`, so this directory holds exactly one released model.

## The gate

This repository is public. A model that ships here must contain no personal data, so a model
cannot be copied into this directory by hand. Run the release script, which audits the candidate
first and refuses to copy anything that fails:

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.release_model --model models\active --mailbox "data\raw\mailbox"
```

The audit reads the sender domains, email addresses and distinctive subject words out of the
owner's mailbox, then searches every file of the candidate for them, in plain text, UTF-16,
gzip and base64. Any hit refuses the release.

A model fitted on the owner's own mail additionally needs `--allow-personal-data`, because it is
derived from private data even when no string of it survives in the artifact. That flag is the
owner's explicit decision; it is not a technical check.

## Without a release

The Docker image falls back to training the synthetic demo model, so a fresh checkout still starts
and passes its health check. The demo model is a pipeline demonstration, not a result.
