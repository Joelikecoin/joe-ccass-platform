# Joe Stock Intelligence Platform｜正式數據能力 Roadmap V2

> **Archived:** 2026-09-17, verbatim as issued by Joe. This document redefines the product; the actionable
> distillation lives in `PROJECT_PROGRESS_V3.md` §2 and §8. Where the two conflict, PROJECT_PROGRESS_V3.md wins
> on repo facts; this document wins on product intent.

## 核心結論

加入你最新硬性要求之後，我會將平台正式定義為：

> **以 5 年財技故事線為核心嘅 Stock Intelligence Data Layer。**
>
> 平時分析至少可以向前追溯 5 年；上市不足 5 年就追到上市。若 5 年內仍解釋唔到控股權、股本來源或人物關係，就按證據需要延伸到 10 年甚至上市日。

架構唔需要全市場預先儲晒 5 年文件，而係：

**Persistent Time-series + Historical Retrieval + Structured Evidence Cache。**

朋友兩份報告亦證明，真正高質素分析唔係「見到異動」，而係能夠判斷異動背後究竟係派貨、轉倉、無主流動性事件，定係財技部署。06890 同 01933 表面都係爆升暴跌，但最後結論完全不同，差別就在 CCASS、股本歷史、DI、成交能力及歷史事件能否串成完整故事。

---

## 一、P0_BASELINE：朋友22頁報告真正需要嘅能力

| ANALYSIS_CAPABILITY | REQUIRED_DATA | DATA_TIMEFRAME | 歷史序列 | 事件時間線 |
| ------------------- | ------------- | --------------- | :--: | :---: |
| 收貨／派貨／轉倉 | participant holdings、Changes、Top5/10、成交 | 近期完整＋歷史節點 | ✅ | |
| 貨源集中／街貨 | CCASS stake、Top5/10、非CCASS、大股東、公眾持股 | 1–5年 | ✅ | ✅ |
| 爆量／流動性異常 | OHLCV、turnover、市值、零成交日 | 3–5年 | ✅ | |
| 財技事件識別 | 配股、供股、GO、CB、合拆、回購等 | **最少5年** | | ✅ |
| 股本故事 | issued shares、發行／註銷原因 | **最少5年，必要時上市日** | ✅ | ✅ |
| 大股東行為 | DI、持股%、價格、買賣方向 | **最少5年** | ✅ | ✅ |
| 操作者成本 | GO/配股/供股/CB價＋VWAP＋大手交易 | 事件週期＋前後價格 | ✅ | ✅ |
| 人物／中介網絡 | 董事、控股人、顧問、代理、包銷商、要約人 | **最少5年** | | ✅ |
| 基本面壓力 | 盈利、NAV、現金、債務、應收、核數師 | 3–5財年 | ✅ | ✅ |
| 「有局／無局」反證 | 上述全部 | **5年基準** | ✅ | ✅ |
| 下一關鍵日期 | AGM、供股、GO、業績、月報等 | 未來12月 | | ✅ |

所以新增硬性要求之後：

> **5-Year Historical Corporate Intelligence Timeline = P0，而唔係附加 Evidence 功能。**

---

# 二、教材真正要求嘅底層數據

Project 教材入面大量策略雖然名稱不同，但去重後並冇需要建立大量新 Data Service。

例如 VCP 教材本質上用價格波幅、成交量收縮及突破條件；即底層仍然係 OHLCV。

而財技教材入面 GO、供股、配股、CB、Settle 等，真正共用嘅係：

> **Corporate Actions + Share Capital + Ownership/DI + OHLCV + CCASS。**

01933 更證明 RTSS／Settle 唔應成為獨立數據平台：爆量訊號需要配合 CCASS 集中度方向先可以排除派貨型爆升。

因此教材去重後，核心仍然係以下 7 個 Data Domain：

1. **Market Data**
2. **CCASS**
3. **Share Capital**
4. **Corporate Actions / 5-Year Timeline**
5. **Ownership / DI**
6. **Fundamentals**
7. **People / Intermediaries / Evidence**

VCP、RTSS、Settle、派貨、收貨、殼價等全部屬於 **Derived Intelligence**，唔係另一套原始數據服務。呢個方向亦同之前 Roadmap 審計一致。

---

# 三、5年財技故事線應該點儲

我建議正式鎖定三層架構：

```text
A. Persistent Time-series
   CCASS / OHLCV / issued shares snapshots

B. 5-Year Historical Retrieval
   HKEX公告 / DI / 通函 / 年報 / 人物 / 中介

C. Structured Evidence Cache
   已經解析及核實過嘅關鍵事件永久保存
```

