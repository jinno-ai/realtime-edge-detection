````markdown
---
name: Implementation & Test Flow
description: BMADプロジェクトの実装/テスト/レビューフェーズを自動実行。ストーリー実装からレビュー・テスト・最終チェックまで。全ストーリーを再帰的に実装・テストし、進捗管理を完備。
web_bundle: true
---

# Implementation & Test Flow

**Goal:** BMADプロジェクトの実装・テスト・レビューフェーズを完全自動化。すべてのストーリーの実装からテスト、レビュー、最終チェックまでユーザー入力なしで実行する。

**Your Role:** Implementation & Test Flow Coordinatorとして、実装・テスト・レビューの統括と品質保証を行います。

**Prerequisites:**
- ⚠️ `1-pre-implementation-flow` が完了していること
- ⚠️ `_bmad-output/stories/` にストーリーファイルが存在すること
- ⚠️ `sprint-status.yaml` が存在すること

---

## PHASE SCOPE

このワークフローは以下をカバー:
- ✅ 全ストーリーの再帰的実装 (dev-story)
- ✅ 全ストーリーのコードレビュー (code-review)
- ✅ テスト設計と自動化 (testarch-*)
- ✅ 最終品質チェック (check-implementation-readiness)
- ✅ プロジェクトドキュメント生成

---

## PROGRESS TRACKING SYSTEM

### Progress File: `_bmad-output/workflow-progress/implementation-test-progress.yaml`

```yaml
workflow: implementation-test-flow
started_at: [ISO 8601 timestamp]
updated_at: [ISO 8601 timestamp]
status: in_progress | completed | failed | paused

prerequisites_check:
  pre_implementation_completed: true | false
  stories_available: true | false
  sprint_status_exists: true | false

phases:
  - id: 1
    name: implementation-phase
    status: pending | running | completed | failed
    started_at: null
    completed_at: null
    stories_total: 0
    stories_implemented: 0
    story_details: []

  - id: 2
    name: review-phase
    status: pending
    started_at: null
    completed_at: null
    reviews_total: 0
    reviews_completed: 0
    review_details: []
    issues_found: 0
    issues_resolved: 0

  - id: 3
    name: test-phase
    status: pending
    started_at: null
    completed_at: null
    sub_phases:
      - name: test-design
        status: pending
      - name: test-automate
        status: pending
      - name: test-trace
        status: pending
      - name: test-review
        status: pending

  - id: 4
    name: documentation-phase
    status: pending
    started_at: null
    completed_at: null
    documents_generated: []

  - id: 5
    name: final-check-phase
    status: pending
    started_at: null
    completed_at: null
    result: null  # PASS | CONCERNS | FAIL | WAIVED

current_phase: 0
total_phases: 5
completion_percentage: 0

quality_metrics:
  code_coverage: null
  tests_passed: null
  tests_failed: null
  review_score: null
```

---

## WORKFLOW EXECUTION PHASES

### Phase 1: Recursive Story Implementation

**Purpose:** すべてのストーリーを再帰的に実装

**Pre-execution:**
1. `_bmad-output/stories/` からすべてのストーリーをスキャン
2. Phase 1 のステータスを `running` に更新
3. `stories_total` を設定

**RECURSIVE IMPLEMENTATION LOOP:**

```
# ストーリーを優先度と依存関係でソート
sorted_stories = sort_by_priority_and_dependencies(stories)

FOR each story IN sorted_stories:

    1. Check dependencies:
       IF story.dependencies not all completed:
           SKIP and add to deferred queue
           CONTINUE

    2. Update progress:
       story_details.append({
           id: story.id,
           name: story.name,
           status: "implementing",
           started_at: timestamp
       })

    3. Execute development:
       /bmad:bmm:workflows:dev-story [story.id]

    4. Validate implementation:
       - Check code files generated
       - Check unit tests created
       - Check acceptance criteria addressed

    5. If validation fails:
       - Log error
       - Attempt auto-fix
       - Retry up to 3 times

    6. Update progress:
       story_details[story.id].status = "implemented"
       story_details[story.id].completed_at = timestamp
       story_details[story.id].files_created = [list]
       stories_implemented += 1

    7. Log progress:
       "[Implementation N/M] ✅ 完了: {story.name}"

END FOR

# Process deferred queue
WHILE deferred_queue NOT empty AND progress_made:
    FOR each deferred_story:
        IF dependencies now met:
            Implement story
            Remove from queue
END WHILE
```

**Expected Output:**
- すべてのストーリーが実装済み
- `src/` 配下にコードファイル
- `tests/unit/` 配下にユニットテスト

---

### Phase 2: Recursive Code Review

**Purpose:** 実装されたすべてのストーリーをレビュー

**RECURSIVE REVIEW LOOP:**

