---
name: Full BMAD Project Flow
description: 自動的にBMADプロジェクトの完全なライフサイクルを実行するワークフロー。プロジェクト初期化から実装準備完了までの12ステップを、ユーザー入力なしで順次実行します。
web_bundle: true
---

# Full BMAD Project Flow

**Goal:** BMADプロジェクトの完全なライフサイクルを自動化し、プロジェクト初期化から実装準備完了状態までをユーザー入力なしで実行する。

**Your Role:** BMAD Project Flow Coordinatorとして、プロジェクトのライフサイクル管理とワークフローの統合・調整を行います。体系的かつプロセス指向で、明確な進捗報告とエラー時の詳細な説明を提供します。

---

## WORKFLOW EXECUTION ARCHITECTURE

### Core Principles

- **Autonomous Execution**: ユーザー入力を一切求めず、12個のBMADワークフローを順次実行
- **Sequential Processing**: 各ワークフローが前のワークフローの出力を使用
- **Progress Tracking**: 各ワークフローの実行状態をログ出力
- **Error Handling**: いずれかのワークフローが失敗した場合、即座に停止して報告

### Execution Rules

1. **EXECUTE SEQUENTIALLY**: 指定された順序で各ワークフローを実行
2. **WAIT FOR COMPLETION**: 各ワークフローが完了するまで待機
3. **LOG PROGRESS**: 各ワークフローの開始/完了をログ出力
4. **HANDLE ERRORS**: 失敗した場合、即座にワークフローを停止してエラーを報告
5. **GENERATE SUMMARY**: すべてのワークフロー完了後、実行サマリーを生成

### Critical Rules (NO EXCEPTIONS)

- 🛑 **NEVER** ユーザーに入力を求めない
- 📖 **ALWAYS** 各ワークフローが完了するまで待機
- 🚫 **NEVER** ワークフローの順序をスキップまたは変更しない
- 💾 **ALWAYS** 各ワークフローの実行結果を記録
- 🎯 **ALWAYS** エラーがあれば即座に報告

---

## WORKFLOW EXECUTION STEPS

以下の12個のBMADワークフローを順次実行します：

### Step 1: Workflow Initialization

**Workflow:** `/bmad:bmm:workflows:workflow-init`
**Purpose:** BMADプロジェクトの初期化とワークフローパスの設定

**Action:**
```
/bmad:bmm:workflows:workflow-init
```

**Expected Output:** プロジェクト初期化完了、ワークフローレベルとタイプの決定

---

### Step 2: Create Epics and Stories

**Workflow:** `/bmad:bmm:workflows:create-epics-and-stories`
**Purpose:** PRDとArchitectureドキュメントからエピックとストーリーを作成

**Action:**
```
/bmad:bmm:workflows:create-epics-and-stories
```

**Expected Output:** エピックファイルとストーリーファイルの生成

---

### Step 3: Sprint Planning

**Workflow:** `/bmad:bmm:workflows:sprint-planning`
**Purpose:** スプリントステータス追跡ファイルの生成と管理

**Action:**
```
/bmad:bmm:workflows:sprint-planning
```

**Expected Output:** sprint-status.yamlファイルの生成

---

### Step 4: Create Story (First)

**Workflow:** `/bmad:bmm:workflows:create-story`
**Purpose:** 最初のユーザーストーリーを作成

**Action:**
```
/bmad:bmm:workflows:create-story
```

**Expected Output:** 最初のストーリーファイルの生成

---

### Step 5: Create Story (Second)

**Workflow:** `/bmad:bmm:workflows:create-story`
**Purpose:** 2番目のユーザーストーリーを作成

**Action:**
```
/bmad:bmm:workflows:create-story
```

**Expected Output:** 2番目のストーリーファイルの生成

---

### Step 6: Develop Story

**Workflow:** `/bmad:bmm:workflows:dev-story`
**Purpose:** ストーリーの実装（コード作成）

**Action:**
```
/bmad:bmm:workflows:dev-story
```

**Expected Output:** 実装されたコードと関連テスト

---

### Step 7: Code Review

**Workflow:** `/bmad:bmm:workflows:code-review`
**Purpose:** 敵対的なレビューによるコード品質の評価

**Action:**
```
/bmad:bmm:workflows:code-review
```

**Expected Output:** コードレビューレポートと改善提案

---

### Step 8: Test Architecture Design

**Workflow:** `/bmad:bmm:workflows:testarch-test-design`
**Purpose:** テスト設計と受け入れテストの生成

**Action:**
```
/bmad:bmm:workflows:testarch-test-design
```

**Expected Output:** テスト計画と受け入れテスト

---

### Step 9: Test Automation

**Workflow:** `/bmad:bmm:workflows:testarch-automate`
**Purpose:** テスト自動化の実装

**Action:**
```
/bmad:bmm:workflows:testarch-automate
```

**Expected Output:** 自動化されたテストスイート

---

### Step 10: Test Traceability

**Workflow:** `/bmad:bmm:workflows:testarch-trace`
**Purpose:** 要求追跡マトリックスの生成と品質ゲートの評価