即係例如第一次分析某股票：

```text
2021 配股
2022 控股人變更
2023 合股
2024 供股
2025 CCASS集中
2026 爆量
```

平台先抓出 5 年索引及相關文件，然後將真正高價值資料結構化：

```text
event_type
announce_date
effective_date
shares_before
shares_after
price
ratio
discount
counterparty
beneficial_owner
placing_agent
adviser
source_document
confidence
```

**原 PDF 未必要永久存晒，但已驗證事實唔應該下次重新做。**

---

# 四、MASTER ANALYSIS CAPABILITY MATRIX

| 能力 | 歷史要求 | 朋友報告 | 教材 | Joe現況 | 狀態 | 優先 |
| --- | --- | :--: | :-: | --- | --- | --- |
| CCASS current holdings | 即日 | ✅ | 極高 | 已有 production chain | **READY** | P0 |
| CCASS persistent history | 近期＋歷史重建 | ✅ | 極高 | 目前 production真正連續日期仍有限 | **PARTIAL** | P0 |
| Changes / Big Changes / Concentration | 由 snapshots derive | ✅ | 極高 | 已可做近期 | **PARTIAL** | P0 |
| OHLCV / Turnover | 5年較理想 | ✅ | 極高 | service存在但 production深度未完全證實 | **PARTIAL** | P0 |
| Share Capital History | **至少5年** | ✅ | 極高 | 約5年範圍曾證實 | **接近 READY** | P0 |
| **5-Year Corporate Timeline** | **至少5年** | ✅ | 極高 | 部分 service存在，未完成統一事件層 | **PARTIAL** | **P0** |
| HKEX Announcements | **至少5年可Retrieve** | ✅ | 高 | code有，production歷史能力未完整證實 | **PARTIAL** | P0 |
| DI / Ownership | **至少5年** | ✅ | 高 | 尚無完整 dedicated service | **MISSING** | P0 |
| Major Shareholders | **至少5年** | ✅ | 高 | 尚未完整 | **MISSING** | P0 |
| Financial Fundamentals | 3–5年 | ✅ | 高 | 未形成完整 normalized layer | **MISSING/PARTIAL** | P0 |
| Directors / Key Persons | **至少5年** | ✅ | 中高 | current officers有，historical未完整 | **PARTIAL** | P0 |
| Advisers / Intermediaries | **至少5年** | ✅ | 高 | 無 dedicated history | **MISSING** | P0 |
| Shell valuation engine | 3–5年 | ✅ | 中 | 部分可算 | PARTIAL | P1 |
| VCP/technical scanner | 1–3年 OHLCV | ❌ | 高 | 底層資料即可 | 不需新data | P2 |
| Tick / Level 2 history | 日/月級 | 少量 | 中 | 無 | MISSING | P2 |
| Rainbow/UI/Exports | — | ❌ | 低 | 部分已有 | 不影響分析 | UNNECESSARY |

> **V3 note:** the "Joe現況" column above predates the DI / document-entities / fundamentals component work.
> See PROJECT_PROGRESS_V3.md §5 for the corrected status (those domains are COMPONENT_PASS, not MISSING).

現有最新平台審計亦支持呢個判斷：目前 Holdings→Longbridge→Turso→API/8504 已經完成；但 5 年層面，DI、Major Shareholders、Advisers、Financial/Audit events 仍明顯缺失，而 Officers 主要仍然係 current snapshot。

---

# 五、現時 Joe Platform 最重要嘅差距

有一個判斷要同較早 Roadmap 更新：

### CCASS current production 已經唔係最大問題

你最新平台證據已確認 P0 current chain：

> Longbridge → validate → normalize → Turso → service/API → 8504

而 Holdings、Changes、Big Changes、Concentration 基礎 production chain 已經成功。

所以而家真正產品瓶頸已經由：

> 「攞唔攞到 CCASS？」

逐步變成：

> **「AI 可唔可以知道呢隻股票過去5年發生過乜？」**

呢個係 Roadmap 應該轉軸嘅位置。

---

# 六、最終四個開發答案

## 1. 現有平台必須繼續完成

最重要係以下四類：

**第一：5-Year Historical Corporate Intelligence Timeline。**

統一整合：

* Announcements
* Corporate Actions
* Share Capital
* DI
* Major Shareholders
* Directors
* Advisers / intermediaries

所有事件都必須有日期、來源、原文證據及 temporal identity。

