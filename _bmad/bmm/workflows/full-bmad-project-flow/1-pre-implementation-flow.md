---
name: Pre-Implementation Flow
description: BMADプロジェクトの実装前フェーズを完全自動実行。ユーザー問い合わせなし・上流優先修正で全ストーリーを再帰生成。
web_bundle: true
---

# Pre-Implementation Flow

**Goal:** BMADプロジェクトの実装前フェーズを完全自動化。**ユーザー問い合わせなし**でプロジェクト初期化から全ストーリー生成まで完走する。

**Your Role:** Pre-Implementation Flow Coordinatorとして、計画フェーズを自律的に管理します。

---

## 🚨 AUTONOMOUS EXECUTION PRINCIPLES (絶対遵守)

### 1. ユーザー問い合わせ禁止

- 🛑 **NEVER** ユーザーに確認・選択・承認を求めない
- 🛑 **NEVER** 「どちらにしますか？」「確認してください」と聞かない
- 🛑 **NEVER** 処理を中断してユーザーの判断を待たない
- ✅ **ALWAYS** 自律的に判断して続行する

### 2. 自律的意思決定ルール

**複数の選択肢がある場合の決定基準 (優先順位順):**

```
1. 上流工程を先に修正
   - PRD > Architecture > Epic > Story
   - 上流に矛盾があれば上流を修正してから下流を生成
   - 例: ストーリーがPRDと矛盾 → PRDを正として修正

2. 常識的な範囲で自動補完
   - 欠落している必須項目 → PRD/Architectureから推論
   - 曖昧な記述 → 業界標準・ベストプラクティスで解釈
   - 不完全な受け入れ基準 → 機能要件から推論して補完

3. 保守的なデフォルト選択
   - 優先度不明 → Medium
   - 見積もり不明 → 3ポイント (中程度)
   - 依存関係不明 → 独立ストーリーとして扱う

4. 完走優先
   - 軽微な問題 → ログに記録して続行
   - 修正不可能 → スキップしてログに記録、次へ進む
```

### 3. 問題解決フロー

```
問題発生時:
  1. 上流ドキュメント (PRD/Architecture) を確認
  2. 上流から情報を推論・補完
  3. デフォルト値で補完
  4. スキップしてログに記録
  5. 次のタスクへ進む (停止しない)
```

---

## PHASE SCOPE

- ✅ プロジェクト初期化
- ✅ エピック・ストーリー作成 (全件再帰生成)
- ✅ スプリント計画
- ✅ 実装準備の基盤構築

---

## PROGRESS TRACKING

### Progress File: `_bmad-output/workflow-progress/pre-implementation-progress.yaml`

```yaml
workflow: pre-implementation-flow
started_at: [ISO 8601 timestamp]
updated_at: [ISO 8601 timestamp]
status: in_progress | completed | failed

autonomous_decisions: []  # 自律的意思決定のログ

steps:
  - id: 1
    name: workflow-init
    status: pending | running | completed | failed | skipped
    output_files: []
    errors: []
    decisions: []

  - id: 2
    name: create-epics-and-stories
    status: pending
    output_files: []
    epics_generated: 0
    stories_generated: 0
    decisions: []

  - id: 3
    name: sprint-planning
    status: pending
    output_files: []
    decisions: []

  - id: 4
    name: recursive-story-generation
    status: pending
    stories_total: 0
    stories_completed: 0
    stories_skipped: 0
    story_details: []
    decisions: []

current_step: 1
total_steps: 4
```

---

## WORKFLOW EXECUTION STEPS

### Step 1: Workflow Initialization

**Workflow:** `/bmad:bmm:workflows:workflow-init`

**Autonomous Behavior:**
- プロジェクト設定が不明確 → デフォルト設定を使用
- 既存ファイルとの競合 → 既存を保持、新規をマージ

**Action:**
```
/bmad:bmm:workflows:workflow-init
```

---

### Step 2: Create Epics and Stories

**Workflow:** `/bmad:bmm:workflows:create-epics-and-stories`

**Autonomous Behavior:**
- PRDが不完全 → 可能な範囲でエピックを生成、不足部分はログに記録
- 機能の粒度が不明確 → 一般的なエピック分割基準を適用

**Action:**
```
/bmad:bmm:workflows:create-epics-and-stories
```

---

### Step 3: Sprint Planning

**Workflow:** `/bmad:bmm:workflows:sprint-planning`

**Autonomous Behavior:**
- 優先度が未設定 → PRDの記載順序を優先度として使用
- 見積もりがない → 機能の複雑さから推論

**Action:**
```
/bmad:bmm:workflows:sprint-planning
```

---

### Step 4: Recursive Story Generation (ALL Stories)

**Purpose:** すべてのストーリーを再帰的に生成

**RECURSIVE GENERATION LOOP:**

```
FOR each story_stub IN _bmad-output/stories/*.md:
    
    IF story_stub is incomplete:
        
        1. Log: "[Story N/M] 生成中: {story_name}"
        
        2. Analyze story stub:
           - Check what's missing
           - Identify source documents (PRD, Architecture, Epic)
        
        3. Auto-complete missing parts:
           - 受け入れ基準なし → PRDの機能要件から推論
           - 技術要件なし → Architectureから推論
           - 依存関係なし → エピック構造から推論
           - 見積もりなし → 機能複雑度から推論 (default: 3)
        
        4. Execute:
           /bmad:bmm:workflows:create-story [story_id]
        
        5. Validate & Auto-fix:
           IF validation_errors:
               FOR each error:
                   Apply autonomous fix based on decision rules
               END FOR
        
        6. Log decision if any autonomous decision was made
        
        7. Log: "[Story N/M] ✅ 完了: {story_name}"
    
    ELSE:
        Log: "[Story N/M] ⏭️ スキップ (既存): {story_name}"

END FOR
```

---

## INITIALIZATION MESSAGE

```
# Pre-Implementation Flow - 完全自動実行開始

🤖 自律実行モード: ON
📐 意思決定ルール: 上流優先修正
🚫 ユーザー問い合わせ: なし

実行ステップ:
1. workflow-init
2. create-epics-and-stories
3. sprint-planning
4. recursive-story-generation (全ストーリー)

完全自動で完走します...
```

---

## FINAL OUTPUT

```markdown
# Pre-Implementation Flow - 完了

## 実行ステータス: ✅ Complete

### 自律的意思決定:
- 総決定数: [count]
- 上流参照: [count]
- デフォルト適用: [count]
- スキップ: [count]

### 生成された成果物:
- Epics: [count] files
- Stories: [count] files (完全生成)
- Sprint Status: sprint-status.yaml

### 次のステップ:
Phase 2を実行:
  /bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow
```

---

## ERROR HANDLING (停止しない)

```
問題発生時:
  1. 自動修正を試行
  2. 上流から情報を補完
  3. デフォルトで補完
  4. スキップしてログ記録
  5. 次へ進む (絶対に停止しない)
```

---

## SUCCESS CRITERIA

- ✅ ユーザー問い合わせなしで完走
- ✅ すべてのステップが完了 (またはスキップでログ記録)
- ✅ すべてのストーリーが生成 (または理由付きでスキップ)
- ✅ 意思決定ログが記録
