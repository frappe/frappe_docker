# Easy Docker Wizard Flow (Clean View)

This document shows the wizard paths in a clean, forward-only view.
Back/Cancel/Exit loops are intentionally hidden to keep the flow readable.

## 1) Main Wizard Paths

```mermaid
flowchart TD
    A[Main Menu]
    A --> B[Production Setup]
    A --> C[Development Setup]
    A --> D[Environment Check]
    A --> Z[Exit]

    B --> E[Create new stack]
    B --> F[Manage existing stacks]
    C --> E2[Create new stack]
    C --> F2[Manage existing stacks]

    E --> G[Create stack dir + metadata.json]
    E2 --> G
    G --> H[Topology selection]

    H --> I[Single-host flow]
    H --> J[Split services flow]

    I --> K[Persist files + render compose]
    K --> L[Done]

    J --> J2[Current status: placeholder only]
    J2 --> L2[Pending implementation]

    F --> M[Select existing stack]
    F2 --> M
    M --> N[Manage stack actions]
    N --> N1[Apps actions]
    N --> N2[Docker actions]
    N1 --> O[apps.json generated/updated]
    N2 --> P[compose.generated.yaml rendered]
    N2 --> Q[Start stack in Docker Compose]
    Q --> Q1{Topology}
    Q1 -->|single-host| Q2[docker compose up -d]
    Q1 -->|split-services / others| Q3[Show runbook warning]
```

## 2) Single-host Detail Path

```mermaid
flowchart TD
    S1[Single-host selected]
    S1 --> S2[Choose proxy mode]
    S2 --> S3[Choose database mode]
    S3 --> S4[Choose redis mode]
    S4 --> S5[Set CUSTOM_IMAGE + CUSTOM_TAG]
    S5 --> S6[Select apps: apps catalog]
    S6 --> S7[For each selected app: fetch branches + choose branch]
    S7 --> S8[Proxy-specific questions]
    S8 --> S9[Database-specific questions]
    S9 --> S10[Write .env]
    S10 --> S11[Write metadata.json]
    S11 --> S12[Generate apps.json]
    S12 --> S13[Render compose.generated.yaml]
    S13 --> S14[Success message]
```

## 3) Notes

- This is a readability-focused flow map, not an exhaustive state machine.
- Navigation loops (Back/Cancel/Exit) are intentionally omitted.
- `Split services` remains not fully implemented in the wizard runtime.
- `Start stack in Docker Compose` currently supports only `single-host` topology.
- Site bootstrap is currently scoped to one supported site per stack.
- The site bootstrap installs the full app selection stored on the stack.
- Multiple sites in one stack with different per-site app selections are
  not supported yet and are planned for a later phase.
