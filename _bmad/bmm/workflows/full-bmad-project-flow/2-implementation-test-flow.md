---
name: Implementation & Test Flow
description: BMADプロジェクトの実装/テスト/レビューフェーズを完全自動実行。ユーザー問い合わせなし・上流優先修正で全ストーリーを再帰的に実装・テスト。
web_bundle: true
---

# Implementation & Test Flow

**Goal:** BMADプロジェクトの実装・テスト・レビューフェーズを完全自動化。**ユーザー問い合わせなし**ですべてのストーリーの実装から最終チェックまで完走する。

**Your Role:** Implementation & Test Flow Coordinatorとして、実装・テスト・レビューを自律的に統括します。

**Prerequisites:**
- `1-pre-implementation-flow` が完了していること
- `_bmad-output/stories/` にストーリーファイルが存在すること

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
   - Story定義 > 実装 > テスト
   - 実装がストーリーと矛盾 → ストーリーを正として実装を修正
   - テストが失敗 → 実装を修正 (ストーリーが正しい前提)

2. 常識的な範囲で自動修正
   - コンパイルエラー → 自動修正
   - 型エラー → 自動修正
   - リントエラー → 自動修正
   - テスト失敗 → 実装を修正して再試行 (最大3回)

3. 保守的なデフォルト選択
   - ライブラリバージョン不明 → 最新安定版
   - アーキテクチャパターン不明 → 業界標準パターン
   - エラーハンドリング不明 → 例外をログして安全に失敗

4. 完走優先
   - 軽微な問題 → ログに記録して続行
   - レビュー指摘 → 可能な限り自動修正
   - 修正不可能 → スキップしてログに記録、次へ進む
```

### 3. 問題解決フロー

```
問題発生時:
  1. 自動修正を試行 (最大3回)
  2. 上流ドキュメント (Story/Architecture) を確認
  3. 上流を正として下流を修正
  4. デフォルト実装で補完
  5. スキップしてログに記録
  6. 次のタスクへ進む (停止しない)
```

---

## PHASE SCOPE

- ✅ 全ストーリーの再帰的実装 (dev-story)
- ✅ 全ストーリーのコードレビュー (code-review)
- ✅ テスト設計と自動化 (testarch-*)
- ✅ 最終品質チェック (check-implementation-readiness)
- ✅ プロジェクトドキュメント生成

---

## PROGRESS TRACKING

### Progress File: `_bmad-output/workflow-progress/implementation-test-progress.yaml`

```yaml
workflow: implementation-test-flow
started_at: [ISO 8601 timestamp]
updated_at: [ISO 8601 timestamp]
status: in_progress | completed | failed

autonomous_decisions: []

phases:
  - id: 1
    name: implementation-phase
    status: pending | running | completed | failed
    stories_total: 0
    stories_implemented: 0
    stories_skipped: 0
    story_details: []
    decisions: []

  - id: 2
    name: review-phase
    status: pending
    reviews_completed: 0
    issues_found: 0
    issues_auto_resolved: 0
    decisions: []

  - id: 3
    name: test-phase
    status: pending
    sub_phases:
      - name: test-design
        status: pending
      - name: test-automate
        status: pending
      - name: test-trace
        status: pending
      - name: test-review
        status: pending
    decisions: []

  - id: 4
    name: documentation-phase
    status: pending
    documents_generated: []
    decisions: []

  - id: 5
    name: final-check-phase
    status: pending
    result: null
    decisions: []

current_phase: 0
total_phases: 5
```

---

## WORKFLOW EXECUTION PHASES

### Phase 1: Recursive Story Implementation

**Purpose:** すべてのストーリーを再帰的に実装

**RECURSIVE IMPLEMENTATION LOOP:**

```
# ストーリーを依存関係順にソート
sorted_stories = topological_sort(stories, by=dependencies)

FOR each story IN sorted_stories:
    
    1. Log: "[Implementation N/M] 実装中: {story.name}"
    
    2. Check dependencies:
       IF story.dependencies not all completed:
           # 依存ストーリーを先に実装 (再帰)
           FOR each dep IN story.dependencies:
               IF dep not completed:
                   Implement dep first (recursive)
           END FOR
    
    3. Execute development:
       /bmad:bmm:workflows:dev-story [story.id]
    
    4. Validate & Auto-fix:
       IF compilation_errors:
           Auto-fix up to 3 times
       IF type_errors:
           Auto-fix based on story definition
       IF lint_errors:
           Auto-fix
    
    5. Run unit tests:
       IF tests_fail:
           Analyze failure
           Auto-fix implementation (story is correct)
           Retry up to 3 times
    
    6. Log decision if any autonomous decision was made
    
    7. Log: "[Implementation N/M] ✅ 完了: {story.name}"

