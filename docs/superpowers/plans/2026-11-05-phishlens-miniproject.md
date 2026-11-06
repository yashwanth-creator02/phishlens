# PhishLens Mini-Project Delivery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** Ship a free-tier, multi-user, explainable phishing triage app with real-data evaluation, Supabase Auth and Postgres, a Vercel frontend, a Hugging Face Space backend, and a complete frontend surface.

**Architecture:** React/Vite SPA on Vercel calls a FastAPI container on a public Hugging Face Space. Supabase provides Auth and Postgres. The model is trained offline and baked into the Space image. Upload is primary; Gmail IMAP is a stretch.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, scikit-learn, XGBoost, SHAP, Supabase Auth/Postgres, React 18, TypeScript, Vite 5, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-11-05-phishlens-miniproject-scope-design.md`

## Global Constraints

- Free tiers only. No credit card. No paid service.
- Keep the GitHub repository private until submission.
- Never commit raw corpora, `.env` files, credentials, or real email.
- Scope every query and API route to the authenticated `user_id`.
- Do not claim real-world quality from the synthetic model.
- No emojis, pill badges, or `transition: all`.
- Backend: `cd backend; .\.venv\Scripts\python.exe -m pytest -q`.
- Frontend: `cd frontend; npm run build; npm run test`.

## Review Focus

- A first-time sender must not be scored as if it had history.
- A second user must never see the first user's case or stored email.
- A missing or expired token must return `401`, not an empty list.
- An oversized upload or webhook must be rejected before buffering.
- A deleted case must remove features, explanations, and stored email.

### Task 1: Supabase schema and RLS verification

**Files:**
- Create: `supabase/migrations/0002_auth_hardening.sql`
- Create: `backend/scripts/verify_rls.py`
- Create: `backend/tests/test_rls_contract.py`
- Modify: `docs/10-security.md`

**Interfaces:**
- `verify_rls.py` takes two user JWTs and two analysis IDs, then asserts each token sees only its own row.
- `test_rls_contract.py` skips unless `SUPABASE_URL` and two test JWTs are set.

- [ ] **Step 1: Write the contract test**

```python
def test_rls_hides_other_users_case(client, user_a_token, analysis_b):
    r = client.get(f"/rest/v1/analyses?id=eq.{analysis_b}", headers={"apikey": ANON, "Authorization": f"Bearer {user_a_token}"})
    assert r.json() == []
```

- [ ] **Step 2: Run it and confirm the skip or failure**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_rls_contract.py -q`
Expected: skipped without credentials, or failure before policies exist.

- [ ] **Step 3: Add the migration**

Keep `user_id = auth.uid()::text` policies. Add an index on every child table through `analysis_id`. Add a comment that the backend uses the service role and therefore must scope every query itself; RLS protects direct client access only.

- [ ] **Step 4: Run the contract test with credentials**

Run: `cd backend; $env:SUPABASE_URL="..."; .\.venv\Scripts\python.exe -m pytest tests/test_rls_contract.py -q`
Expected: pass; user A sees zero rows for user B.

- [x] **Step 5: Commit**

```bash
git add supabase backend/scripts backend/tests docs/10-security.md
git commit -m "feat: verify Supabase row isolation"
```


### Task 2: Real-data evaluation pipeline

**Files:**
- Create: `backend/training/download_datasets.py`
- Create: `backend/training/evaluate.py`
- Create: `backend/tests/test_evaluate.py`
- Create: `docs/datasets/README.md`
- Modify: `backend/training/corpus.py`

**Interfaces:**
- `download_datasets.py` writes `backend/data/raw/<name>/` and a manifest with counts and SHA-256.
- `evaluate.py::run_evaluation(phish_dir: Path, ham_dir: Path, out: Path) -> dict` writes `reports/evaluation.json` and `reports/evaluation.md`.
- Returns keys: `n_train`, `n_test`, `precision`, `recall`, `f1`, `pr_auc`, `fpr_at_threshold`, `cold_start_f1`.

- [ ] **Step 1: Write the failing test**

```python
def test_evaluation_uses_grouped_split(tmp_path):
    report = run_evaluation(mini_phish_dir, mini_ham_dir, tmp_path)
    assert report["n_test"] > 0
    assert "cold_start_f1" in report
    assert report["split_unit"] == "campaign_or_sender"
```

- [ ] **Step 2: Run it and confirm failure**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_evaluate.py -q`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement download and evaluation**

Use Nazario for phishing and SpamAssassin for ham. Dedupe by Message-ID and body hash. Group phishing by campaign or URL host, ham by sender. Report random and grouped results; grouped is primary.

- [ ] **Step 4: Run the test and the full suite**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest -q`
Expected: all tests pass.

