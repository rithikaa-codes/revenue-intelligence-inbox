# Revenue Intelligence Inbox — SpendNest Operations Workspace

A lightweight, high-performance, deterministic revenue intelligence application built for sales managers to process incoming calls, calendar meetings, transcripts, and automated notes.

Built in accordance with:
- `ASSIGNMENT.md`
- `DATA_CONTRACT.md`
- `DATA_DICTIONARY.md`
- `CONVERSATIONS.md`
- `SUBMISSION_CHECKLIST.md`

---

## 1. Quick Startup Steps

The application runs using **standard Python 3 only** (no external pip dependencies, virtual environments, node modules, or paid API keys required).

### Option A: From Workspace Root
```bash
python app.py
```

### Option B: From `candidate/` Subdirectory
```bash
cd candidate
python app.py
```

### Open in Browser
Once the server starts, open your web browser to:
```
http://localhost:8000
```
*(If port 8000 is occupied, the server automatically binds to the next available port, e.g., 8001, and logs the active URL in the console).*

---

## 2. Architecture & Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend & Routing Engine** | Python 3 (Standard Library: `http.server`, `urllib`, `json`, `csv`, `zipfile`, `shutil`) | Zero-dependency, deterministic, portable across Windows, macOS, and Linux. |
| **Frontend UI** | HTML5, Vanilla CSS3, Modern JavaScript (ES6+) | Instant load times, zero build steps, responsive desktop-first design inspired by Linear & Stripe. |
| **State Persistence** | Local `state.json` + Browser Local Storage | All source records, revisions, review states, and manual manager overrides persist across browser refresh and server restart. |
| **Export Generation** | Route-specific Markdown files, `manifest.json`, `manifest.csv`, and ZIP archive | Fully traceable, deterministic, machine-readable exports organized by destination category. |

---

## 3. Data Contract & Replay Verification Steps

The application strictly implements the envelope and identity contract defined in `DATA_CONTRACT.md`:
- **Record Identity:** Strictly keyed by `(source_type, source_id)`. Record references (`M07`, `C01`), names, or array positions are never used as identity keys.
- **Revision Precedence:** Higher delivery revisions replace the entire source payload and transcript payload. Same or older revisions are ignored.
- **Manual Route Preservation:** Manager overrides are preserved independently of source updates.
- **Stale Analysis Flags:** When source text is updated (such as M07 receiving a 27-turn transcript in revision 2), analysis is marked `Pending Review - Text Changed` and `Stale - Source Updated` rather than silently presenting obsolete analysis.

### Interactive Replay Guide (In-App or Automated)

You can reproduce the contract tests either visually using the in-app **Import & Replay** console, or automatically using the included validation script.

#### Automated Contract Test:
```bash
python validate_contract.py
```
This runs 7 rigorous automated test suites verifying clean reset, initial import (44 records, 17 usable texts), reordered idempotency (0 duplicates), M07 manual correction, update ingestion (18 usable texts, M07 rev 2 with 27 turns), manual route preservation, older revision replay rejection, persistence across restart, and export file manifest integrity.

#### Manual Interactive Replay Steps (matching `RECORDING_SCRIPT.md`):
1. **Reset Demo:** Click **Reset Demo (Clean)** in the *Import & Replay* tab. State is wiped to 0 records.
2. **Initial Import:** Click **Import Initial Batch**. Ingests `data/01_initial.json`. Verify: exactly 44 unique records (30 calls, 14 meetings), 17 usable texts, 27 missing text intake records.
3. **Repeat Reordered:** Click **Repeat Reordered**. Replays initial batch in reversed order. Verify: 0 inserted, 44 skipped, unique record count remains 44.
4. **Manual Route Correction:** Click **Set M07 Manual Route** (or open M07 in the Inbox and select `Partner Development` + `Deal Next Steps`). Verify: M07 effective route updates and manual override badge appears.
5. **Update Ingestion:** Click **Import Update Batch**. Ingests `data/02_update.json`. Verify: M07 updates to Revision 2, receives 27 turns, usable text count increases from 17 to 18, total unique records remains 44, **M07 manual route is preserved**, and freshness is flagged as `Stale - Source Updated`.
6. **Replay Older Batch:** Click **Replay Older Batch**. Replays `01_initial.json` (revision 1). Verify: Revision 1 is ignored; M07 remains Revision 2; manual route is intact.
7. **Persistence:** Refresh the browser or restart `app.py`. Re-inspect M07: all state, revision 2 text, and manual route overrides remain intact.

---

## 4. Export Locations & Manifest Structure

When exports are generated (via the top bar button or `/api/export`), files are physically organized on disk under `outputs/`:

