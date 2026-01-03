````markdown
---
name: Pre-Implementation Flow
description: BMADプロジェクトの実装前フェーズを自動実行。プロジェクト初期化〜すべてのストーリー生成まで。ストーリーを再帰的に全件生成し、進捗管理を完備。
web_bundle: true
---

# Pre-Implementation Flow

**Goal:** BMADプロジェクトの実装前フェーズを完全自動化。プロジェクト初期化から全ストーリーの生成まで、ユーザー入力なしで実行する。

**Your Role:** Pre-Implementation Flow Coordinatorとして、計画フェーズの管理と成果物生成を統括します。

---

## PHASE SCOPE

このワークフローは以下をカバー:
- ✅ プロジェクト初期化
- ✅ エピック・ストーリー作成 (全件再帰生成)
- ✅ スプリント計画
- ✅ 実装準備の基盤構築

---

## PROGRESS TRACKING SYSTEM

### Progress File: `_bmad-output/workflow-progress/pre-implementation-progress.yaml`

ワークフロー実行時に以下の進捗ファイルを作成・更新:

```yaml
workflow: pre-implementation-flow
started_at: [ISO 8601 timestamp]
updated_at: [ISO 8601 timestamp]
status: in_progress | completed | failed | paused

steps:
  - id: 1
    name: workflow-init
    status: pending | running | completed | failed | skipped
    started_at: null
    completed_at: null
    output_files: []
    errors: []

  - id: 2
    name: create-epics-and-stories
    status: pending
    started_at: null
    completed_at: null
    output_files: []
    epics_generated: 0
    stories_generated: 0
    errors: []

  - id: 3
    name: sprint-planning
    status: pending
    started_at: null
    completed_at: null
    output_files: []
    errors: []

  - id: 4
    name: recursive-story-generation
    status: pending
    started_at: null
    completed_at: null
    stories_total: 0
    stories_completed: 0
    story_details: []
    errors: []

current_step: 1
total_steps: 4
completion_percentage: 0
```

### Progress Update Protocol

各ステップの開始時:
```yaml
steps[N].status: running
steps[N].started_at: [current timestamp]
current_step: N
```

各ステップの完了時:
```yaml
steps[N].status: completed
steps[N].completed_at: [current timestamp]
steps[N].output_files: [list of generated files]
completion_percentage: (completed_steps / total_steps) * 100
```

---

## WORKFLOW EXECUTION STEPS

### Step 1: Workflow Initialization

**Workflow:** `/bmad:bmm:workflows:workflow-init`
**Purpose:** BMADプロジェクトの初期化とワークフローパスの設定

**Pre-execution:**
1. 進捗ファイルを作成: `_bmad-output/workflow-progress/pre-implementation-progress.yaml`
2. Step 1 のステータスを `running` に更新

**Action:**
```
/bmad:bmm:workflows:workflow-init
```

**Post-execution:**
1. 生成されたファイルを `output_files` に記録
2. Step 1 のステータスを `completed` に更新

**Expected Output:**
- プロジェクト初期化完了
- ワークフローレベルとタイプの決定
- `_bmad-output/` ディレクトリ構造の作成

---

### Step 2: Create Epics and Stories

**Workflow:** `/bmad:bmm:workflows:create-epics-and-stories`
**Purpose:** PRDとArchitectureドキュメントからエピックとストーリーを作成

**Pre-execution:**
1. Step 2 のステータスを `running` に更新

**Action:**
```
/bmad:bmm:workflows:create-epics-and-stories
```

**Post-execution:**
1. 生成されたエピック/ストーリーファイルをカウント
2. `epics_generated` と `stories_generated` を更新
3. Step 2 のステータスを `completed` に更新

**Expected Output:**
- `_bmad-output/epics/` 配下にエピックファイル
- `_bmad-output/stories/` 配下にストーリーファイル (スタブ)

---

### Step 3: Sprint Planning

**Workflow:** `/bmad:bmm:workflows:sprint-planning`
**Purpose:** スプリントステータス追跡ファイルの生成と管理

**Pre-execution:**
1. Step 3 のステータスを `running` に更新

**Action:**
```
/bmad:bmm:workflows:sprint-planning
```

**Post-execution:**
1. `sprint-status.yaml` のパスを記録
2. Step 3 のステータスを `completed` に更新

**Expected Output:**
- `sprint-status.yaml` ファイルの生成
- スプリントバックログの初期化

---

### Step 4: Recursive Story Generation (ALL Stories)

**Purpose:** すべてのストーリーを再帰的に生成

**Pre-execution:**
1. Step 4 のステータスを `running` に更新
2. `_bmad-output/stories/` 配下のストーリースタブをスキャン
3. `stories_total` を設定

**RECURSIVE GENERATION LOOP:**