- [x] **Step 5: Commit**

```bash
git add backend/training backend/tests docs/datasets
git commit -m "feat: add grouped real-data evaluation"
```

### Task 3: Supabase auth and Postgres serving

**Files:**
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/db/session.py`
- Create: `backend/tests/test_auth_supabase.py`
- Modify: `backend/requirements.txt`

**Interfaces:**
- `verify_supabase_token(token: str, settings: Settings) -> str` returns the `sub` claim or raises `401`.
- `get_current_user` returns `UserContext(user_id: str)`.
- Config adds `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `SUPABASE_JWKS_URL`.

- [ ] **Step 1: Write the failing tests**

```python
def test_missing_token_returns_401(client):
    assert client.get("/api/analyses").status_code == 401

def test_expired_token_returns_401(client, expired_token):
    assert client.get("/api/analyses", headers=auth(expired_token)).status_code == 401
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_auth_supabase.py -q`
Expected: `401` assertions fail.

- [ ] **Step 3: Implement verification**

Use `PyJWT` HS256 with `SUPABASE_JWT_SECRET` when set. Otherwise fetch JWKS from `SUPABASE_JWKS_URL` with `PyJWKClient` and accept `ES256` or `RS256`. Check `aud` equals `authenticated`, `exp`, and `sub`. Never log the token.

- [ ] **Step 4: Run tests**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest -q`
Expected: all tests pass.

- [x] **Step 5: Commit**

```bash
git add backend/app backend/tests backend/requirements.txt
git commit -m "feat: verify Supabase tokens and support Postgres"
```

### Task 4: Retention, delete cascade, and cold-start senders

**Files:**
- Modify: `backend/app/db/repository.py`
- Modify: `backend/app/services/analysis_service.py`
- Modify: `backend/app/api/analyses.py`
- Create: `backend/tests/test_retention_and_cold_start.py`

**Interfaces:**
- `delete_analysis(user_id: str, analysis_id: str) -> bool` removes the row, children, and stored file.
- `purge_expired(before: datetime) -> int` deletes old analyses across users.
- `load_sender_profile(user_id, sender) -> SenderProfile` returns neutral defaults when absent.

- [ ] **Step 1: Write the failing tests**

```python
def test_delete_removes_children_and_file(service, saved_case, storage_dir):
    assert service.delete_analysis(saved_case.user_id, saved_case.id) is True
    assert not (storage_dir / saved_case.storage_path).exists()

def test_first_time_sender_is_neutral(service, user_id):
    features = service.build_features(user_id, "new@example.com", email)
    assert features["sender_history_count"] == 0
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_retention_and_cold_start.py -q`
Expected: missing method or wrong feature value.

- [ ] **Step 3: Implement**

Make delete transactional. Remove the stored file only after the row deletes. Return `404` for another user's case. Add `POST /api/admin/purge` guarded by `ADMIN_TOKEN`, not by a user JWT.

- [ ] **Step 4: Run the suite**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest -q`
Expected: pass.

- [x] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add retention and cold-start handling"
```

### Task 5: Hugging Face Space deployment

**Files:**
- Create: `Dockerfile.space`
- Create: `deploy/space/README.md`
- Create: `.github/workflows/deploy-space.yml`
- Modify: `docs/12-deployment.md`
- Modify: `backend/app/main.py`

**Interfaces:**
- The Space runs `uvicorn app.main:app --host 0.0.0.0 --port 7860`.
- `GET /api/health` returns `model_loaded: true`.
- GitHub Actions pushes `backend/`, the model, and `Dockerfile.space` to the Space on `main`.

- [x] **Step 1: Write the deployment check** (build passes)

```bash
docker build -f Dockerfile.space -t phishlens-space .
docker run --rm -p 7860:7860 phishlens-space
curl http://127.0.0.1:7860/api/health
```

Expected: `{"status":"ok","model_loaded":true,...}`.

- [ ] **Step 2: Build and run locally**

Run the commands from Step 1. Fix only build failures.

- [ ] **Step 3: Add the workflow**

Use `huggingface_hub` with `HF_TOKEN` from GitHub Secrets. Do not print the token. Fail if `model_loaded` is false after deploy.

- [ ] **Step 4: Deploy and verify**

Run the workflow manually. Open the Space URL and check `/api/health`.

- [x] **Step 5: Commit**

```bash
git add Dockerfile.space deploy .github docs/12-deployment.md backend/app/main.py
git commit -m "feat: deploy backend to Hugging Face Spaces"
```

### Task 6: Frontend API and auth foundation

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/auth.tsx`
- Create: `frontend/src/api/client.test.ts`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/package.json`
- Create: `frontend/.env.example`

**Interfaces:**
- `apiFetch<T>(path: string, init?: RequestInit): Promise<T>` attaches the Supabase access token and throws `ApiError(status, detail)`.
- `useSession()` returns `{ session, user, loading, signIn, signOut }`.
- `RequireAuth` redirects unauthenticated users to `/login`.

- [ ] **Step 1: Add test tooling**

Run: `cd frontend; npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom`.
Add `"test": "vitest run"` to `package.json`.

- [ ] **Step 2: Write the failing test**

```ts
it("adds the bearer token", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  await apiFetch("/api/analyses", { token: "abc" });
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer abc");
});
```

- [ ] **Step 3: Implement**

Read `VITE_API_BASE_URL` and `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`. Throw on missing config. On `401`, clear the session and route to `/login`.

- [ ] **Step 4: Run**

Run: `cd frontend; npm run test; npm run build`
Expected: pass.

- [x] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add authenticated API client"
```

