# Easy-Docker Development Team Process

## Purpose

This document defines the working model for the easy-docker team.
Focus is process, responsibilities, and execution flow for ongoing refactoring and feature work.

## Team Setup

- Lead Developer
  - Owns scope, priorities, and release decisions.
  - Resolves conflicts between technical proposals.
  - Approves final merge readiness.
- Senior Developer A (Correctness)
  - Reviews control flow, edge cases, and failure behavior.
  - Validates data handling, state transitions, and rollback paths.
  - Checks defensive programming and explicit error handling.
- Senior Developer B (Architecture)
  - Reviews modularity, coupling, and naming consistency.
  - Drives DRY/KISS refactors and shared helper extraction.
  - Validates maintainability and testability.
- Implementation Developer
  - Delivers code changes according to approved scope.
  - Keeps behavior stable unless change is explicitly requested.
  - Adds/update docs for structure and flow changes.
- QA/Verification Owner
  - Runs pre-commit and targeted checks.
  - Executes reproducible manual test matrix for wizard paths.
  - Reports pass/fail with concrete reproduction steps.

## Working Agreement

- No hidden behavior changes during refactors.
- Source-of-truth decisions must be explicit and documented.
- New code must prefer existing helpers over duplicated logic.
- Every change batch must be reviewable by concern (flow, env, compose, ui).

## Daily Process (Tomorrow Plan)

1. Kickoff (15 min)
   - Confirm target scope for the day.
   - Confirm "no functional change" boundaries.
   - Assign owners for implementation and verification.
2. Design sync (20 min)
   - Compare at least two technical options for non-trivial edits.
   - Select one approach with short tradeoff note.
3. Implementation blocks
   - Work in small vertical batches (one concern per batch).
   - Keep public function contracts stable where possible.
   - Update docs in the same batch when structure changes.
4. Review blocks
   - Senior A reviews correctness and failure paths.
   - Senior B reviews architecture and maintainability.
   - Lead resolves conflicts and accepts/rejects batch.
5. Verification block
   - Run pre-commit for changed files.
   - Run targeted manual flow checks.
   - Record results in short checklist format.
6. Handover
   - Write what is done, what is pending, and next first task.
   - List any blockers with owner and proposed resolution.

## Implementation Workflow

1. Define scope and constraints.
2. Map affected files/functions.
3. Propose options and select approach.
4. Implement with small commits by concern.
5. Validate with checks and manual path coverage.
6. Document final state and next steps.

## Review Workflow

1. Findings-first review format.
2. Severity order: BLOCKER, HIGH, MEDIUM, LOW.
3. Each point must include file reference and reason.
4. Lead decision:
   - Approved
   - Approved with conditions
   - Not approved

## Test and Verification Matrix (Minimum)

- Create new production stack and complete wizard.
- Create new development stack and complete wizard.
- Manage existing stack:
  - Apps -> Generate apps.json
  - Apps -> Select apps and branches
  - Docker -> Generate docker compose from env
  - Docker -> Start stack in Docker Compose (single-host topology)
- Abort/Back paths:
  - Back navigation in each submenu
  - Abort wizard with rollback
- Validation paths:
  - Domain validation error then correction
  - Branch selection from apps catalog (including back-navigation)

## Definition of Done (Team)

- Scope completed with no unplanned behavior change.
- No avoidable duplication introduced.
- Review completed by both senior roles.
- Lead verdict documented.
- Verification evidence recorded.
- Handover notes prepared for next workday.

## Handover Template

Use this at day end:

```text
Date:
Completed:
- ...

In Progress:
- ...

Next First Task:
- ...

Blockers:
- <owner> - <issue> - <proposed action>

Verification:
- pre-commit: <pass/fail + note>
- manual matrix: <pass/fail + note>
```
