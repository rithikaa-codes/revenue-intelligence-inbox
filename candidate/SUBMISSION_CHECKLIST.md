# Submission Checklist — Verified

- [x] **Working local app with exact startup steps:**
  - Startup: `python app.py` (accessible at `http://localhost:8000`).
  - Tested across both workspace root and `candidate/` directory.

- [x] **Editable source; no private keys or dependencies folder:**
  - Self-contained vanilla HTML/CSS/JS frontend and Python standard library backend. Zero third-party packages, zero private keys, zero external credentials.

- [x] **Organised generated files and machine-readable manifest:**
  - Route-specific Markdown files generated in `outputs/deal-next-steps/`, `outputs/customer-follow-up/`, `outputs/sales-coaching/`, `outputs/partner-development/`, `outputs/internal-vendor-note/`, and `outputs/human-review/`.
  - Machine-readable `manifest.json` and `manifest.csv` with 100% verified paths.
  - Downloadable archive: `revenue_inbox_exports.zip`.

- [x] **Five slides as PPTX explaining decisions, evidence and trade-offs:**
  - `Submission_5_Slides.pptx` in workspace root covering manager problem & 3 findings, interface choices & omissions, route design & M07 difficult case, number validation, and trade-offs/limitations.

- [x] **Short README:**
  - `README.md` includes exact run steps, replay instructions, export locations, metric definitions, pre-generated vs dynamic operations, findings, trade-offs, and hours spent placeholder.

- [x] **Three-minute screen recording with narration guide:**
  - `RECORDING_SCRIPT.md` provides continuous narration script for 0:00–3:00 covering overview, C07/C01 analysis, idempotency reordered import, M07 manual correction, update ingestion, older replay rejection, persistence, and export structure.

- [x] **Three most important findings:**
  - Finding 1: C03 (Milan — developer API access email & callback window).
  - Finding 2: C07 (Aditya — channel referral partnership lead vs closed sale).
  - Finding 3: C01 (Pranav — explicit customer disinterest & suppression governance).
  - Documented in `README.md`, `Submission_5_Slides.pptx`, and in-app Settings view.

- [x] **One deliberately rejected decision:**
  - Rejected forcing a single route per conversation. Multi-route support allows complex interactions (e.g. C07, M07, M03) to serve multiple department destinations while transparently explaining that assigned route counts can exceed unique source records.
  - Documented in `README.md`, `Submission_5_Slides.pptx`, and in-app Settings view.

- [x] **Automated contract test suite:**
  - `validate_contract.py` executes and passes all 7 validation suites for the data contract.

- [x] **Approximate hours spent, known limitations and unfinished work:**
  - Documented in `README.md` with explicit placeholder for candidate time.