END FOR
```

**Autonomous Behavior:**
- 依存関係の循環 → 循環を検出してログ、独立として扱う
- 実装不明確 → Architectureとストーリーから推論
- API設計不明 → RESTful標準パターンを適用

---

### Phase 2: Recursive Code Review

**Purpose:** 実装されたすべてのストーリーをレビュー

**RECURSIVE REVIEW LOOP:**

```
FOR each implemented_story:
    
    1. Log: "[Review N/M] レビュー中: {story.name}"
    
    2. Execute review:
       /bmad:bmm:workflows:code-review [story.id]
    
    3. Collect issues:
       issues_found += review.issues.count
    
    4. Auto-resolve issues:
       FOR each issue IN review.issues:
           TRY:
               Apply autonomous fix
               issues_auto_resolved += 1
           CATCH:
               Log issue for manual review later
       END FOR
    
    5. Log: "[Review N/M] ✅ 完了: {story.name}"
       "  - Issues found: {count}"
       "  - Auto-resolved: {resolved}"

END FOR
```

**Autonomous Behavior:**
- セキュリティ指摘 → 即座に自動修正
- パフォーマンス指摘 → 可能なら自動修正、不可ならログ
- スタイル指摘 → 自動修正

---

### Phase 3: Test Phase (4 Sub-phases)

#### Sub-phase 3.1: Test Design
```
/bmad:bmm:workflows:testarch-test-design
```
**Autonomous Behavior:**
- テストケース不足 → ストーリーの受け入れ基準から生成

#### Sub-phase 3.2: Test Automation
```
/bmad:bmm:workflows:testarch-automate
```
**Autonomous Behavior:**
- テストフレームワーク不明 → pytest (Python), Jest (JS) をデフォルト

#### Sub-phase 3.3: Test Traceability
```
/bmad:bmm:workflows:testarch-trace
```
**Autonomous Behavior:**
- カバレッジ不足 → 追加テストを自動生成

#### Sub-phase 3.4: Test Review
```
/bmad:bmm:workflows:testarch-test-review
```

---

### Phase 4: Documentation Generation

```
/bmad:bmm:workflows:document-project
```

**Autonomous Behavior:**
- ドキュメント不足 → コードから自動生成
- API仕様不明 → 実装から推論して生成

---

### Phase 5: Final Implementation Check

```
/bmad:bmm:workflows:check-implementation-readiness
```

**Result Handling:**
- **PASS**: 完了
- **CONCERNS**: ログに記録して完了
- **FAIL**: 可能な修正を試行、修正不可ならログに記録して完了
- **WAIVED**: ログに記録して完了

---

## INITIALIZATION MESSAGE

```
# Implementation & Test Flow - 完全自動実行開始

🤖 自律実行モード: ON
📐 意思決定ルール: 上流優先修正
🚫 ユーザー問い合わせ: なし

実行フェーズ:
1. implementation-phase (全ストーリー再帰実装)
2. review-phase (全ストーリーレビュー)
3. test-phase (設計/自動化/トレース/レビュー)
4. documentation-phase
5. final-check-phase

ストーリー数: [count]

完全自動で完走します...
```

---

## FINAL OUTPUT

```markdown
# Implementation & Test Flow - 完了

## 実行ステータス: ✅ Complete

### 自律的意思決定:
- 総決定数: [count]
- 自動修正: [count]
- 上流参照: [count]
- スキップ: [count]

### Phase 1: Implementation
- Stories implemented: [N/M]
- Auto-fixes applied: [count]

### Phase 2: Review
- Reviews completed: [N/M]
- Issues found: [count]
- Issues auto-resolved: [count]

### Phase 3: Test
- Test design: ✅
- Test automation: ✅
- Test traceability: ✅
- Test review: ✅

### Phase 4: Documentation
- Documents generated: [count]

### Phase 5: Final Check
- Result: [PASS/CONCERNS/WAIVED]

### 成果物:
- Source: src/
- Tests: tests/
- Docs: docs/
- Decision Log: _bmad-output/workflow-progress/decision-log.yaml
```

---

## ERROR HANDLING (停止しない)

```
問題発生時:
  1. 自動修正を試行 (最大3回)
  2. 上流を正として下流を修正
  3. デフォルト実装で補完
  4. スキップしてログ記録
  5. 次へ進む (絶対に停止しない)
```

---

## SUCCESS CRITERIA

- ✅ ユーザー問い合わせなしで完走
- ✅ すべてのフェーズが完了 (またはスキップでログ記録)
- ✅ すべてのストーリーが実装 (または理由付きでスキップ)
- ✅ 意思決定ログが記録
- ✅ 最終チェックが PASS/CONCERNS/WAIVED