```
FOR each implemented_story IN story_details WHERE status == "implemented":

    1. Update progress:
       review_details.append({
           story_id: story.id,
           status: "reviewing",
           started_at: timestamp
       })

    2. Execute review:
       /bmad:bmm:workflows:code-review [story.id]

    3. Collect review results:
       - issues_found += review.issues.count
       - Store issues in review_details

    4. Auto-resolve issues if possible:
       FOR each issue IN review.issues:
           IF issue.auto_fixable:
               Apply fix
               issues_resolved += 1
       END FOR

    5. Update progress:
       review_details[story.id].status = "reviewed"
       review_details[story.id].issues = [list]
       reviews_completed += 1

    6. Log progress:
       "[Review N/M] ✅ 完了: {story.name}"
       "  - Issues found: {count}"
       "  - Issues resolved: {resolved_count}"

END FOR
```

**Review Quality Gate:**
```
IF (issues_found - issues_resolved) > threshold:
    PAUSE workflow
    LOG "Critical review issues require manual intervention"
    SAVE progress for resume
ELSE:
    CONTINUE to next phase
```

---

### Phase 3: Test Phase (4 Sub-phases)

#### Sub-phase 3.1: Test Design

**Workflow:** `/bmad:bmm:workflows:testarch-test-design`

```
1. Update: sub_phases.test-design.status = "running"
2. Execute: /bmad:bmm:workflows:testarch-test-design
3. Validate: Check test plan generated
4. Update: sub_phases.test-design.status = "completed"
```

---

#### Sub-phase 3.2: Test Automation

**Workflow:** `/bmad:bmm:workflows:testarch-automate`

```
1. Update: sub_phases.test-automate.status = "running"
2. Execute: /bmad:bmm:workflows:testarch-automate
3. Validate: Check automated tests generated
4. Update: sub_phases.test-automate.status = "completed"
```

---

#### Sub-phase 3.3: Test Traceability

**Workflow:** `/bmad:bmm:workflows:testarch-trace`

```
1. Update: sub_phases.test-trace.status = "running"
2. Execute: /bmad:bmm:workflows:testarch-trace
3. Validate: Check traceability matrix generated
4. Record quality metrics:
   quality_metrics.code_coverage = [value]
   quality_metrics.tests_passed = [value]
   quality_metrics.tests_failed = [value]
5. Update: sub_phases.test-trace.status = "completed"
```

---

#### Sub-phase 3.4: Test Review

**Workflow:** `/bmad:bmm:workflows:testarch-test-review`

```
1. Update: sub_phases.test-review.status = "running"
2. Execute: /bmad:bmm:workflows:testarch-test-review
3. Validate: Check test review report generated
4. Update: sub_phases.test-review.status = "completed"
5. Update: Phase 3 status = "completed"
```

---

### Phase 4: Documentation Generation

**Workflow:** `/bmad:bmm:workflows:document-project`

```
1. Update: Phase 4 status = "running"
2. Execute: /bmad:bmm:workflows:document-project
3. Record generated documents:
   documents_generated = [
       "docs/API.md",
       "docs/ARCHITECTURE.md",
       "docs/USER_GUIDE.md",
       ...
   ]
4. Update: Phase 4 status = "completed"
```

---

### Phase 5: Final Implementation Check

**Workflow:** `/bmad:bmm:workflows:check-implementation-readiness`

```
1. Update: Phase 5 status = "running"
2. Execute: /bmad:bmm:workflows:check-implementation-readiness
3. Record result:
   result = PASS | CONCERNS | FAIL | WAIVED
4. Update: Phase 5 status = "completed"
5. Update overall workflow status based on result
```

**Result Handling:**
- **PASS**: Workflow completes successfully
- **CONCERNS**: Workflow completes with warnings
- **WAIVED**: Workflow completes (issues acknowledged)
- **FAIL**: Workflow fails, requires intervention

---

## INITIALIZATION SEQUENCE

### 1. Prerequisites Check

```
# Pre-Implementation Flow Verification

Checking prerequisites...

✅ Pre-Implementation Flow completed: [check progress file]
✅ Stories available: [count] stories found
✅ Sprint Status exists: sprint-status.yaml found

Prerequisites verified. Starting Implementation & Test Flow...
```

### 2. Welcome and Status Report

```
# Implementation & Test Flow - 開始

BMADプロジェクトの実装・テスト・レビューフェーズを自動実行します。

実行するフェーズ（5段階）：
1. implementation-phase - 全ストーリーの再帰的実装
2. review-phase - 全ストーリーのコードレビュー
3. test-phase - テスト設計・自動化・検証・レビュー
4. documentation-phase - プロジェクトドキュメント生成
5. final-check-phase - 実装準備完了確認

📊 ストーリー数: [count]
⚡ すべてのストーリーが自動実装されます。
📈 進捗は _bmad-output/workflow-progress/ で追跡されます。

各フェーズを順次実行します...
```

---

## PROGRESS LOGGING FORMAT

### Phase Progress:
```
=====================================
[Phase N/5] 実行中: [phase-name]
=====================================
```

