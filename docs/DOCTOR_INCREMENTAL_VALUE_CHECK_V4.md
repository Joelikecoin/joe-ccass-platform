# DOCTOR_INCREMENTAL_VALUE_CHECK_V4

> Package §6: 剩餘來源攝取前先做增量價值檢查。LOW_INCREMENTAL_VALUE 者跳過或
> 只記錄，不擴充規則數。

| source | classification | decision |
|---|---|---|
| 股票案例/L型研究_完整結果總表_20260731.md | LOW_INCREMENTAL_VALUE（原研究的樣本數據表；GO-MEDIATOR/SCREENING-NOT-DISCRIMINATOR 的統計結論已隨 IVANL-LXING-GO-MECH 攝取；表內數字不新增能力或條件） | SKIP — Luna 執行 LT-11 時直接向 Joe 索取原始表 |
| 股票案例/Ivan老師L型List現況檢查 - chatgpt.md | LOW_INCREMENTAL_VALUE（持倉現況更新，非方法規則） | SKIP — 供 Luna 個案挑選參考 |
| 股票案例/chatgpt_L型絕地投資法研究｜I 版【最終版】.md | SAME_RULE_NEW_EVIDENCE（與已攝取 L型研究I版 同一研究的 earlier version） | SKIP — 無新增 capability；如 Luna 發現 LT-11 需要更早版本條件定義再開 |
| 周顯 L2B/3A/3B/4/5A/5B/102（7 units） | 未逐檢 — 依 L1/L2A 先例（大勢框架+已覆蓋的供股/碎股/門檻規則）預期多為 LOW~MEDIUM | DEFER — 下輪逐檔做 SOURCE_INCREMENTAL_VALUE_CHECK；僅 NEW_RULE_LOGIC/NEW_FALSIFICATION 級內容才攝取 |
| 20260906 Hilton GO全購買殼學 五階段完整教材.md（113KB） | 未逐檢 — 與 L2 GO-STAGE-MATRIX 高度重疊（同主題五階段），但為最大單一來源、可能含 NEW_CONDITION（各階段細節門檻） | DEFER — 下輪以 checkpoint 方式分節攝取，僅增補 DISTINCT_CONDITIONS 不開新 capability |
| 財技班 筆記 PDF 8 份 | LOW_INCREMENTAL_VALUE（課堂摘要已覆蓋主幹；PDF 逐頁成本高） | SKIP |

## Rule inflation control

```text
RAW_RULE_COUNT=48
RULE_FAMILY_COUNT=14
DISTINCT_CAPABILITY_COUNT=14
LUNA_TARGET_COUNT=14 (HIGH=11)
```

結論：48 條規則 = 14 個真正獨立 Doctor 能力。教師重複表述（Hilton 乾度門檻在
L1/L7/L8 重複出現、周顯與 Hilton 的門檻線索同構）已按 §8 處理：只計一次能力，
lineage 保留全部來源，status 一律維持 CASE_DERIVED / PARTIALLY_CASE_SUPPORTED，
不因「多課重複」或「多師同講」晉升。
