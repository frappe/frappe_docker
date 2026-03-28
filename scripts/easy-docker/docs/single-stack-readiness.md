# Easy-Docker Single-Stack Readiness

## Purpose

This document freezes the required single-stack scope for `easy-docker`
before work moves to `separate services`.

Current interpretation:

- `single-stack` means the implemented `single-host` topology.
- The stack must be isolated from other stacks at the Docker Compose project level.
- The supported happy path is one usable site per stack unless a later
  product decision explicitly broadens this.
- The current site bootstrap path always installs the full app selection
  stored on the stack itself.
- It is not yet supported to create multiple sites in one stack with
  different app selections per site.

## Current Supported Scope

The current codebase already supports these single-stack paths:

- Create production stack
- Create development stack
- Choose `single-host` topology
- Select proxy, database, and redis mode
- Select apps and branches
- Persist `metadata.json`, stack `.env`, `apps.json`
- Render `compose.generated.yaml`
- Manage existing stacks
- Regenerate `apps.json`
- Re-select apps and branches
- Build custom image
- Start stack with Docker Compose
- Stop stack with Docker Compose
- Show stack runtime status
- Abort wizard with rollback or keep-files behavior
- Isolate stacks through stack-specific Compose project names

## Definition Of Done Before Separate Services

Single-stack is not considered complete when containers merely run.
It is considered complete when the user can move from stack creation
to a usable Frappe/ERPNext site and operate that stack safely.

Minimum user-facing path:

1. Create stack
2. Configure single-host topology
3. Build image if needed
4. Start stack
5. Create/bootstrap first site
6. Install selected apps on that site
7. Verify site access behind the chosen proxy mode
8. Stop/restart/down the stack
9. Re-open manage flow and inspect status/logs

## Required Remaining Changes

### High Priority

- Add a documented or automated site/bootstrap path
  - create first site
  - install selected apps
  - verify site routing/access
- Freeze the supported site model
  - recommended: one site per stack as the supported happy path

### Medium Priority

- Add remaining lifecycle operations
  - `restart`
  - `down/remove`
  - `logs`
- Add post-start recovery guidance
  - partial start
  - failed bootstrap
  - retry after custom image rebuild
- Add one-time cleanup/runbook note for stacks created before
  per-stack Compose project isolation

### Hardening Priority

- Keep runtime status semantics explicit
  - `Not created`
  - `Created`
  - `Running`
  - `Partial`
  - `Stopped`
  - `Restarting`
  - optional uptime hint
- Ensure manage actions only affect the selected stack
- Preserve safe abort/rollback behavior

## Required Single-Stack Paths

### Setup Paths

- Environment check
- Create production stack
- Create development stack
- Complete single-host wizard
- Back/cancel at each prompt
- Abort wizard with rollback
- Abort wizard while keeping files

### Runtime Paths

- Generate compose from env
- Build custom image
- Start stack
- Stop stack
- Restart stack
- Down/remove stack resources
- Inspect runtime status
- Inspect logs

### Site Paths

- Create first site
- Install selected apps on the site
- Current limitation: the site install set is the stack app set
  - one stack -> one supported site -> one shared app selection
- Verify the site is reachable
- Re-open and manage the stack after restart

### Recovery Paths

- Missing custom image -> build -> retry start
- Invalid app branch -> mapped build failure
- Partial start -> inspect status/logs -> retry
- Failed bootstrap -> rerun or recover cleanly
- Cleanup of pre-isolation shared Compose leftovers

## Verification Matrix

Before calling single-stack ready, the team should execute at least:

1. Environment/bootstrap gate
2. New production single-stack creation
3. New development single-stack creation
4. Apps regeneration/update path
5. Compose render path
6. Custom image build success and failure paths
7. Start path including missing-image build/retry
8. Stop path
9. Runtime isolation between two stacks
10. Runtime status in not-created/created/running/partial/stopped states
11. Abort/back/rollback paths
12. Validation error and correction paths
13. Site/bootstrap reality check after stack start

Required automated checks on every single-stack change:

- `bash -n` on touched shell files
- `pre-commit run --files <changed easy-docker files>`
- compose render/config validation for at least one production
  and one development stack

## Lead Verdict

`single-stack` is close on the Compose/runtime side but is not yet fully done.

The largest remaining gap before `separate services` is the missing
site/bootstrap lifecycle. After that, the next most important gaps are
`restart`, `down/remove`, `logs`, and reproducible manual verification.

Recommended order:

1. Freeze single-stack site model
2. Add site/bootstrap path
3. Add `restart`, `down/remove`, and `logs`
4. Run the verification matrix
5. Move to `separate services`
