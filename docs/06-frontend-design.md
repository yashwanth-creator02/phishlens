# 06 - Frontend design

React 18 + TypeScript + Vite; `react-router-dom`; optional `@supabase/supabase-js`. Source: `frontend/src/`. Builds with `npm run build` (type-check + bundle).

## Screens

Six top-level screens, each with one job. The navigation groups them into the two screens an analyst works in all day and the three reference screens, separated by a rule in the top bar.

| Route | File | Shows |
|---|---|---|
| `/` | `pages/Dashboard.tsx` | upload box (.eml), band-count strip, the five most recent analyses |
| `/history` | `pages/History.tsx` | the full record list: search, band filter, sort, page size, pagination |
| `/analyses/:id` | `pages/AnalysisDetail.tsx` | band bar + score + guidance, **reasons** (tagged by evidence group), inline-forward notice, sender-history note, evidence (links with shown-vs-real, attachments, authentication, preview), optional SHAP feature table, delete |
| `/model` | `pages/Model.tsx` | active model card, band thresholds, training metrics, limitations |
| `/how-it-works` | `pages/HowItWorks.tsx` | the six pipeline steps |
| `/profile` | `pages/Profile.tsx` | signed-in identity, forwarding alias, trusted-sender baseline upload, sign out |
| `/status` | `pages/Status.tsx` | API health and model identity, service metrics |
| `/login` | `pages/Login.tsx` | Supabase email/password; hidden when auth is disabled |

The Dashboard deliberately does not repeat the History controls. It answers "what needs my attention right now"; History answers "find a specific earlier result". A screen that did both would make the analyst filter a list of five.

* `api/client.ts` - typed fetch wrapper; adds `Authorization: Bearer <Supabase access token>` when Supabase is configured. In dev, Vite proxies `/api` to :8000 (no CORS); in Docker nginx does.
* LOW results are titled "Minor signals noticed", MEDIUM/HIGH "Why this message looks suspicious".
* The UI states plainly that explanations are checked against the email and that it does not replace the user's judgement.

## Screenshots (captured from the running app with the synthetic demo model)
![Dashboard](screenshots/dashboard.png)
![Analysis detail](screenshots/analysis_detail.png)

Note: in the SHAP table, some features show contributions that look odd (e.g. a failed SPF with a negative contribution). That is a property of the *synthetic* demo model (legitimate synthetic mail also fails SPF sometimes); it is exactly the kind of thing to examine with real data. Reasons only use risk-*raising* contributions.

## Next UI work
Reason wording review; "report as phishing / mark as safe" feedback buttons (also feeds sender history); Supabase password reset flow; browser add-on reuse of `api/client.ts`.

Completed in v0.1 UI polish:
- History search and risk-band filtering controls.
- Mobile layout polish with responsive wrapping for headers, stat cards, and evidence tables.
- WCAG AA contrast compliance and accessibility pass (focus visible outlines, `role="status"` on loaders, skip links).
- Honest stat strip reporting loaded counts and capping limits.
- Bounded, high-contrast typography and design token system.

Completed in the v0.2 screen split:
- Six separate screens with one job each: Dashboard, History, Profile, Model, Status, How it works.
- The top bar separates the working screens (Dashboard, History) from the reference screens (Model, How it works, Status), and the signed-in address and Profile sit on the right.
- The active destination carries `aria-current="page"` and a colour and weight change, so the current screen is not signalled by colour alone.
- The Profile screen owns the account surface that used to be mixed into Settings, and Settings itself is gone: the model card lives on `/model`, where the other model facts already were.
- Every screen uses the same page-header shape: an H1, one line of purpose, and the page action on the right.
