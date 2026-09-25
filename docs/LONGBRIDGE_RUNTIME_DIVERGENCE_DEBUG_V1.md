# Longbridge Runtime Divergence Debug V1

日期：2026-09-25（Asia/Hong_Kong）

## Exact equivalence

本次使用的 exact request 是 `symbol="700.HK"`，broker IDs 為 `A00003` 及 `B01955`。
沒有使用 `00700.HK`、`0700.HK`、`700` 或 `HK.700`。

## Runtime diagnosis

Codex 使用 `app.sources.longbridge.LongbridgeMcpClient`，transport endpoint 為
`https://mcp.longbridge.com`，透過本機 OAuth cache；secret 沒有輸出。Exact probes
結果：

- `broker_holding_daily("700.HK","A00003")`: 40 rows，2026-07-31 至 2026-09-24。
- `broker_holding_daily("700.HK","B01955")`: 40 rows，2026-07-31 至 2026-09-24。
- `broker_holding_detail("700.HK")`: 421 rows。
- `participants("700.HK")`: 545 participant entries。
- `broker_holding("700.HK","rct_60")`: valid response，buy/sell lists empty；這是 period movement surface，不是 daily history。

Daily response shape 是 `{ "list": [{"date","holding","ratio","chg"}, ...] }`。
沒有 HTTP/API error、auth error、permission error 或 parser failure。分類為
`VALID_200_NONEMPTY`；前一次 empty 結果是因為只 probe 00003/00005/00006，不能外推到
700.HK。沒有 adapter code fix，因 exact request 已經通過。

## Rescue continuation

既有 checkpoint 已延續，將 700.HK 兩個已證實 participant 的 80 rows 寫入隔離 raw
SQLite：`work/longbridge_ccass_daily_rescue_20260925.sqlite`。natural key 為
`(stock_code, participant_id, observation_date)`；duplicate overwrite 0、conflict 0，
readback 80/80。資料保留 source system、source surface、fetch time、payload hash 及
quality status。DB SHA-256：`EDF6FE01D92F0C4C7D5657FEAA482B448874029D2A23E747E3E2092586415016`。

這是 participant-scoped rescue，不能宣稱 full-market completeness；其他股票及 transient
participants 仍未捕獲。下一步是按相同 exact symbol/broker contract 擴展既有 verified
stock universe，並維持每 stock checkpoint。