```
FOR each story_stub IN _bmad-output/stories/*.md:
    IF story_stub.status == "stub" OR story_stub.status == "incomplete":

        1. Update progress:
           story_details.append({
               id: story_id,
               name: story_name,
               status: "generating",
               started_at: timestamp
           })

        2. Execute:
           /bmad:bmm:workflows:create-story [story_id]

        3. Validate output:
           - Check acceptance criteria exist
           - Check technical requirements defined
           - Check dependencies listed

        4. Update progress:
           story_details[story_id].status = "completed"
           story_details[story_id].completed_at = timestamp
           stories_completed += 1

        5. Log progress:
           "[Story N/M] ✅ 完了: {story_name}"

    ELSE:
        Log: "[Story N/M] ⏭️ スキップ (既存): {story_name}"
        stories_completed += 1
END FOR
```

**Post-execution:**
1. すべてのストーリーが生成されたことを確認
2. Step 4 のステータスを `completed` に更新
3. 最終進捗サマリーを出力

**Expected Output:**
- すべてのストーリーファイルが完全な状態で生成
- 各ストーリーに以下が含まれる:
  - ユーザーストーリー (As a... I want... So that...)
  - 受け入れ基準
  - 技術要件
  - 依存関係
  - 見積もり

---

## INITIALIZATION SEQUENCE

### 1. Welcome and Status Report

以下のメッセージを出力:

```
# Pre-Implementation Flow - 開始

BMADプロジェクトの実装前フェーズを自動実行します。

実行するステップ（4段階）：
1. workflow-init - プロジェクト初期化
2. create-epics-and-stories - エピックとストーリー作成
3. sprint-planning - スプリント計画
4. recursive-story-generation - 全ストーリーの再帰生成

⚡ ストーリーはすべて自動生成されます。
📊 進捗は _bmad-output/workflow-progress/ で追跡されます。

各ステップを順次実行します...
```

### 2. Progress Logging Format

```
=====================================
[Step N/4] 実行中: [step-name]
=====================================
↓
[Step N/4] ✅ 完了: [step-name]
  - 生成ファイル: [file list]
  - 所要時間: [duration]
=====================================
```

再帰的ストーリー生成時:
```
[Story 1/12] 生成中: STORY-001-user-authentication...
[Story 1/12] ✅ 完了: STORY-001-user-authentication
[Story 2/12] 生成中: STORY-002-data-ingestion...
[Story 2/12] ✅ 完了: STORY-002-data-ingestion
...
[Story 12/12] ✅ 完了: STORY-012-api-documentation
```

---

## FINAL OUTPUT

### 完了時のサマリー:

```markdown
# Pre-Implementation Flow - 実行完了

## 実行ステータス: ✅ Complete

### 完了したステップ:
1. ✅ workflow-init - Completed
2. ✅ create-epics-and-stories - Completed
3. ✅ sprint-planning - Completed
4. ✅ recursive-story-generation - Completed

### 生成された成果物:
- Epics: [count] files in _bmad-output/epics/
- Stories: [count] files in _bmad-output/stories/
- Sprint Status: sprint-status.yaml

### ストーリー生成詳細:
| Story ID | Name | Status |
|----------|------|--------|
| STORY-001 | [name] | ✅ |
| STORY-002 | [name] | ✅ |
| ... | ... | ... |

### 次のステップ:
実装前フェーズが完了しました。
次のワークフローを実行してください:

  /bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow

```

---

## PAUSE & RESUME SUPPORT

### 中断時:
進捗ファイルに以下を記録:
```yaml
status: paused
paused_at: [timestamp]
paused_reason: [reason]
resume_from: [step_id]
```

### 再開時:
1. 進捗ファイルを読み込み
2. `resume_from` ステップから再開
3. `status: in_progress` に更新

---

## ERROR HANDLING

### エラー発生時:

```yaml
status: failed
failed_at: [timestamp]
failed_step: [step_id]
error_details:
  message: [error message]
  stack: [error stack if available]
  suggested_fix: [suggested resolution]
```

### エラーメッセージ:

```markdown
# Pre-Implementation Flow - エラー

## 失敗したステップ: [Step N] [step-name]

## エラー詳細:
[具体的なエラー内容]

## 推奨される修正手順:
1. [修正手順1]
2. [修正手順2]

## 完了したステップ:
[list of completed steps]

## 再開方法:
問題を修正後、以下を実行:
  /bmad:bmm:workflows:full-bmad-project-flow:1-pre-implementation-flow --resume
```

---

## SUCCESS CRITERIA

- ✅ 4個のステップすべてがエラーなしで完了
- ✅ すべてのエピックが生成されている
- ✅ すべてのストーリーが完全な状態で生成されている
- ✅ sprint-status.yaml が生成されている
- ✅ 進捗ファイルが正しく更新されている

````