**Action:**
```
/bmad:bmm:workflows:testarch-trace
```

**Expected Output:** 要求追跡マトリックスと品質評価レポート

---

### Step 11: Test Review

**Workflow:** `/bmad:bmm:workflows:testarch-test-review`
**Purpose:** テスト品質の包括的レビュー

**Action:**
```
/bmad:bmm:workflows:testarch-test-review
```

**Expected Output:** テストレビューレポート

---

### Step 12: Document Project

**Workflow:** `/bmad:bmm:workflows:document-project`
**Purpose:** プロジェクトの包括的ドキュメント生成

**Action:**
```
/bmad:bmm:workflows:document-project
```

**Expected Output:** プロジェクトドキュメント

---

### Step 13: Check Implementation Readiness

**Workflow:** `/bmad:bmm:workflows:check-implementation-readiness`
**Purpose:** 実装準備完了状態の検証

**Action:**
```
/bmad:bmm:workflows:check-implementation-readiness
```

**Expected Output:** 実装準備評価レポート（PASS/CONCERNS/FAIL/WAIVED）

---

## INITIALIZATION SEQUENCE

### 1. Welcome and Status Report

以下のメッセージを出力：

```
# Full BMAD Project Flow - 開始

BMADプロジェクトの完全なライフサイクルを自動実行します。

実行するワークフロー（12ステップ）：
1. workflow-init - プロジェクト初期化
2. create-epics-and-stories - エピックとストーリー作成
3. sprint-planning - スプリント計画
4. create-story - ストーリー作成（1つ目）
5. create-story - ストーリー作成（2つ目）
6. dev-story - ストーリー実装
7. code-review - コードレビュー
8. testarch-test-design - テスト設計
9. testarch-automate - テスト自動化
10. testarch-trace - テストトレーサビリティ
11. testarch-test-review - テストレビュー
12. document-project - プロジェクトドキュメント化
13. check-implementation-readiness - 実装準備確認

各ワークフローを順次実行します...
```

### 2. Sequential Execution

各ワークフローを順次実行し、以下の形式で進捗をログ出力：

```
[Step N/13] 実行中: [workflow-name]
↓
[Step N/13] ✅ 完了: [workflow-name]
```

またはエラーの場合：

```
[Step N/13] ❌ 失敗: [workflow-name]

エラー詳細: [error details]

ワークフローを停止しました。
```

### 3. Final Execution Summary

すべてのワークフローが正常に完了した場合、以下のサマリーを生成：

```markdown
# Full BMAD Project Flow - 実行完了

## 実行ステータス: ✅ Complete

### 完了したステップ:
1. ✅ workflow-init - Completed
2. ✅ create-epics-and-stories - Completed
3. ✅ sprint-planning - Completed
4. ✅ create-story - Completed
5. ✅ create-story - Completed
6. ✅ dev-story - Completed
7. ✅ code-review - Completed
8. ✅ testarch-test-design - Completed
9. ✅ testarch-automate - Completed
10. ✅ testarch-trace - Completed
11. ✅ testarch-test-review - Completed
12. ✅ document-project - Completed
13. ✅ check-implementation-readiness - Completed

### 最終成果物の場所:
- Epics: _bmad-output/epics/
- Stories: _bmad-output/stories/
- Sprint Status: sprint-status.yaml
- Implementation: src/
- Tests: tests/
- Documentation: docs/

### 次のステップ:
プロジェクトが実装準備完了状態になりました。
引き続き実装を進めることができます。
```

---

## ERROR HANDLING

いずれかのワークフローが失敗した場合：

1. **即座に停止**: 次のワークフローには進まない
2. **エラー報告**: どのワークフローで失敗したかを明確に報告
3. **詳細な説明**: エラーの原因と可能な修正案を提示
4. **状態保存**: 成功したワークフローの出力は保持

**エラーメッセージの例:**

```markdown
# ワークフロー実行エラー

## 失敗したステップ: [Step N] [workflow-name]

## エラー詳細:
[具体的なエラー内容]

## 推奨される修正手順:
1. [修正手順1]
2. [修正手順2]
...

## 完了したステップ:
1-([N-1]). ✅ [completed workflows]

## ワークフローを停止しました。
修正後に最初からやり直すか、失敗したステップから再開してください。
```

---

## SUCCESS CRITERIA

ワークフローが成功と見なされる条件：

- ✅ 12個のステップすべてがエラーなしで完了
- ✅ check-implementation-readiness が PASS または CONCERNS（WAIVEDを含む）
- ✅ すべての成果物が正しく生成されている

---

## EXECUTION NOTES

- **自律実行**: このワークフローは完全に自律で実行されます。ユーザー入力は一切不要です。
- **時間**: 実行には数時間かかる場合があります。各ワークフローの複雑さに依存します。
- **中断**: このワークフローは中断できません。一度開始すると、完了または失敗するまで実行されます。
- **再実行**: 失敗した場合、問題を修正して最初から再実行してください。
