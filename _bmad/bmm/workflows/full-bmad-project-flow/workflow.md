---
name: Full BMAD Project Flow (Orchestrator)
description: BMADプロジェクトの完全なライフサイクルを2フェーズに分割して実行。大規模プロジェクトでも最後まで完走できるよう、実装前フェーズと実装/テストフェーズに分離。
web_bundle: true
---

# Full BMAD Project Flow (Orchestrator)

**Goal:** BMADプロジェクトの完全なライフサイクルを2フェーズに分割して自動化。大規模プロジェクトでも確実に完走できる。

**Your Role:** BMAD Project Flow Orchestratorとして、2つのサブワークフローを管理・調整します。

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

## 🚀 EXECUTION OPTIONS

### Option 1: 両フェーズを連続実行

```
/bmad:bmm:workflows:full-bmad-project-flow
```

両フェーズを順次実行します。進捗は各フェーズの進捗ファイルで追跡されます。

### Option 2: フェーズ1のみ実行（推奨：初回）

```
/bmad:bmm:workflows:full-bmad-project-flow:1-pre-implementation-flow
```

実装前フェーズのみを実行。すべてのストーリーが生成されたことを確認してからフェーズ2に進めます。

### Option 3: フェーズ2のみ実行

```
/bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow
```

⚠️ **Prerequisites:** フェーズ1が完了していること

### Option 4: 中断からの再開

```
# フェーズ1から再開
/bmad:bmm:workflows:full-bmad-project-flow:1-pre-implementation-flow --resume

# フェーズ2から再開
/bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow --resume
```

---

## 📊 PROGRESS TRACKING

### 進捗ファイルの場所:

```
_bmad-output/workflow-progress/
├── pre-implementation-progress.yaml    # フェーズ1の進捗
├── implementation-test-progress.yaml   # フェーズ2の進捗
└── orchestrator-progress.yaml          # 全体の進捗
```

### Orchestrator Progress File:

```yaml
workflow: full-bmad-project-flow
version: "2.0"
started_at: [timestamp]
updated_at: [timestamp]
status: not_started | phase1_running | phase1_complete | phase2_running | completed | failed

phases:
  phase1:
    name: pre-implementation-flow
    status: not_started | running | completed | failed
    progress_file: _bmad-output/workflow-progress/pre-implementation-progress.yaml
    
  phase2:
    name: implementation-test-flow
    status: not_started | running | completed | failed
    progress_file: _bmad-output/workflow-progress/implementation-test-progress.yaml

overall_completion: 0%  # 0-100
```

---

## 🔄 PHASE EXECUTION DETAILS

### Phase 1: Pre-Implementation Flow

**ファイル:** `1-pre-implementation-flow.md`

**実行内容:**
1. **workflow-init** - プロジェクト初期化
2. **create-epics-and-stories** - エピックとストーリーのスタブ作成
3. **sprint-planning** - スプリント計画
4. **recursive-story-generation** - 🔁 **全ストーリーを再帰的に生成**

**特徴:**
- ストーリー数に関係なく、すべてのストーリーを自動生成
- 進捗追跡で中断・再開をサポート
- 完了後、すぐにフェーズ2に進める状態

**成果物:**
- `_bmad-output/epics/*.md`
- `_bmad-output/stories/*.md` (完全な状態)
- `sprint-status.yaml`

---

### Phase 2: Implementation & Test Flow

**ファイル:** `2-implementation-test-flow.md`

**実行内容:**
1. **implementation-phase** - 🔁 **全ストーリーを再帰的に実装**
2. **review-phase** - 🔁 **全ストーリーをレビュー**
3. **test-phase** (4サブフェーズ):
   - test-design
   - test-automate
   - test-trace
   - test-review
4. **documentation-phase** - ドキュメント生成
5. **final-check-phase** - 実装準備確認

**特徴:**
- ストーリー単位で実装・レビューを反復
- 依存関係を考慮した実行順序
- 自動リトライ機能
- 品質メトリクスの収集

**成果物:**
- `src/` - ソースコード
- `tests/` - テストスイート
- `docs/` - ドキュメント
- 品質レポート

---

## 🎯 FULL WORKFLOW EXECUTION

このファイルから両フェーズを連続実行する場合:

### Initialization:

```
# Full BMAD Project Flow (Orchestrator) - 開始

2フェーズ構成でBMADプロジェクトライフサイクルを実行します。

📌 Phase 1: Pre-Implementation Flow
   - プロジェクト初期化
   - エピック/ストーリー作成
   - スプリント計画
   - 全ストーリーの再帰的生成

📌 Phase 2: Implementation & Test Flow
   - 全ストーリーの再帰的実装
   - 全ストーリーのコードレビュー
   - テストフェーズ (設計/自動化/トレース/レビュー)
   - ドキュメント生成
   - 最終チェック

⚡ 各フェーズは中断・再開が可能です。
📊 進捗は _bmad-output/workflow-progress/ で追跡されます。

Phase 1 を開始します...
```

### Execution Sequence:

```
1. Create orchestrator progress file
2. Execute Phase 1:
   /bmad:bmm:workflows:full-bmad-project-flow:1-pre-implementation-flow
3. Verify Phase 1 completion
4. Execute Phase 2:
   /bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow
5. Generate final summary
```

---

## 📝 FINAL SUMMARY

```markdown
# Full BMAD Project Flow - 完了

## 実行ステータス: ✅ Complete

### Phase 1: Pre-Implementation Flow
- Status: ✅ Completed
- Epics generated: [count]
- Stories generated: [count]
- Duration: [time]

### Phase 2: Implementation & Test Flow
- Status: ✅ Completed
- Stories implemented: [count]
- Reviews completed: [count]
- Tests created: [count]
- Duration: [time]

### 品質メトリクス:
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Code Coverage | 87% | 80% | ✅ |
| Tests Passed | 142 | - | ✅ |
| Review Score | 8.5/10 | 7/10 | ✅ |

### 成果物:
- Epics: _bmad-output/epics/
- Stories: _bmad-output/stories/
- Source: src/
- Tests: tests/
- Docs: docs/

### 総実行時間: [total time]

プロジェクトが実装完了状態になりました。
```

---

## ❌ ERROR HANDLING

フェーズが失敗した場合:

1. **進捗を保存**: 次の再開時に使用
2. **失敗フェーズを報告**: どのフェーズ・ステップで失敗したか
3. **再開方法を提示**: 適切な再開コマンド

```markdown
# ワークフロー実行エラー

## 失敗したフェーズ: Phase [1/2] - [phase-name]

## エラー詳細:
[具体的なエラー内容]

## 完了した作業:
[list of completed items]

## 再開方法:
問題を修正後、以下を実行:
  /bmad:bmm:workflows:full-bmad-project-flow:[1/2]-[flow-name] --resume
```

---

## ✅ SUCCESS CRITERIA

- ✅ Phase 1 がエラーなしで完了
- ✅ すべてのストーリーが生成されている
- ✅ Phase 2 がエラーなしで完了
- ✅ すべてのストーリーが実装・レビュー済み
- ✅ テストフェーズ完了
- ✅ 最終チェックが PASS または CONCERNS

---

## 📚 RELATED WORKFLOWS

- [1-pre-implementation-flow.md](1-pre-implementation-flow.md) - 実装前フェーズの詳細
- [2-implementation-test-flow.md](2-implementation-test-flow.md) - 実装/テストフェーズの詳細