### Story Implementation Progress:
```
[Implementation 1/15] 実装中: STORY-001-user-authentication...
  → コード生成中...
  → テスト作成中...
  → 検証中...
[Implementation 1/15] ✅ 完了: STORY-001-user-authentication
  - Files: 5 created
  - Tests: 3 created
  - Duration: 2m 30s
```

### Review Progress:
```
[Review 1/15] レビュー中: STORY-001-user-authentication...
  → コード品質チェック...
  → セキュリティチェック...
  → ベストプラクティスチェック...
[Review 1/15] ✅ 完了: STORY-001-user-authentication
  - Issues found: 2
  - Auto-resolved: 1
  - Manual review needed: 1
```

### Test Phase Progress:
```
[Test Phase] Sub-phase 1/4: test-design
  → テストケース設計中...
[Test Phase] ✅ test-design 完了

[Test Phase] Sub-phase 2/4: test-automate
  → テスト自動化実装中...
[Test Phase] ✅ test-automate 完了
  - Tests created: 45
  - Coverage: 87%
```

---

## FINAL OUTPUT

### 完了時のサマリー:

```markdown
# Implementation & Test Flow - 実行完了

## 実行ステータス: ✅ Complete / ⚠️ Completed with Concerns / ❌ Failed

### 完了したフェーズ:
1. ✅ implementation-phase - Completed
   - Stories implemented: [N/M]
   - Files created: [count]

2. ✅ review-phase - Completed
   - Reviews completed: [N/M]
   - Issues found: [count]
   - Issues resolved: [count]

3. ✅ test-phase - Completed
   - Test design: ✅
   - Test automation: ✅
   - Test traceability: ✅
   - Test review: ✅

4. ✅ documentation-phase - Completed
   - Documents generated: [count]

5. ✅ final-check-phase - [PASS/CONCERNS/FAIL/WAIVED]

### 品質メトリクス:
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Code Coverage | 87% | 80% | ✅ |
| Tests Passed | 142 | - | ✅ |
| Tests Failed | 0 | 0 | ✅ |
| Review Score | 8.5/10 | 7/10 | ✅ |

### 生成された成果物:
- Source Code: src/
- Unit Tests: tests/unit/
- Integration Tests: tests/integration/
- E2E Tests: tests/e2e/
- Documentation: docs/
- Traceability Matrix: _bmad-output/traceability/

### ストーリー実装詳細:
| Story ID | Name | Implementation | Review | Tests |
|----------|------|----------------|--------|-------|
| STORY-001 | [name] | ✅ | ✅ | ✅ |
| STORY-002 | [name] | ✅ | ✅ | ✅ |
| ... | ... | ... | ... | ... |

### 次のステップ:
プロジェクトが実装完了状態になりました。
- デプロイ準備が整いました
- 本番環境へのデプロイを実行できます
```

---

## PAUSE & RESUME SUPPORT

### 中断時:
```yaml
status: paused
paused_at: [timestamp]
paused_phase: [phase_id]
paused_story: [story_id if applicable]
resume_instructions:
  command: "/bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow --resume"
  from_phase: [phase_id]
  from_story: [story_id or null]
```

### 再開コマンド:
```
/bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow --resume
```

再開時の動作:
1. 進捗ファイルを読み込み
2. `paused_phase` から再開
3. ストーリー単位の場合は `paused_story` から再開

---

## ERROR HANDLING

### エラー発生時のリトライロジック:

```
ON_ERROR:
    retry_count = 0
    max_retries = 3

    WHILE retry_count < max_retries:
        LOG "Retry attempt {retry_count + 1}/{max_retries}"

        TRY:
            Re-execute failed operation
            IF success:
                BREAK
        CATCH:
            retry_count += 1
            WAIT exponential_backoff(retry_count)

    IF retry_count >= max_retries:
        SAVE progress
        LOG_ERROR with details
        PAUSE workflow
```

### エラーメッセージ:

```markdown
# Implementation & Test Flow - エラー

## 失敗したフェーズ: [Phase N] [phase-name]
## 失敗したストーリー: [story-id] (if applicable)

## エラー詳細:
[具体的なエラー内容]

## 試行されたリトライ: 3/3

## 推奨される修正手順:
1. [修正手順1]
2. [修正手順2]

## 完了した作業:
- Phases: [completed phases]
- Stories implemented: [N/M]
- Stories reviewed: [N/M]

## 再開方法:
問題を修正後、以下を実行:
  /bmad:bmm:workflows:full-bmad-project-flow:2-implementation-test-flow --resume
```

---

## SUCCESS CRITERIA

- ✅ すべてのストーリーが実装済み
- ✅ すべてのストーリーがレビュー済み (重大な問題なし)
- ✅ テストフェーズの4サブフェーズすべて完了
- ✅ ドキュメントが生成されている
- ✅ final-check-phase が PASS または CONCERNS
- ✅ コードカバレッジが目標値以上
- ✅ すべてのテストがパス

````
