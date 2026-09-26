# CCASS Recent Gap Dual-Path Runtime Proof V1

日期：2026-09-26（Asia/Hong_Kong）

既有 Longbridge rescue store 已 read-only inventory：49,454 rows、5 stocks、40 dates、
2026-07-31 至 2026-09-24，negative rows 0。沒有重下載相同 stock/participant/date。

固定七股 `00550, 01750, 08283, 02138, 06182, 01792, 00700` 的 7 個 detail calls 全部
成功。participant counts 為 124、98、120、167、101、118、420；平均 detail latency
4,714.2ms。49 個 selective daily calls 中 49 個 API 成功、48 個回傳非空 rows；平均 latency
4,431.8ms，觀察到 2026-08-03 至 2026-09-25 的 40-day 型窗口。

抽樣 16 個 zero-change participants，未見 false-flat；但樣本不足以證明所有 `chg_60=0`
都 flat，因此 `CHG_ZERO_SAFE_TO_SKIP=NO`。SDW 本輪沒有 request，保留作 Longbridge
不覆蓋日期、disappeared participant 或 targeted validation fallback。沒有 cross-source
exact comparison，不能宣稱兩來源已完成 reconciliation。

本輪是 performance gate proof，沒有寫入 production canonical DB；既有 checkpointed rescue
store 保持不變並已 readback。七股的 disappeared-participant union 尚未完整建立，
completeness 仍是 participant-union scoped。沒有啟動 full-market run。