### Task 7: App shell, routes, and shared overlays

**Files:**
- Create: `frontend/src/components/AppShell.tsx`
- Create: `frontend/src/components/Toast.tsx`
- Create: `frontend/src/components/ConfirmDialog.tsx`
- Create: `frontend/src/components/SessionExpired.tsx`
- Create: `frontend/src/pages/NotFound.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- `AppShell` renders nav, main, footer, skip link, and `<Outlet />`.
- `useToast()` returns `{ show(message, tone), viewport }`.
- `useConfirm()` returns `{ ask(options), dialog }`.

- [ ] **Step 1: Write the failing test**

```tsx
it("marks the active route", () => {
  render(<MemoryRouter initialEntries={["/cases"]}><AppShell /></MemoryRouter>);
  expect(screen.getByRole("link", { name: /cases/i })).toHaveAttribute("aria-current", "page");
});
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd frontend; npm run test -- AppShell`
Expected: module not found.

- [ ] **Step 3: Implement**

Routes: `/`, `/cases`, `/cases/:id`, `/model`, `/how-it-works`, `/settings`, `/status`, `/login`, `*`. Keep the skip link and `#main-content`. Dialogs use `<dialog>` with focus return. Toasts use `role="status"` and `aria-live="polite"`. Respect `prefers-reduced-motion`.

- [ ] **Step 4: Run**

Run: `cd frontend; npm run test; npm run build`
Expected: pass.

- [x] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: add app shell and shared overlays"
```

### Task 8: Dashboard and cases list

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/Cases.tsx`
- Create: `frontend/src/lib/cases.ts`
- Create: `frontend/src/lib/cases.test.ts`

**Interfaces:**
- `filterCases(items, { query, band })` matches subject, sender, and band.
- `paginate(items, page, size)` returns `{ rows, page, pages, total }`.

- [ ] **Step 1: Write the failing tests**

```ts
it("filters by sender and band", () => {
  const rows = filterCases(cases, { query: "bank", band: "High" });
  expect(rows).toHaveLength(1);
});

it("clamps a page past the end", () => {
  expect(paginate(cases, 99, 10).page).toBe(1);
});
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd frontend; npm run test -- cases`
Expected: module not found.

- [ ] **Step 3: Implement**

Dashboard keeps the upload hero, stat strip, recent five cases, and links to `/cases`. Cases page adds search, band filter, sort, page size, pagination, and a real empty state. Both show distinct first-run, filter-empty, loading, and error states.

- [ ] **Step 4: Run**

Run: `cd frontend; npm run test; npm run build`
Expected: pass.

- [x] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: add dashboard and cases list"
```

### Task 9: Case report, model card, and method pages

**Files:**
- Modify: `frontend/src/pages/AnalysisDetail.tsx`
- Create: `frontend/src/pages/Model.tsx`
- Create: `frontend/src/pages/HowItWorks.tsx`
- Create: `frontend/src/components/ReasonCard.tsx`
- Create: `frontend/src/components/EvidencePanel.tsx`
- Create: `frontend/src/components/FeatureTable.tsx`

**Interfaces:**
- `sortContributions(rows)` returns rows sorted by `abs(contribution)` descending.
- `Model` reads `GET /api/model`; `HowItWorks` is static and names the six feature groups.

- [ ] **Step 1: Write the failing test**

```tsx
it("shows the largest contribution first", () => {
  render(<FeatureTable rows={[{ name: "b", contribution: -0.2 }, { name: "a", contribution: 0.9 }]} />);
  expect(screen.getAllByRole("row")[1]).toHaveTextContent("a");
});
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd frontend; npm run test -- FeatureTable`
Expected: module not found.

- [ ] **Step 3: Implement**

Detail page: verdict header, band bar, numbered verified reasons, evidence panels, top-20 contributions, raw headers, copy summary, and delete with confirm dialog. Model page states training source, metrics, thresholds, and limitations. Method page explains parsing, features, prediction, SHAP, verification, and bands.

- [ ] **Step 4: Run**

Run: `cd frontend; npm run test; npm run build`
Expected: pass.

- [x] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: expand case, model, and method views"
```

