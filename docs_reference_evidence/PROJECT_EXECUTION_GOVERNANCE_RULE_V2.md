# Project Execution Governance Rule V2

## 1. One Active Milestone Rule

同一時間只允許一個 Active Milestone。

流程：

Approved Scope
↓
Implementation
↓
CTO Review
↓
Testing / Validation
↓
Joe Acceptance
↓
Next Milestone

禁止：

- 未完成當前 Milestone 前開始新的 Implementation
- 未批准 Scope 前建立 Codex Task

## 2. Review Scope Rule

所有 Review 必須以 Current Change Set 為中心。

Review 只檢查：

- Changed Files
- Changed Modules
- Changed API
- Changed Data Contract
- 受影響 User Flow

禁止重新審查：

- 已完成並接受的 Milestone
- 未被本次修改影響的 Approved Baseline

Testing 原則：

不是減少 Testing。

而是避免重複 Testing。

只執行：

- Current Change Set 相關 Tests
- 必要 Regression Tests

如發現既有問題：

- 判斷是否由 Current Change 引起
- 若不是，標記為 Existing Issue
- 不阻塞目前 Milestone Acceptance

## 3. Acceptance Boundary Rule

每個 Milestone 必須具備：

- Scope
- Acceptance Criteria
- Definition of Done

完成流程：

Requirement
↓
Implementation
↓
CTO Review
↓
Testing Evidence
↓
Joe Acceptance

Approved Baseline Protection：

已接受 Milestone：

- 不因後續 Review 重新審查
- 不因新建議重新修改
- 不作為後續 Milestone 阻塞條件

除非：

- New Requirement
- Architecture Change
- Breaking Issue
- Security / Data Integrity Issue

## 4. Cost Control Rule

所有回答與分析：

必須從：

Current Project Status

開始。

禁止：

- 重新整理完整 Project History
- 重複解釋已批准決策
- 重複檢查未變更部分

優先：

Current State
↓
Current Decision
↓
Next Action

## 5. Project Context Protection Rule

禁止每次 Implementation 重建完整背景。

只引用：

- Current Milestone
- Existing Approved Baseline
- Relevant Architecture

完整 Project Summary 只在：

- Architecture Major Change
- CTO 要求
- 新角色 Onboarding

時生成。

## 6. Codex Execution Rule

Codex Prompt 應保持最小化。

只需要：

- Milestone
- Objective
- Scope
- Acceptance Criteria
- Tests

固定 Governance 不需要重複放入每次 Prompt。

## 7. Existing Issue Handling Rule

發現問題時：

先分類：

Current Change Issue

或

Existing Issue

只有 Current Change Issue 阻塞目前 Milestone。

## 8. Objective

目標：

保持：

- 工程品質
- 架構穩定
- 測試可信度

同時避免：

- 重複分析
- 重複 Review
- 重複 Testing
- 不必要 Token 消耗
