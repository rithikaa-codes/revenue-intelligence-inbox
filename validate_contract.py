#!/usr/bin/env python3
"""
Automated Contract & Replay Validation Script
Validates all requirements specified in DATA_CONTRACT.md and ASSIGNMENT.md.
"""

import os
import sys
import json

# Ensure candidate directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
candidate_dir = os.path.join(current_dir, "candidate")
if candidate_dir not in sys.path:
    sys.path.insert(0, candidate_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import RevenueInboxEngine, TAXONOMY

def run_tests():
    print("=" * 60)
    print("RUNNING REVENUE INTELLIGENCE INBOX CONTRACT VALIDATION")
    print("=" * 60)

    engine = RevenueInboxEngine(workspace_dir=candidate_dir)

    # Step 0: Clean reset
    print("\n[Step 0] Resetting to clean state...")
    reset_res = engine.reset_to_clean()
    assert len(engine.records) == 0, f"Expected 0 records, got {len(engine.records)}"
    print(f" PASS: Workspace reset cleanly. Unique records = {len(engine.records)}")

    # Step 1: Initial import
    print("\n[Step 1] Importing 01_initial.json...")
    res1 = engine.import_initial_batch()
    metrics1 = engine.get_metrics()
    assert metrics1["total_unique_records"] == 44, f"Expected 44 records, got {metrics1['total_unique_records']}"
    assert metrics1["usable_text_count"] == 17, f"Expected 17 usable texts, got {metrics1['usable_text_count']}"
    assert metrics1["missing_text_count"] == 27, f"Expected 27 missing texts, got {metrics1['missing_text_count']}"
    assert metrics1["call_count"] == 30, f"Expected 30 calls, got {metrics1['call_count']}"
    assert metrics1["meeting_count"] == 14, f"Expected 14 meetings, got {metrics1['meeting_count']}"
    print(f" PASS: Initial batch imported: 44 unique records (30 calls, 14 meetings).")
    print(f"       Usable texts = {metrics1['usable_text_count']}, Missing text intake = {metrics1['missing_text_count']}")

    # Step 2: Repeat initial import reordered
    print("\n[Step 2] Repeating initial batch in reordered/reversed sequence...")
    res2 = engine.import_initial_batch(reordered=True)
    metrics2 = engine.get_metrics()
    assert metrics2["total_unique_records"] == 44, f"Expected 44 records, got {metrics2['total_unique_records']}"
    assert res2["inserted"] == 0, f"Expected 0 inserted, got {res2['inserted']}"
    assert res2["skipped"] == 44, f"Expected 44 skipped, got {res2['skipped']}"
    print(f" PASS: Reordered import produced 0 duplicates. Total unique records remains exactly {metrics2['total_unique_records']}.")

    # Step 3: Manual route correction on M07
    print("\n[Step 3] Applying manual route correction on M07...")
    m07_key = engine.record_key("meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
    assert m07_key in engine.records, "M07 not found in engine records"
    initial_m07 = engine.records[m07_key]
    assert initial_m07["applied_revision"] == 1
    assert initial_m07["has_usable_text"] is False

    manual_routes = ["Partner Development", "Deal Next Steps"]
    updated_rec = engine.set_manual_route("meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a", manual_routes)
    assert updated_rec["is_manual_override"] is True
    assert updated_rec["manual_route"] == manual_routes
    assert updated_rec["effective_routes"] == manual_routes
    print(f" PASS: M07 manual route successfully set to {manual_routes} (override flag = True).")

    # Step 4: Import update batch (02_update.json)
    print("\n[Step 4] Importing 02_update.json...")
    res3 = engine.import_update_batch()
    metrics3 = engine.get_metrics()
    assert metrics3["total_unique_records"] == 44, f"Expected 44 records, got {metrics3['total_unique_records']}"
    assert metrics3["usable_text_count"] == 18, f"Expected 18 usable texts, got {metrics3['usable_text_count']}"
    assert res3["updated"] == 1, f"Expected 1 updated, got {res3['updated']}"
    assert "M07" in res3["updated_refs"], f"Expected M07 in updated_refs, got {res3['updated_refs']}"

    post_update_m07 = engine.records[m07_key]
    assert post_update_m07["applied_revision"] == 2, f"Expected revision 2, got {post_update_m07['applied_revision']}"
    assert post_update_m07["has_usable_text"] is True, "Expected M07 to have usable text after update"
    assert post_update_m07["transcript_turns"] == 27, f"Expected 27 turns, got {post_update_m07['transcript_turns']}"
    # Critical contract test: manual route MUST be preserved!
    assert post_update_m07["is_manual_override"] is True, "Manual override flag lost!"
    assert post_update_m07["manual_route"] == manual_routes, "Manual route lost!"
    assert post_update_m07["effective_routes"] == manual_routes, "Effective routes not honoring manual route!"
    # Critical contract test: stale analysis warning triggered
    assert post_update_m07["analysis_freshness"] == "Stale - Source Updated", f"Expected stale warning, got {post_update_m07['analysis_freshness']}"
    assert post_update_m07["review_state"] == "Pending Review - Text Changed", f"Expected review state pending, got {post_update_m07['review_state']}"
    print(f" PASS: 02_update applied. Total records remains 44. Usable text coverage increased to 18.")
    print(f"       M07 updated to Revision 2 with 27 turns.")
    print(f"       M07 manual route preserved: {post_update_m07['effective_routes']}.")
    print(f"       Freshness flag correctly set to: '{post_update_m07['analysis_freshness']}'.")

    # Step 5: Replay older initial batch (rev 1)
    print("\n[Step 5] Replaying older initial batch (01_initial.json)...")
    res4 = engine.replay_older_batch()
    metrics4 = engine.get_metrics()
    assert metrics4["total_unique_records"] == 44
    assert res4["updated"] == 0, "Older batch should not update newer revision!"
    post_replay_m07 = engine.records[m07_key]
    assert post_replay_m07["applied_revision"] == 2, "Older revision overwrote newer revision!"
    assert post_replay_m07["effective_routes"] == manual_routes, "Manual route lost during older replay!"
    print(f" PASS: Older batch ignored. M07 remains Revision 2. Manual route preserved.")

    # Step 6: Simulate restart from disk
    print("\n[Step 6] Simulating application restart and loading state from disk...")
    new_engine = RevenueInboxEngine(workspace_dir=candidate_dir)
    reloaded_metrics = new_engine.get_metrics()
    assert reloaded_metrics["total_unique_records"] == 44
    assert reloaded_metrics["usable_text_count"] == 18
    reloaded_m07 = new_engine.records[m07_key]
    assert reloaded_m07["applied_revision"] == 2
    assert reloaded_m07["effective_routes"] == manual_routes
    assert reloaded_m07["is_manual_override"] is True
    print(f" PASS: Persistence verified. All state survived restart.")

    # Step 7: Export generation verification
    print("\n[Step 7] Generating exports and checking manifest integrity...")
    export_res = new_engine.generate_exports()
    assert export_res["total_records"] == 44, f"Expected 44 manifest rows, got {export_res['total_records']}"
    assert os.path.exists(export_res["manifest_json"]), "manifest.json missing!"
    assert os.path.exists(export_res["manifest_csv"]), "manifest.csv missing!"
    assert os.path.exists(export_res["zip_path"]), "revenue_inbox_exports.zip missing!"

    with open(export_res["manifest_json"], "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert len(manifest_data) == 44

    # Verify that all manifest output paths actually exist on disk
    missing_files = []
    for entry in manifest_data:
        for p in entry.get("output_paths", []):
            # p is like "outputs/deal-next-steps/C03_deal-next-steps.md"
            full_p = os.path.join(candidate_dir, p)
            if not os.path.exists(full_p):
                missing_files.append(full_p)
    assert len(missing_files) == 0, f"Missing output files: {missing_files}"
    print(f" PASS: Export generated with {len(manifest_data)} records. All file paths exist on disk!")
    print(f"       Downloadable ZIP created at: {export_res['zip_path']}")

    print("\n" + "=" * 60)
    print("ALL 7 CONTRACT & REPLAY TEST SUITES PASSED PERFECTLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