### Task 10: Settings, login, and status

**Files:**
- Modify: `frontend/src/pages/Settings.tsx`
- Modify: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/pages/Status.tsx`
- Create: `frontend/src/components/ProfileCard.tsx`
- Create: `frontend/src/components/AliasCard.tsx`
- Create: `frontend/src/components/RetentionCard.tsx`

**Interfaces:**
- `Status` reads `GET /api/health` and `GET /api/model`.
- `Login` calls `signIn(email, password)` and shows a field-level error, not a generic banner.
- Settings sections: profile, forwarding alias, sender baseline, retention, sign out.

- [ ] **Step 1: Write the failing test**

```tsx
it("shows a login error next to the field", async () => {
  render(<Login signIn={vi.fn().mockRejectedValue(new Error("Invalid login"))} />);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(await screen.findByText("Invalid login")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd frontend; npm run test -- Login`
Expected: failure.

- [ ] **Step 3: Implement**

Make login the only public route. Add no signup link. Settings uses cards and confirm dialogs for sign out and alias reset. Status shows API, model, and last-checked time.

- [ ] **Step 4: Run**

Run: `cd frontend; npm run test; npm run build`
Expected: pass.

- [x] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: add settings, login, and status"
```

### Task 11: Vercel frontend deployment

**Files:**
- Create: `frontend/vercel.json`
- Modify: `frontend/.env.example`
- Modify: `backend/app/main.py`
- Modify: `docs/12-deployment.md`

**Interfaces:**
- Vercel builds `frontend/` with `npm run build`.
- `VITE_API_BASE_URL` points at the Space.
- Backend CORS allows the Vercel production and preview domains only.

- [x] **Step 1: Write the deployment check** (build passes)

```bash
cd frontend
npm run build
npx vercel --prod
```

Expected: a production URL that loads the login page.

- [ ] **Step 2: Deploy** (blocked: needs your Vercel account)

Import the GitHub repo in Vercel. Set root directory `frontend`. Add `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY` for Production and Preview.

- [x] **Step 3: Fix CORS**

Set `CORS_ORIGINS` to the Vercel domains. Reject `*` when credentials are used. Add a test that an unknown origin is rejected.

- [ ] **Step 4: Verify live** (blocked: needs the deployed URL)

Open the URL. Sign in with a seeded user. Upload a sample email. Confirm a scored case appears.

- [x] **Step 5: Commit**

```bash
git add frontend/vercel.json frontend/.env.example backend/app/main.py docs/12-deployment.md
git commit -m "feat: deploy frontend to Vercel"
```

### Task 12: End-to-end smoke and submission docs

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/smoke.spec.ts`
- Create: `docs/16-demo-script.md` (13 is the testing doc)
- Create: `docs/report/final-report.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/02-project-log.md`

**Interfaces:**
- E2E base URL comes from `E2E_BASE_URL`; credentials from `E2E_EMAIL` and `E2E_PASSWORD`.
- Demo script covers sign-in, upload, report, delete confirm, model page, and status page.

- [x] **Step 1: Install Playwright**

Run: `cd frontend; npm install -D @playwright/test; npx playwright install chromium`.

- [x] **Step 2: Write the failing smoke test**

```ts
test("signs in and opens a case", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(process.env.E2E_EMAIL!);
  await page.getByLabel("Password").fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
});
```

- [ ] **Step 3: Run against the deployed URL** (local run passes; deployed run needs E2E_BASE_URL)

Run: `cd frontend; $env:E2E_BASE_URL="https://..."; npm run e2e`
Expected: pass.

- [x] **Step 4: Write the report and demo script**

Record dataset counts, grouped metrics, calibration, cold-start results, limitations, and the free-tier setup. Do not claim real-world performance.

- [x] **Step 5: Commit**

```bash
git add frontend docs README.md AGENTS.md
git commit -m "docs: add e2e smoke, report, and demo script"
```

## Self-Review

- Spec coverage: evaluation, Supabase, auth, retention, deployment, frontend surface, docs, and demo are all owned by a task.
- Review Focus: cold start is Task 4; cross-user isolation is Tasks 1 and 3; `401` is Task 3; oversized bodies are in the existing API tests; delete cascade is Task 4.
- Type consistency: `user_id` is the only owner key; `apiFetch` is the only HTTP entry point; `filterCases` and `paginate` are the only list helpers.
- Deliberately deferred: Gmail IMAP, real inbound MX, admin UI, background workers, and model retraining automation.

