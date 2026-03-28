# Easy Docker Wizard Flow

```mermaid
flowchart TD
    A[Main Menu] -->|Production Stack| B[Setup Menu: Production]
    A -->|Development Stack| C[Setup Menu: Development]
    A -->|Environment check| D[Environment Status]
    A -->|Exit| Z1[Exit App]
    D -->|Back to main menu| A
    D -->|Exit and close easy-docker| Z1

    B -->|Create new stack| E[Prompt: Stack name]
    B -->|Manage existing stacks| F[List existing production stacks]
    B -->|Back| A
    B -->|Exit| Z1

    C -->|Create new stack| E2[Prompt: Stack name]
    C -->|Manage existing stacks| F2[List existing development stacks]
    C -->|Back| A
    C -->|Exit| Z1

    E --> E3[Select Frappe branch profile from frappe.tsv]
    E2 --> E4[Select Frappe branch profile from frappe.tsv]
    E3 --> G[Create stack directory + metadata.json]
    E4 --> G2[Create stack directory + metadata.json]
    G --> H[Topology Menu]
    G2 --> H2[Topology Menu]

    H -->|Single-host| I[Single-host selection]
    H -->|Split services| J[Split services example]
    H -->|Abort wizard to main menu| K[Abort prompt]
    H -->|Back/Cancel| B
    H2 -->|Single-host| I
    H2 -->|Split services| J
    H2 -->|Abort wizard to main menu| K
    H2 -->|Back/Cancel| C

    J -->|Use this topology| J2[Info: placeholder path]
    J -->|Back| H
    J2 --> H

    K -->|Rollback files and return to main menu| A
    K -->|Keep files and return to main menu| A
    K -->|Back to topology selection| H

    I --> I1[Proxy mode]
    I1 --> I2[Database mode]
    I2 --> I3[Redis mode]
    I3 --> I6[Prompt CUSTOM_IMAGE + CUSTOM_TAG]
    I6 --> I7[App selection list]
    I7 -->|Enter| I8[Per selected app: choose branch from apps.tsv]
    I8 --> I9[Continue]

    I9 --> P{Proxy specific questions}
    P -->|traefik-https| P1[SITE_DOMAINS + LETSENCRYPT_EMAIL + HTTP_PUBLISH_PORT? + HTTPS_PUBLISH_PORT?]
    P -->|nginxproxy-https| P2[SITE_DOMAINS + NGINX_PROXY_HOSTS + LETSENCRYPT_EMAIL + HTTP_PUBLISH_PORT? + HTTPS_PUBLISH_PORT?]
    P -->|nginxproxy-http| P3[SITE_DOMAINS + NGINX_PROXY_HOSTS + HTTP_PUBLISH_PORT?]
    P -->|traefik-http| P4[HTTP_PUBLISH_PORT?]
    P -->|caddy-external / no-proxy| P5[HTTP_PUBLISH_PORT? default 8080]

    P1 --> DBQ
    P2 --> DBQ
    P3 --> DBQ
    P4 --> DBQ
    P5 --> DBQ

    DBQ{Database specific question}
    DBQ -->|postgres| DB1[DB_PASSWORD required]
    DBQ -->|mariadb| DB2[DB_PASSWORD optional]

    DB1 --> S[Write stack env file]
    DB2 --> S
    S --> T[Write metadata.json with top-level apps]
    T --> U[Generate apps.json from metadata.json apps]
    U --> V[Render compose.generated.yaml from metadata + env]
    V --> W[Success message]
    W --> B

    F -->|Stack selected| M[Manage selected stack]
    F -->|Back| B
    F -->|Exit| Z1
    F -->|No stacks found| F0[Manage stacks placeholder]
    F0 -->|Back| B
    F0 -->|Exit| Z1

    F2 -->|Stack selected| M
    F2 -->|Back| C
    F2 -->|Exit| Z1
    F2 -->|No stacks found| F20[Manage stacks placeholder]
    F20 -->|Back| C
    F20 -->|Exit| Z1

    M --> M2[Stack actions: Apps / Docker / Back / Exit]
    M2 -->|Apps| M3[Apps submenu]
    M2 -->|Docker| M4[Docker submenu]
    M2 -->|Back| M0[Return to current stack list]
    M2 -->|Exit| Z1
    M0 --> F
    M0 --> F2

    M3 -->|Generate apps.json| M31[Read metadata.json apps + regenerate apps.json]
    M3 -->|Select apps and branches| M32[Re-prompt app and branch selection]
    M32 --> M33[Update metadata.json apps]
    M33 --> M34[Regenerate apps.json from metadata]
    M34 --> M3
    M3 -->|Back| M2
    M3 -->|Exit| Z1
    M31 --> M3

    M4 -->|Generate docker compose from env| M41[Render compose.generated.yaml]
    M4 -->|Start stack in Docker Compose| M42[Topology gate]
    M42 -->|single-host| M43[docker compose up -d]
    M42 -->|split-services / others| M44[Show topology-specific runbook message]
    M4 -->|Back| M2
    M4 -->|Exit| Z1
    M41 --> M4
    M43 --> M4
    M44 --> M4
```

## Notes

- `SITE_DOMAINS` validation accepts only domain names in form `sub.domain.tld` or `sub.sub.domain.tld`.
- Existing stack lists are filtered by `setup_type` (`production` vs `development`).
- In `Manage existing stacks`, navigation options are only `Back` and `Exit`.
- `Select apps and branches` writes app selection to top-level `apps` in `metadata.json`.
- `Generate apps.json` uses only `metadata.json -> apps` as source of truth.
- New stack wizard always uses custom image path (no separate official-vs-custom image step).
- `Start stack in Docker Compose` is currently allowed only for `single-host` topology stacks.

## Module Layout

- `lib/app/wizard/common.sh` is now a loader for common modules under `lib/app/wizard/common/`.
- `lib/app/wizard/env.sh` is now a loader for env modules under `lib/app/wizard/env/`.
- `lib/app/wizard/flows.sh` is now a loader for flow modules under `lib/app/wizard/flows/`.
- Public function names and flow behavior remain unchanged; only code organization was refactored.