```
outputs/
├── deal-next-steps/          # Opportunities with commercial/technical next actions
│   ├── C03_deal-next-steps.md
│   ├── C08_deal-next-steps.md
│   ├── M01_deal-next-steps.md
│   ├── M03_deal-next-steps.md
│   ├── M04_deal-next-steps.md
│   └── M06_deal-next-steps.md
├── customer-follow-up/       # Scheduled callbacks, proposals, and customer updates
│   ├── C02_customer-follow-up.md
│   ├── C03_customer-follow-up.md
│   ├── C04_customer-follow-up.md
│   ├── C05_customer-follow-up.md
│   ├── C07_customer-follow-up.md
│   ├── C08_customer-follow-up.md
│   ├── C10_customer-follow-up.md
│   ├── M04_customer-follow-up.md
│   ├── M06_customer-follow-up.md
│   ├── M07_customer-follow-up.md
│   └── M09_customer-follow-up.md
├── sales-coaching/           # Rep coaching, respecting objections, and process bounds
│   ├── C01_sales-coaching.md
│   ├── C05_sales-coaching.md
│   ├── C06_sales-coaching.md
│   ├── C09_sales-coaching.md
│   ├── C10_sales-coaching.md
│   ├── M03_sales-coaching.md
│   └── M10_sales-coaching.md
├── partner-development/      # Channel partnerships, advisory referrals, integrations
│   ├── C07_partner-development.md
│   ├── M01_partner-development.md
│   └── M02_partner-development.md
├── internal-vendor-note/     # Engineering bug triage, vendor API notes, billing ops
│   ├── M02_internal-vendor-note.md
│   ├── M07_internal-vendor-note.md
│   ├── M09_internal-vendor-note.md
│   └── M10_internal-vendor-note.md
├── human-review/             # Intake records without usable text, gatekeeper calls
│   ├── B01_human-review.md ... B20_human-review.md
│   ├── C01_human-review.md
│   ├── C02_human-review.md
│   ├── C09_human-review.md
│   └── M05_human-review.md ... M14_human-review.md
├── manifest.json             # Machine-readable JSON manifest
├── manifest.csv              # Machine-readable CSV manifest
└── revenue_inbox_exports.zip # Complete downloadable archive
```

### Manifest Schema
Both `manifest.json` and `manifest.csv` record:
- `source_type`: `call` or `meeting`
- `source_id`: Raw unique source UUID
- `record_ref`: Display reference (e.g. `C03`, `M07`, `B01`)
- `applied_revision`: Integer (1 or 2)
- `effective_routes`: List of assigned destination categories
- `output_paths`: Relative file paths inside the archive
- `review_state`: `Reviewed`, `Intake - Needs Usable Text`, or `Pending Review - Text Changed`
- `is_manual_override`: Boolean indicating if route was modified by a manager
- `analysis_freshness`: `Current`, `Stale - Source Updated`, or `N/A - No Usable Text`
- `generated_at`: Timestamp in Asia/Kolkata timezone

---

## 5. Metric Methodology & Denominators

| Metric | Denominator | Definition & Policy |
|---|---|---|
| **Total Unique Records** | 44 | Distinct count of `(source_type, source_id)`. Fixed across repeated deliveries. |
| **Usable Supplied Text** | 44 | Records with non-empty conversation text. 17 initially (38.6%); 18 post-update (40.9%). Missing text reflects extract condition, not proof of inactivity. |
| **Missing Usable Text** | 44 | 27 initially; 26 post-update. Preserved with upstream metadata; substantive analysis withheld per data contract. |
| **Assigned Route Counts** | Variable | Sum of route assignments across records (e.g. 52). Exceeds 44 because multi-routing allows records to serve multiple business purposes. |
| **Activity by Person** | Distinct Rep / Org | Separates telephony representatives (outbound/inbound dialers) from meeting organizers (calendar creators). Organizers are not assumed to be salespeople or confirmed attendees. |
| **Timezone** | Asia/Kolkata | All timestamps presented in UTC+5:30. All selected activity occurs on 21 August 2026. |

---

## 6. Three Most Important Findings

### Finding 1: Explicit Cadence & Subject Follow-up (C03 — Milan)
- **What Was Observed:** Kiran followed up with Milan on developer API access. Milan reported roaming audio interference and noted past price sensitivity, but agreed to an email follow-up and callback.
- **Source Citation:** C03 call text:
  > *"Could we do this by email? Or call on Monday a bit earlier, when I'm back indoors?... Something like 'Developer access and event notifications — follow-up'... Send the email and we can speak Monday or Tuesday."*
- **What Evidence Supports:** Sending a pricing proposal with the exact subject line and scheduling an outbound callback for Monday morning.
- **What Evidence Does NOT Establish:** Does not establish purchase intent or budget approval. Milan explicitly stated: *"it isn't essential enough for us to spend much on it."*
- **Product Impact:** Governs C03 routing to `Deal Next Steps` + `Customer Follow-up`; featured in Manager Brief Follow-up Priorities table.

### Finding 2: Channel Referral Signal vs Closed Deal (C07 — Aditya)
- **What Was Observed:** Dev cold-called Aditya at Willowbank Advisory proposing virtual business accounts for newly incorporated overseas entities. Aditya confirmed they regularly refer corporate clients to account providers, requested a proposal via chat app, and agreed to a Monday follow-up call.
- **Source Citation:** C07 call text:
  > *"Do you currently refer clients to providers for that part of the process? Yes, that is something we normally do... send whatever proposal you have... could I call on Monday to see whether you'd like to discuss it further? Yes, that's fine."*
