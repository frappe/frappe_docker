---
title: Image Size Checks
---

# Automatic image size checks

The reusable core build and test workflow checks image growth before integration
tests and dependent publishing jobs. This reference describes its measurements,
policy, baseline selection, and reports. For the pipeline design, see the
[image build and publish pipeline](../13-explanation/07-github-actions-image-workflows.md).

## Measurements and coverage

| Property       | Value                                                                                                            |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| Images         | `base`, `build`, and `erpnext`, measured separately                                                              |
| Release lines  | `15`, `16`, and `develop`                                                                                        |
| Architectures  | `linux/amd64` and `linux/arm64`, with separate baselines                                                         |
| Size metric    | Sum of compressed filesystem layer sizes from the registry manifest                                              |
| Included bytes | Every filesystem layer, including inherited base layers                                                          |
| Excluded bytes | Image configuration, manifests, and attestations                                                                 |
| Layer count    | Reported for information; does not independently cause failure                                                   |
| Data source    | The local CI registry's manifests and image configuration; no filesystem blob download or second reference build |

Shared base layers are included in each image's measurement. The metric does not
represent Docker's local disk usage or the bytes needed by a host that already has
some layers cached.

Comparisons cover the `base`, `build`, and `erpnext` images already built by core
CI. Custom and layered image builds are outside this check's coverage.

## Growth policy

Limits are configured in `.github/image-size-policy.json`:

| Key                  | Default     | Meaning                                    |
| -------------------- | ----------- | ------------------------------------------ |
| `max_growth_percent` | `5`         | Percentage growth over the baseline        |
| `max_growth_bytes`   | `104857600` | Absolute growth over the baseline: 100 MiB |

A build fails when growth exceeds **both** limits for any measured image.
Equality with a limit is permitted. For example, growth from 1,000 MiB to 1,200 MiB
fails; growth from 1,000 MiB to 1,100 MiB does not exceed the absolute limit.

Limits must be non-negative, finite numbers.

### Accept image growth for one run

In GitHub Actions, open a stable or develop build workflow, choose **Run workflow**
on `main`, and enable **Allow images to exceed size limits for this run on main**.

The size check records growth above the limits as a warning and marks it
**Accepted** in the job summary for every affected image, release line, and
architecture in the run. Measurements must still succeed, and integration tests
must pass before publishing. Automatic runs continue to enforce the limits.

After a successful run, its size report becomes eligible as the baseline for the
same workflow. Use **Core / Build Stable** or **Core / Build Develop** to update
the baseline for the corresponding automated builds.

## Baseline selection

Baseline candidates are reports from earlier workflow runs. A candidate must meet
all these conditions:

- The entire workflow run completed successfully on `main`.
- The run belongs to the same repository and uses the same calling workflow.
- The event is `push`, `repository_dispatch`, `schedule`, or `workflow_dispatch`.
- Reports for both architectures exist and have not expired.
- The report matches the requested image type, release line, and architecture.

PR reports and failed or incomplete runs are excluded, even if they uploaded
measurements. Lookup examines up to 500 recent baseline artifacts and selects by
workflow run ID, so an older run finishing late does not replace a newer successful
baseline.

Successful image builds triggered by relevant pushes to `main`, upstream releases,
and the existing develop schedule make new reports eligible automatically.
Pushes that do not trigger image builds need no new measurements. Generated
measurements are not committed to Git, and no manual baseline update is required.

### Initial rollout and expiration

Reports are retained for 90 days. When no eligible retained baseline exists, CI
reports sizes without a numerical comparison. The next successful `main` build
supplies a baseline automatically.

API and download failures fail the check rather than silently discarding an
existing baseline.

## Version selection

PR builds use the Frappe and ERPNext tags recorded in the selected baseline. Main
and release builds continue resolving the latest application versions.

When recorded build inputs change, the summary shows the previous and current
values; growth limits still apply. Moving `develop` refs, mutable base images, and
unpinned dependencies can affect sizes even when the recorded inputs match.

## Reports

Once measurements have been collected, the workflow uploads `report.json`,
including when the size check or a later step fails.

| Run type | Artifact name                                                           |
| -------- | ----------------------------------------------------------------------- |
| Main     | `image-sizes-<repo>-<release-line>-<architecture>`                      |
| PR       | `image-sizes-pr-<repo>-<release-line>-<architecture>-attempt-<attempt>` |

For the existing core matrix, `<repo>` is `erpnext`. Each report records its source
commit and workflow run, architecture, application and build versions, image
sizes, layer digests, sizes, and instruction history.

The job summary contains the baseline, current size, absolute and percentage
changes, layer counts, results, and the ten largest layers per image with their
build instructions. Failed runs retain their reports for review but cannot become
baselines.

For pull requests, GitHub Actions posts a build report when a Stable build
finishes. The report shows the Docker Bake step duration and compressed
sizes by release line and architecture alongside the same successful `main`
baseline used in the Actions size summary. Each row also shows the outcome of
the full build-and-test job. The comment links to the baseline
run and shows absolute and percentage changes in time and size when the
measurements are available. An orange circle marks an increase, and a green
circle marks a decrease.
New Stable runs update the existing comment, including
when the build fails after collecting measurements. If an artifact download
fails, rerun **Core / Report PR Build** to retry posting the comment.

## Publishing boundary

The publishing workflow rebuilds images after the test workflow. Size reports
describe the tested images rather than verify every published digest. See the
[core publishing flow](../13-explanation/07-github-actions-image-workflows.md#current-flow)
for how those stages relate.
