# Three-minute continuous screen recording — narration guide

**Before recording:** start `python app.py`, open the dashboard, click **Load final demo state**, and ensure the app shows 44 unique records and 18 usable supplied texts. This script is a guide; narrate in your own words. The assignment requires your own spoken narration in one continuous screen capture.

## 0:00–0:35 — Overview and one metric

“ This is the Revenue Intelligence Inbox for the selected activity on 21 August 2026. The dataset has 44 unique source records: 30 calls and 14 meetings. After the late update, 18 have usable supplied conversation text. Coverage is usable texts divided by unique records, not a claim that the other records never happened. The activity chart separates call reps from meeting organisers, because an organiser is not automatically a salesperson or confirmed attendee. ”

Show the dashboard cards and activity chart. Change the source-type filter to demonstrate it works, then return to all types.

## 0:35–1:15 — Inspect a useful conversation and difficult route

“ I’ll open C07. The contact says they normally refer clients to providers for business accounts, then agrees to receive a proposal and a Monday follow-up. That supports partner development and a follow-up action, but it does not prove a purchase or a deal value. I allow multiple routes because one conversation can support more than one useful output. ”

Open C07 in the inbox, show the source text and route selector. Point out the next action and evidence excerpt. Briefly open C01 and say the explicit “I'm not interested” statement is treated as a signal to respect the recipient’s preference, not as a reason for repeated outreach.

## 1:15–2:35 — Duplicate/update replay and correction preservation

“ Now I’ll demonstrate the replay contract. I’ll reset the workspace, import the initial batch, and repeat it in reverse order. The count stays at 44 because the identity is the pair source type and source ID; it does not use record names or array positions. The initial batch has 17 usable texts. ”

Click Reset demo. In Exports & replay, import initial batch; show 44 and 17. Click repeat initial batch (reordered); show no count change.

“ I’ll select M07 and make a manual route correction. Manual judgement is stored separately from source data. Now I’ll import the update. M07 becomes revision 2 and the late transcript appears, but the manual route remains. The analysis is marked pending review because source text changed. Finally, replaying the older initial batch does not roll M07 back. ”

Select M07, save a different route, import update, inspect M07, click older initial replay, then refresh and reopen M07 to show persistence.

## 2:35–3:00 — Export and limitations

“ The export contains a JSON and CSV manifest plus route-specific Markdown outputs. Each output records the source identity, revision, route and evidence, so a multi-route conversation does not lose context. The analysis is deterministic triage, not a live AI call. I have deliberately not estimated pipeline revenue or performance rankings because the supplied data does not support them. ”

Show export buttons, then end recording. Keep the recording continuous and speak naturally; do not submit this script instead of the recording.