- **What Evidence Supports:** Routing to `Partner Development` and dispatching partner program materials via chat app.
- **What Evidence Does NOT Establish:** Does not establish an executed partnership contract or guaranteed referral volume. Labeling this a "won deal" or pipeline revenue would be a fabricated claim.
- **Product Impact:** Governs C07 `Partner Development` routing; informs Manager Brief partner strategy; prevents false pipeline inflation.

### Finding 3: Explicit Customer Disinterest as Governance Signal (C01 — Pranav)
- **What Was Observed:** Pranav firmly rejected Arun's cold outreach, stating he did not request contact, his work mobile is not for sales calls, and his firm already has advanced internal automation.
- **Source Citation:** C01 call text:
  > *"I didn't ask for this call, and I'm not interested. This number is for my work, not for people to sell things to me... Our processes are already very automated... I don't think this is something we need."*
- **What Evidence Supports:** Immediate addition to CRM suppression/do-not-call list and coaching SDRs to conclude calls immediately upon clear disinterest.
- **What Evidence Does NOT Establish:** Does not establish future product demand or rep ethical violation; however, continuing outreach would violate customer preference.
- **Product Impact:** Surfaces C01 as a `Sales Coaching` priority; suppresses further automated cadences; prevents harassment.

---

## 7. Deliberately Rejected Product Decision

### Rejected Alternative: Enforcing a Strict "One Route Per Conversation" Constraint
- **Why It Was Considered:** Traditional CRM pipelines force every activity into a single category (e.g., either "Sales Lead" OR "Customer Support") to maintain simple 1:1 reporting.
- **Why It Was Rejected:** Real revenue interactions routinely serve multiple organizational purposes. For example:
  - **C07** is both a channel partnership negotiation (`Partner Development`) and an active task (`Customer Follow-up`).
  - **M07** is both customer issue support (`Customer Follow-up`) and an urgent engineering bug report (`Internal / Vendor Note`).
  - **M03** is both an active enterprise sales deal (`Deal Next Steps`) and a coaching boundary on executive gatekeepers (`Sales Coaching`).
  Forcing a single category would destroy cross-departmental visibility and lose vital follow-up context.
- **Trade-off Accepted:** Total assigned routing counts (e.g. 52 across 44 records) exceed the number of unique source records. To prevent confusion, the Overview dashboard and Methodology panel explicitly display the distinct denominators and explain this design choice transparently.

---

## 8. AI Usage & Pre-generated vs Dynamic Operations

- **Pre-generated / Static Elements:** Candidate-derived analysis (summaries, passage citations, boundaries, recommended next steps) for the 18 conversations with usable text was compiled deterministically before runtime to ensure zero hallucinations, evidence fidelity, and zero paid API dependencies.
- **Dynamic Runtime Operations:**
  - Ingestion, upserting, and revision management per `DATA_CONTRACT.md`.
  - Identity verification and idempotency filtering based on `(source_type, source_id)`.
  - Manual route overrides, override state tracking, and reset-to-suggestion logic.
  - Source text change detection and `Stale - Source Updated` analysis flagging.
  - Interactive multi-parameter filtering, search, and activity aggregation.
  - On-disk export generation of route-specific Markdown files, `manifest.json`, `manifest.csv`, and ZIP compression.
  - State persistence to disk (`state.json`) and local browser storage.

---

## 9. Submission Deliverables Summary

- `app.py`: Working HTTP server and deterministic engine.
- `index.html`, `styles.css`, `app.js`: Interactive SaaS frontend.
- `validate_contract.py`: Automated contract verification suite.
- `Submission_5_Slides.pptx`: 5 presentation slides covering problem, interface, routing, numbers, and trade-offs.
- `RECORDING_SCRIPT.md`: 3-minute screen recording narration guide.
- `SUBMISSION_CHECKLIST.md`: Verified submission checklist.
- `outputs/`: Route-specific export directory.
- `manifest.json` & `manifest.csv`: Export manifests.
- `revenue_inbox_exports.zip`: Downloadable export archive.

---

## 10. Known Limitations & Next Improvements

1. **Local Single-User Persistence:** Persistence is implemented via a local JSON file (`state.json`) and local browser storage. For multi-user concurrent production use, an ACID-compliant SQL store (e.g., SQLite or PostgreSQL) with optimistic concurrency locks would be introduced.
2. **Deterministic Rules vs Live LLM Triage:** Routing rules and candidate analyses are deterministic. In production, an on-premise or privacy-preserving LLM could assist with drafting candidate analysis on newly arriving transcripts, while retaining human-in-the-loop approval.
3. **Audio Playback:** Telephony audio and video recording files were redacted in the assessment fixture; adding waveform playback and clickable turn synchronization would enhance usability when media is available.

---

## 11. Time Spent

**Approximate Hours Spent:** `[CANDIDATE_HOURS_PLACEHOLDER: e.g. 7.5 hours]`
*(Please update this placeholder with your exact personal time spent before final submission).*
