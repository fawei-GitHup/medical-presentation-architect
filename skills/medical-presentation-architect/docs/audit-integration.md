# Audit integration report

## Inputs read

- `audit-handoff.md` **v1.0** — 2026-09-14. The referenced source file was available outside this release tree and was read. Its clinical statements are findings to verify against a suitable current guideline, model/version-specific IFU or approved institutional SOP; they are never converted into replacement clinical instructions.
- `intake-design-addendum.md` **v1.1** — includes the v1.0 adaptive-intake design plus the user-notice module and behavior cases 11–20.
- The five supplied private PPT/script artifacts were inventoried locally. None are copied into this public-ready source tree or release ZIP.

## Audit findings mapped to implementation

| Finding | Implemented control | Executable validation | State |
|---|---|---|---|
| F01 visible and hidden layers may differ | `rules/medical-integrity.md`, `rules/failure-gates.md`, `scripts/pptx_lint.py` inspects hidden pages/shapes, image overlays and rendered page count | `test_hidden_slide_detected`, `test_image_overlay_detected` | Implemented; OCR and expert visual review remain manual |
| F02 image count does not measure usefulness | `rules/visual-policy.md`, `rules/image-policy.md`, visual plan carries purpose/placement/alt and image count is a warning only | `test_visuals_require_purpose_and_bounds`, image duplicate/resolution tools | Implemented; semantic relevance requires human review |
| F03 layout follows learning task | content-type opportunities and typed slide/visual schemas; visual planner selects flow, comparison, data, table, case and text forms | `test_demo_builds_varied_editable_content` | Implemented; automatic arrangement is a baseline, review remains required |
| F04 image/title/progress/notes must agree | per-slide objectives, evidence IDs, speaker-note source binding; PPT lint and review require every slide | `test_notes_and_page_coverage_gate` | Implemented |
| F05 geometry and projected readability | `rules/layout.md`, bounds/font/PPI lint and actual all-page rendering | `test_out_of_bounds_fails`; demo PowerPoint render | Implemented for bounds/structure; actual fit remains a visual judgment |
| F06 notes need slide-level sync | stable slide IDs, build attaches notes to their own slide; notes included in review/fingerprint | `test_notes_are_slide_specific` | Implemented |
| F07 numbers retain conditions/comparison | `rules/medical-integrity.md`, claim ledger requires scope, locator, source link/status | `test_numeric_claim_without_verified_source_blocks` | Implemented; source-content interpretation needs reviewer |
| F08 heat treatment branches by material/device | evidence rule keeps material/model/IFU scopes; never universalizes specific manufacturer statements | `test_device_claim_cannot_be_generic_without_evidence` | Implemented as a gate; actual device instructions require current model-specific IFU |
| F09 reprocessing depends on scanner/sleeve | image/device claim source and scope requirements; unresolved model blocks affected claims | `test_unverified_device_claim_stops_export` | Implemented as a gate; cannot determine user department's installed configuration |
| F10 bonding treatment is material-specific | no universal sequence in rules; requires supported source mapped to the claim | `test_material_conditioning_claim_needs_source` | Implemented as a gate; specialist confirms manufacturer IFU |
| F11 previous version “corrections” remain unverified | original values stay in factual inventory; no assumption that V2.1 resolved them | `test_old_parameters_remain_observations` | Implemented in intake procedure; supplied deck stays outside public repo |
| F12 unsupported universal nursing directions | scope and support required for clinical/process instructions; “common knowledge” is not a bypass | `test_universal_instruction_without_support_fails` | Implemented |
| F13 avoid absolute outcome claims | study design and endpoint boundary rule; claim-to-source locator review | `test_source_exists_but_does_not_prove_scope_blocks` | Implemented structurally; faithfulness is a human semantic review |
| F14 image source, privacy, clinical truth | required asset hash, license, consent/privacy state, origin, modifications and alt; public bundle allow-list | `test_uncleared_case_asset_blocks`, `test_release_bundle_excludes_project_data` | Implemented; OCR misses and consent validity remain human/organizational responsibilities |
| F15 hard-coded slide/script weaknesses | data-first stable slide IDs/role fields, per-slide typed rendering, notes, explicit unsupported-type failure | `test_build_uses_stable_ids_and_emits_notes`, `test_unsupported_visual_fails_loudly` | Implemented for new decks; arbitrary legacy-template cloning is not claimed |
| F16 honest status and failure gate | `qa`, `review-template`, `export`; content/render/review fingerprints and stage-specific status | `test_missing_review_blocks`, `test_stale_review_blocks`, `test_unverified_claim_blocks` | Implemented; report is an audit record, not a digital signature or credential check |

## Adaptive intake and user-visible task explanation (addendum v1.1)

| Requirement | Implementation | Test/verification | State |
|---|---|---|---|
| Clear / fuzzy / focused-edit routes | `prompts/adaptive-intake.md`, `design-brief.schema.json` | tests 01, 03 | Implemented |
| Inventory before guessing ambiguous audience; multi-label topics | `content-inventory.schema.json`, adaptive prompt | test 01; manual realistic scenario review | Implemented |
| Provenance states and one versioned source of truth | `intake/design_brief.json`, origin/status/confidence fields | test 02, test 10 | Implemented |
| Execution prompt auto-compiled from brief, no copy-paste | `mpa.py prompt`, `set-field` | test 10, test 18 | Implemented |
| Scope-limited edit | `focused_edit`, scope fields | test 03, test 14 | Implemented |
| Do not force takeaway titles / nursing-only POV / fixed page limits | adaptive intake and visual rules | test 08, prompt scenario cases | Implemented |
| Preserve unverified old parameters as observations; do not call them medical guidance | inventory vs claims separation | test 05, test 11 | Implemented |
| Continue independent work around clinical unknowns | per-question `blocking_scope` | test 09, test 17 | Implemented in workflow instruction; model behavior also needs evaluation |
| Explain approach, reused facts, gaps, defaults and scope in user dialogue | `intake/user_notice.json/.md`, `render_notice`; Skill requires actually show to user | tests 11–20 on fields and consistency; this task updates have been sent in conversation | Implemented; future model must follow instruction |
| Never fabricate sent/read/approved | delivery starts `prepared`; only runtime may mark `sent` after display | test 19 | Implemented; no automatic read/approval signal |
| Sync brief / notice / prompt after correction | `set-field` increments version and recompiles outputs | test 18 | Implemented |

## What still needs professional or local confirmation

1. For a real clinical deck, a qualified domain reviewer must verify each source actually supports its claim and matches local population, product/model, region, and current IFU/SOP version.
2. The department must confirm licensed use and de-identification of its case images and local records. Automated file/metadata scans cannot establish consent or rule out re-identification.
3. The bundled builder is an editable PPTX baseline, not a universal importer for existing hospital .potx/.pptx templates. A template adapter needs real font/office rendering and review.
4. The handoff's named dental equipment/material and nursing statements remain audit leads, not approved operating procedures. The package has not independently repeated a systematic clinical search.
5. Behavior checks cover contracts and deterministic controls; natural-language user understanding needs qualitative model evaluation and feedback from actual clinicians/nurses.

This mapping reports package implementation; it does not certify the supplied deck as clinically approved.
