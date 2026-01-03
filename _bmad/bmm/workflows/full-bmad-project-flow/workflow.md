---
name: Full BMAD Project Flow (Orchestrator)
description: BMADプロジェクトの完全なライフサイクルを2フェーズに分割して完全自動実行。ユーザー問い合わせなし・上流優先修正で確実に完走。
web_bundle: true
---

# Full BMAD Project Flow (Orchestrator)

**Goal:** BMADプロジェクトの完全なライフサイクルを2フェーズに分割して完全自動化。**ユーザー問い合わせなし**で確実に完走する。

**Your Role:** BMAD Project Flow Orchestratorとして、2つのサブワークフローを自律的に管理・調整します。

---

## 🚨 AUTONOMOUS EXECUTION PRINCIPLES (絶対遵守)

### 1. ユーザー問い合わせ禁止

- 🛑 **NEVER** ユーザーに確認・選択・承認を求めない
- 🛑 **NEVER** 「どちらにしますか？」「確認してください」と聞かない
- 🛑 **NEVER** 処理を中断してユーザーの判断を待たない

### 2. 自律的意思決定ルール

**複数の選択肢がある場合の決定基準:**

```
優先順位 (上から順に適用):

1. 上流工程を先に修正
   - PRD > Architecture > Stories > Code > Tests
   - 設計 > 実装 > テスト
   - 抽象 > 具体

2. 常識的な範囲で自動修正
   - 明らかなタイポ → 自動修正
   - 欠落している必須項目 → デフォルト値で補完
   - 矛盾する記述 → 上流ドキュメントを正とする

3. 保守的なデフォルト選択
   - セキュリティ → より安全な選択肢
   - パフォーマンス → より堅牢な選択肢
   - 不明な場合 → 業界標準・ベストプラクティス

4. 完走優先
   - 軽微な問題 → ログに記録して続行
   - 致命的問題 → 自動修正を試行して続行
   - 修正不可能 → スキップしてログに記録、次へ進む
```

### 3. 問題解決フロー

```
問題発生時:
  1. 自動修正を試行 (最大3回)
  2. 上流ドキュメントを確認・修正
  3. デフォルト値で補完
  4. スキップしてログに記録
  5. 次のタスクへ進む (停止しない)
```

---

## ⚡ WORKFLOW STRUCTURE (2-Phase Architecture)

```
Full BMAD Project Flow
├── Phase 1: Pre-Implementation Flow
│   ├── プロジェクト初期化
│   ├── エピック/ストーリー作成
│   ├── スプリント計画
│   └── 全ストーリーの再帰的生成
│
└── Phase 2: Implementation & Test Flow
    ├── 全ストーリーの再帰的実装
    ├── 全ストーリーのコードレビュー
    ├── テスト設計・自動化・トレーサビリティ・レビュー
    ├── ドキュメント生成
    └── 最終チェック
```

---

## 🚀 EXECUTION (完全自動)

### 実行コマンド:

```
# 両フェーズを連続実行 (推奨)
/bmad:bmm:workflows:full-bmad-project-flow

# Phase 1のみ
/bmad:bmm:workflows:full-bmad-project-flow:1-pre-implementation-flow

# Phase 2のみ (Phase 1完了後)
/bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow

# 再開
/bmad:bmm:workflows:full-bmad-project-flow:1-pre-implementation-flow --resume
/bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow --resume
```

---

## 🎯 FULL WORKFLOW EXECUTION SEQUENCE

### Initialization:

```
# Full BMAD Project Flow (Orchestrator) - 完全自動実行開始

🤖 自律実行モード: ユーザー問い合わせなし
📐 意思決定ルール: 上流優先修正

📌 Phase 1: Pre-Implementation Flow
📌 Phase 2: Implementation & Test Flow

完全自動で完走します...
```

### Execution:

```
1. Create orchestrator progress file
2. Execute Phase 1 (autonomous)
3. Verify Phase 1 completion
4. Execute Phase 2 (autonomous)
5. Generate final summary
```

---

## 📊 PROGRESS TRACKING

```
_bmad-output/workflow-progress/
├── pre-implementation-progress.yaml
├── implementation-test-progress.yaml
├── orchestrator-progress.yaml
└── decision-log.yaml  # 自律的意思決定のログ
```

### Decision Log Format:

```yaml
decisions:
  - timestamp: [ISO 8601]
    phase: 1
    step: create-story
    issue: "受け入れ基準が不明確"
    decision: "PRDから推論して補完"
    rationale: "上流優先修正ルール適用"
    
  - timestamp: [ISO 8601]
    phase: 2
    step: dev-story
    issue: "依存ライブラリのバージョン未指定"
    decision: "最新安定版を使用"
    rationale: "業界標準デフォルト適用"
```

---

## 📝 FINAL SUMMARY

```markdown
# Full BMAD Project Flow - 完了

## 実行ステータス: ✅ Complete

### 自律的意思決定:
- 総決定数: [count]
- 上流修正: [count]
- デフォルト適用: [count]
- スキップ: [count]

### Phase 1: Pre-Implementation Flow
- Status: ✅ Completed
- Epics: [count]
- Stories: [count]

### Phase 2: Implementation & Test Flow
- Status: ✅ Completed
- Implementations: [count]
- Reviews: [count]
- Tests: [count]

### 成果物:
- Epics: _bmad-output/epics/
- Stories: _bmad-output/stories/
- Source: src/
- Tests: tests/
- Docs: docs/
- Decision Log: _bmad-output/workflow-progress/decision-log.yaml
```

---

## ✅ SUCCESS CRITERIA

- ✅ ユーザー問い合わせなしで完走
- ✅ Phase 1 完了
- ✅ Phase 2 完了
- ✅ すべての成果物が生成
- ✅ 意思決定ログが記録

---

## 📚 RELATED WORKFLOWS

- [1-pre-implementation-flow.md](1-pre-implementation-flow.md)
- [2-implementation-test-flow.md](2-implementation-test-flow.md)
