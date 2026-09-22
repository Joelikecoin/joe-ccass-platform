# TASK：D 槽併入 C 槽（Windows 11 磁碟分割手術）

> **狀態：待處理（Joe 指定聽日先做）**
> **前置安全：** 分割區手術（DiskGenius 步驟 4）之前，確認 H 槽（3TB HDD）或其他地方已有重要資料備份。
> **唔准掂：** H:\、E:\、G:\ 槽（CCASS 項目數據全部喺 H 槽）。

## 磁碟 0（MSI S270 960GB SSD）分割區排列（已核實）

```text
P1 System 100MB → P2 MSR 16MB → P3 C: 393.3GB → P4 Recovery 0.8GB → P5 D: 500GB
※ C 同 D 之間夾住 Recovery 分割區 → Windows 磁碟管理做唔到 extend
  要用 DiskGenius / 傲梅分區助手（免費版）先搬 Recovery 去碟尾
```

## D 槽現有內容（約 17GB）與處置

| 項目 | 大小 | 處置 |
|---|---|---|
| `D:\WEBBSITE_CCASS_EXTRACT`（ccassData-2025-12-27- 600.sql 17,059,800,013 bytes + webbsite_selective.sqlite 2,674,688 bytes） | 16.3GB | 已核實係 H:\...\David_Webb_CCASS_Research_Pack\WEBBSITE_CCASS_EXTRACT 嘅完整副本。**開工前再用 certutil hash 核實兩邊一致，一致就直接刪** |
| `D:\MT4` / `D:\MT File` | 472MB / 8MB | 搬去 C:\Users\Joe Lau\Documents\ 再核對 |
| `D:\xwechat_files` | 93MB | WeChat 儲存區——搬返 C:\Users\Joe Lau\xwechat_files + 改兩處設定（見下） |
| `D:\ProgramData` | 19MB | 睇下入面係咩先決定搬邊度 |
| `D:\$RECYCLE.BIN` | — | 清埋 |

### WeChat 兩處設定（改之前 Weixin.exe 必須已關閉）

```text
a) registry HKCU\Software\Tencent\Weixin 嘅 FileSavePath = D:\xwechat_files
   → 改做 C:\xwechat_files（注意：係 C:\xwechat_files 唔係 C:\Users\...\xwechat_files）
b) C:\Users\Joe Lau\AppData\Roaming\Tencent\xwechat\config\51a1fffea11325a1e4104c6b3de47af7.ini
   內容 "D:\" → 改做 "C:\"
備份檔：C:\Users\Joe Lau\weixin-registry-backup.reg
```

## 執行順序

1. certutil hash 核實 D 同 H 嘅 WEBBSITE_CCASS_EXTRACT 一致 → 一致直接刪 D 嗰份
2. 搬 MT4／MT File／ProgramData 去 C 槽合適位置；xwechat_files 搬返 C + 改 WeChat 兩處設定
3. 確認 D 槽冇任何有用嘢（清回收桶）；**D 槽分割區唔使刪**，留俾 DiskGenius
4. 【GUI 手動】DiskGenius：a) Recovery 搬去碟尾 b) 刪 D 分割區 c) C 擴充到 ~893GB d) 套用（PreOS 重啟）
5. 重啟後收尾：Get-Partition 確認單一大 C → reagentc /info（disabled 就 /disable+/enable）→ 開 WeChat 驗證 → MT4 開一次驗證

## ⚠️ 交叉依賴：CCASS Webb 17GB 導入工程

`import_webb_full.py` / `import_webb_stream.py`（workspace）嘅 SRC 指住 `D:\WEBBSITE_CCASS_EXTRACT\ccassData-...sql`。
D 槽刪除後：SRC 改指 H: 副本（`H:\...\David_Webb_CCASS_Research_Pack\WEBBSITE_CCASS_EXTRACT\ccassData-2025-12-27- 600.sql`）；
DST（`D:\webbsite_full.sqlite`）改放 C: 或外置。**執行 Webb 導入前先做呢個路徑更新。**

## 管理員權限

需要嘅指令用 `Start-Process -Verb RunAs` 包裝執行。

## ✅ 進度更新 2026-09-22 深夜

步驟 1-3 已由 ZCode 完成：
- ✅ D:\WEBBSITE_CCASS_EXTRACT 已刪（hash 核實兩邊一致）
- ✅ MT4 + MT File 已搬去 C:\Users\Joe Lau\Documents\
- ✅ xwechat_files 已搬去 C:\Users\Joe Lau\xwechat_files + registry FileSavePath 及 .ini 已改 C:
- ✅ ProgramData（Quark 影片快取 19.5MB）已刪
- ✅ 回收桶已清

**淨低（Joe 手動）：**
1. 開 DiskGenius（管理員）：P4 Recovery 搬去碟尾 → 刪除 D: 分割區 → C: 擴充至碟尾 → 保存更改 → PreOS 重啟
2. 重啟後：reagentc /info 確認 WinRE（斷咗就 /disable 再 /enable）
3. 開 WeChat 登入驗證 + MT4 開一次驗證
4. 叫 ZCode 做最終 partition 驗證

**決定：A5 實裝暫緩**（Joe 考慮更好介面方向中）。
