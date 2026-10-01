---
id: model-gates-not-promotable
title: "szl-typesafe-triage: receipt verification red, 11 of 12 gates — publish evidence, do not promote"
surface: models
severity: medium
tags: [models, qualification, gates, szl-forge, typesafe-triage, huggingface]
last_verified: 2026-10-01
---
# szl-typesafe-triage: receipt verification red, 11 of 12 gates — publish evidence, do not promote

## Symptom
A five-seed study passes 11 of 12 release gates; `receipt verification` stays red; a text-only repair and passing local tests exist but no fresh evaluation and no new verified release receipt.

## Diagnose (PowerShell 5.1)
```powershell
$Root = (Resolve-Path -LiteralPath "$HOME\src\szl-typesafe-triage").Path; Set-Location -LiteralPath $Root
git pull --ff-only
Get-ChildItem out\train\study -Recurse -Filter "*gate*" | Select-Object FullName | Select-Object -First 10
python -m pytest -q tests 2>&1 | Select-Object -Last 3
```

## Fix
```powershell
# The order is fixed: pinned inputs -> isolated challenger -> frozen evaluation -> receipts -> publication gate -> promotion gate.
# 1. Re-run the frozen evaluation on the repaired candidate with byte-identical holdouts (never re-grade the published numbers in prose).
# 2. Emit a NEW release receipt and verify it offline:
python scripts\verify_release_receipt.py out\train\study\release-receipt.json
# 3. Only when 12/12 are green: publish the card (evidence-published), THEN open the separate promotion review.
```

## Verify
```powershell
python scripts\verify_release_receipt.py out\train\study\release-receipt.json; $LASTEXITCODE
```

## Notes
Publication is not promotion. A model may be evidence-published at 11/12 with the red gate stated on the card; it may not be routed as production until receipt verification is green. The eval script that produced the historical 12-case DEV result is not hash-bound by the receipt — a new grader written from scratch would manufacture evidence, so search your laptop for the original before rewriting.

## Sources
- https://github.com/szl-holdings/szl-typesafe-triage
- https://huggingface.co/SZLHOLDINGS/szl-triage-qwen3.5-0.8b-lora-study5
