# Longbridge CCASS Rolling Window Emergency Capture V1

日期：2026-09-25（Asia/Hong_Kong）

## Probe result

現有 OAuth cache 可用，並以現有 Longbridge MCP client 成功 authenticated probe
`broker_holding_detail`。00003.HK、00005.HK、00006.HK 均回傳成功但空 `list`，
`updated_at=2026.09.24`。空回應只代表本次 surface 沒有可回傳 participant rows，
不能解讀為零持股或歷史資料不存在。

## API limitation

目前 repository 的 Longbridge adapter 只有 stock-specific `broker_holding_detail`、
`broker_holding` period change，以及指定單一 broker 的 `broker_holding_daily`。沒有
可列舉 earliest available date、全市場 participant snapshots 或按日期批量下載的
historical endpoint。因此本次無法安全發現 rolling-window lower boundary，也沒有
在未取得 rows 時猜測日期或製造 coverage。

## Existing durable state

Read-only inventory of `data/ccass_snapshots.db` found Longbridge persisted dates
2026-09-09、2026-09-10、2026-09-11，共 6 snapshot rows。這些既有資料保留；沒有
delete、truncate、overwrite、Research Store 寫入或來源層替換。

## Gate

`LONGBRIDGE_RECENT_CCASS_COVERAGE_V1.json` records the exact probe and existing-date
checkpoint. Emergency capture remains **BLOCKED** because the currently available
authenticated API surface does not expose an enumerable historical participant dataset.
下一個可執行動作是取得 Longbridge 支援的 full-market/date-addressable historical
CCASS endpoint（或 owner-approved raw export），再按日期 checkpoint、append/upsert、
readback and hash capture；不可把 current empty responses 當作 zero。
