# CCASS 2025-12 to 2026-07 Extension Bridge Verification V1

日期：2026-09-25（Asia/Hong_Kong）  
模式：read-only；沒有重建、全量回填或來源寫入。

## Artifact

實際 artifact 為 Owner-provided `David_Webb_CCASS_Research_Pack` ZIP：

`G:\我的雲端硬碟\投資 - 享受與豐盛\AI Projects\joe-ccass-platform\docs_reference_evidence\David_Webb_CCASS_Research_Pack\drive-download-20260921T133916Z-1-001.zip`

ZIP SHA-256 為 `0681F59B2A2229CBFA2602819CF69B4A4C23AE1A3FF9CB595DE2FA3E5C4529EB`，大小
61,420,993 bytes。內含 `participants.csv` 及 2025-12 至 2026-07 的八個 gzip holdings
快照。資料列實測 9,540,395，日期為 2025-12-01 至 2026-07-31，共 162 個觀察日；
issueID distinct 3,071，participant distinct 590。issue count 比舊文件的 3,070 高一項，
保留實測值，不強行對齊記憶值。

## Semantics and integrity

CSV 欄位為 `atDate, stockCode, issueID, ccassID, partID, holding`。`holding` 是來源日期的
absolute participant state；participant identity 是來源 participant/custodian，不能解讀為
beneficial owner。自然鍵為 `(issueID, partID, atDate)`；重複鍵 0、value conflict 0、
negative values 0、critical null 0。沒有把缺失日期轉成 zero。來源 row-level lineage 可追溯
到 ZIP 內的月度 gzip entry。

## Date and source bridge

權威 historical core 的最後有效日仍是 2025-12-24。extension layer 覆蓋至 2026-07-31，
其中 2025-12-01 至 2025-12-24 與 core 的日期範圍重疊。當前 production Longbridge
evidence 的已驗證樣本在 2026-09-09 至 2026-09-17；因此 extension 到 current 之間存在
明確未覆蓋區間（至少 2026-08-01 至 2026-09-08），不能宣稱無日期缺口。

## Overlap finding

不能把 ZIP 的 `issueID` 直接當作 authoritative Webb SQLite 的 `shortnames.c1`。三個實際
樣本（0003、0005、0006）顯示兩個來源的 issue namespace 並非可直接 join；若未取得已驗證
的 issue mapping，participant/date natural-key equivalence、share-quantity equivalence
及 exact mismatch counts 都不能安全宣稱。這是 `OVERLAP_UNVERIFIED`，不是把 mismatch
當作 source failure，也沒有覆寫任一來源。

## Deterministic bridge contract

在 mapping 及 overlap reconciliation 完成前，不啟用物化 concatenation。暫定安全規則為：
historical core authoritative through 2025-12-24；extension is authoritative only for
its verified 2025-12-25 through 2026-07-31 observations after overlap acceptance；current
Longbridge remains source-native from its actual observed date. The 2025-12-01 through
2025-12-24 overlap remains a comparison window, not a second counted layer.

## Doctor readback

Existing accepted evidence proves source-backed readback for three stocks across Webb core,
the gap package and current Longbridge snapshots, with source lineage preserved. This task
did not expose the ZIP as a new production route and did not mutate Research Store. Therefore
the extension-specific Doctor exposure status is `EXPOSURE_GAP`; data absence must not be inferred.

## Result

Artifact discovery, row count, date coverage, participant semantics, natural-key uniqueness and
lineage checks pass. Full `EXTENSION_BRIDGE_PASS` remains **NO** pending a verified issue/security
mapping for exact overlap equivalence and a documented 2026-08 to current gap. No raw source,
cloud source, Research Store or production database was modified.
