---
title: PhishLens API
sdk: docker
app_port: 7860
pinned: false
---

# PhishLens API

FastAPI backend for the PhishLens explainable phishing-triage mini-project.

The Space starts with the synthetic demo model when no real model is present. Its scores are a pipeline demonstration, not evidence of real-world detection quality. Do not send real personal email to this public Space.

Health: `/api/health`
Docs: `/docs`

The frontend is deployed separately on Vercel and points at this Space through `VITE_API_BASE_URL`.
