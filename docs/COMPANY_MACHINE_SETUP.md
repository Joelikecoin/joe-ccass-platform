# 公司電腦建站指南（C 槽工程檔）

> 用途：喺公司電腦由零建立 joe-ccass-platform 工程環境，接上兩機同步流程。
> 權威來源：Git repo（永遠）。雲端 H: 只係鏡像同證據庫。
> 建立日期：2026-09-18

## 一、一次性安裝（公司機）

1. 安裝 **Git**：https://git-scm.com/download/win （一路 Next 即可）
2. 安裝/登入 **ZCode**（用同一個帳號）
3. 測試公司網絡擋唔擋 GitHub：瀏覽器開 https://github.com/Joelikecoin/joe-ccass-platform 睇到就行；
   擋嘅話問 IT 開白名單，或者用手機 hotspot 做第一次 clone

## 二、建立 C 槽工程檔

喺 ZCode 或 cmd 入面逐句行：

```text
cd C:\Users\<你嘅用戶名>\.zcode\workspace\default
git clone https://github.com/Joelikecoin/joe-ccass-platform
cd joe-ccass-platform
git checkout p0-runtime-api-key-fingerprint-proof
git log --oneline -1
```

✅ 驗證：最後一句應該見到 `57d113b` **或者更新**嘅 commit。

## 三、Credentials（.env 唔會經 Git 同步——要重新輸入一次，約 5 分鐘）

1. 喺 repo 根目錄開一個新檔案叫 `.env`（Git 已設定永遠忽略佢）
2. 填入三行（數值來源）：

```text
RENDER_API_KEY=rnd_xxx        ← dashboard.render.com → Account Settings → API Keys → 開條新 key（建議叫 company）
TURSO_DATABASE_URL=libsql://… ← Render dashboard → joe-ccass-api → Environment → copy
TURSO_AUTH_TOKEN=eyJ…         ← 同上
```

⚠️ 安全規矩：
- **唔好將 .env 放上雲端/Email/chat**——唔見 key 就去 Render/Turso 撤銷重開，5 分鐘搞掂
- .env 永遠唔 commit（.gitignore 第 1 行已保護）

## 四、接上進度

```text
read PROJECT_PROGRESS_V3.md §12
```

呢句咒語喺任何機、任何 session 貼俾 ZCode 就即刻接上（§12 有：已批准任務、根因、驗證步驟）。

## 五、兩部機分工（重要）

| 工作 | 屋企機 | 公司機 |
|---|---|---|
| Code 修改、Render 驗證、API 測試、文檔 | ✅ | ✅ |
| DI 異步 job 開發（Phase 0.2 下一步） | ✅ | ✅ |
| Webb 歷史抽取/重建（需要 D:\ 17GB dump + selective index） | ✅ | ❌ 做唔到（公司機冇呢啲檔案） |
| 讀朋友解題包/證據（H: 雲端） | ✅ | ✅（如果公司機裝咗 Google Drive、掛載 H: 同一條路徑） |

## 六、規矩（不變）

- 開工前 `git pull`；每完成一個工作點 → 更新 V3 → `git commit` + `git push`
- 收工時 V3 §12 要反映最新狀態（`ALL_WORK_PUSHED_THROUGH=<commit>`）
- 雲端 H: 上嘅 `latest_reference_updates` = 朋友證據權威；其他 H: 資料夾可能過時