**第二：CCASS Historical Layer。**

Current 已成功，但仍要補歷史：

* Webb historical seed
* recent/current Longbridge
* 中段完整快照來源
* historical Top5/10、Changes、broker history

**第三：OHLCV / Turnover canonical history。**

要有足夠歷史畀 AI 對照財技事件前後價格及成交。

**第四：Financial Fundamentals normalization。**

特別係：

`Revenue / Profit / NAV / Cash / Debt / Receivables / OCF / Auditor / Going Concern`

## 2. 目前應停止投入時間

以下唔應該成為近期 P0：

* Rainbow 視覺美化
* Excel／Download 功能擴張
* 朋友網站 UI 1:1 Clone
* 獨立 VCP／Cup／Supertrend 頁
* Tick／Level 2 長歷史
* AI報告排版美化
* 為每種策略建立獨立資料庫
* 另一套 CCASS persistence architecture

平台以前嘅工程治理其實亦明確指出，P0 成功唔應該由 UI、下載、report 或 HTTP 200 定義，而係真實資料完整鏈。

## 3. 現時最重要缺失

按分析價值排序：

**① DI / Beneficial Ownership History**

而家最大洞。

朋友 01933 報告甚至直接指出，若有完整 DI，就可以將 Chance Talent 撤退由 CCASS 推理升格為已查證事實。

**② 5-Year Corporate Action + Announcement Retrieval**

唔係單純「有公告列表」，而係可由 AI 查：

> 五年前有冇配股？誰參與？當時股數？之後有冇合股？今日成本如何換算？

**③ Historical People / Intermediary Graph**

人物唔只係 current officers，要知道：

> 邊個幾時入場、離場，同邊間券商／財顧／配售代理共同出現。

**④ Normalized Financial Fundamentals**

否則 AI 只識「發生咗乜」，但未必識：

> **點解公司有動機做呢件事。**

**⑤ CCASS historical gap closure**

Current 已成功，但歷史完整鏈仍未完全 READY。最新審計仍只證實 very recent genuine snapshots；五年要求未由 production current chain 自動滿足。

---

# 七、下一個最值得開發5項能力｜ROI

我會正式改成以下順序：

| ROI | 下一項能力 | 原因 |
| --- | --- | --- |
| 🥇 | **5-Year Historical Corporate Intelligence Engine** | 一次補齊公告、財技事件、股本故事線；直接決定深度報告完整性 |
| 🥈 | **DI / Ownership Engine** | 將大股東／控制權／減持由推測變事實 |
| 🥉 | **CCASS Historical Gap Closure** | 令「現在貨源」可以放入長期變化背景 |
| 4 | **Financial Fundamentals Layer** | 解釋財技動機、資金壓力、殼價及風險 |
| 5 | **Historical People / Intermediary Entity Graph** | 提升人物網絡、代理／顧問重複出現及換班判斷 |

### 我暫時唔會將 Monitor Engine 放 Top 5。

原因好簡單：

> **未建立完整 Intelligence Layer，就太早建立 Monitor。**

否則 Monitor 只會高速提醒：

> 「今日爆量、Top5變化。」

但未必知道：

> 「原來佢三年前供股、兩年前換主、去年配股，而今日呢次爆量係上一輪貨源退出嘅最後一步。」

所以正確順序係：

**先做到識理解故事，再自動監察故事有冇新一章。**

---

# 最終產品架構

我會將整個 Roadmap 鎖成：

```text
P0 DATA FOUNDATION
│
├─ Market Data
│   └─ OHLCV / Turnover / Market Cap
│
├─ CCASS
│   └─ Current + Historical
│
├─ 5-Year Corporate Intelligence
│   ├─ Announcements
│   ├─ Corporate Actions
│   ├─ Share Capital
│   ├─ DI / Ownership
│   ├─ Major Shareholders
│   ├─ Directors
│   └─ Advisers / Intermediaries
│
├─ Fundamentals
│
└─ Evidence / Provenance
        ↓
DERIVED INTELLIGENCE
        ↓
AI 20–30頁深度財技報告
        ↓
MONITOR / ALERTS
```

而5年規則正式係：

> **Default = 5 years / listing date if younger.
> Evidence-triggered extension = up to 10 years or listing date.**

呢個版本我認為已經比之前 Roadmap 更準確：**Joe Platform 下一階段唔應再以「CCASS網站完成度」為主，而要正式升級做「5年公司財技情報層」。** Current CCASS 係重要底座，但唔再係全部。
