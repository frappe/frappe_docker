"""Unit and HTTP integration tests; no Docker daemon or external service needed."""

import argparse
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import image_sizes as sizes

MIB = 1024 * 1024
POLICY = {"max_growth_percent": 5, "max_growth_bytes": 100 * MIB}
REPOSITORY = "frappe/frappe_docker"
WORKFLOW = ".github/workflows/core-build-stable.yml"


def report(size=1000 * MIB, arch="amd64", run_id=10):
    return {
        "schema_version": 1,
        "repo": "erpnext",
        "release_line": "16",
        "arch": arch,
        "inputs": {
            "frappe_version": "v16.52.0",
            "erpnext_version": "v16.51.1",
            "python_version": "3.14",
            "node_version": "24",
            "debian_base": "trixie",
        },
        "source": {"run_id": run_id, "sha": "abc"},
        "images": {
            "erpnext": {
                "compressed_bytes": size,
                "layers": [
                    {"digest": "sha256:abc", "bytes": size, "command": "COPY bench"}
                ],
                "history": ["COPY bench"],
            }
        },
    }


def archive(payload):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("report.json", json.dumps(payload))
    return buffer.getvalue()


class GrowthTests(unittest.TestCase):
    def test_both_limits_must_be_exceeded(self):
        for previous, current, expected in (
            (1000, 1200, True),
            (1000, 1100, False),  # Exactly 100 MiB is permitted.
            (4000, 4200, False),  # Exactly 5% is permitted.
            (4000, 4190, False),
            (100, 150, False),
            (1000, 900, False),
        ):
            with self.subTest(previous=previous, current=current):
                self.assertEqual(
                    sizes.growth_exceeds(current * MIB, previous * MIB, POLICY),
                    expected,
                )

    def test_missing_baseline_reports_sizes_and_source_guard_is_independent(self):
        current = report()
        summary, failures = sizes.compare(current, None, POLICY)
        self.assertIn("next successful", summary)
        self.assertEqual(failures, [])
        current["images"]["erpnext"]["history"] = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "RUN chmod -R g=u /home/frappe/frappe-bench",
        ]
        self.assertEqual(sizes.compare(current, None, POLICY)[1], [])
        self.assertTrue(
            sizes.permission_errors(
                sizes.instructions(
                    "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench\n"
                    "RUN chmod -R g=u /home/frappe/frappe-bench\n"
                )
            )
        )

    def test_report_shows_delta_and_large_layers(self):
        summary, failures = sizes.compare(report(1200 * MIB), report(), POLICY)
        self.assertEqual(len(failures), 1)
        self.assertIn("200.0 MiB (+20.0%)", summary)
        self.assertIn("largest layers", summary)

    def test_changed_inputs_are_explicit_and_still_checked(self):
        current = report(1200 * MIB)
        current["inputs"]["erpnext_version"] = "v16.52.0"
        summary, failures = sizes.compare(current, report(), POLICY)
        self.assertIn("Build inputs changed", summary)
        self.assertTrue(failures)

    def test_buildkit_display_history_is_not_executed_as_shell(self):
        for workdir in ("/tmp", "/home/frappe/frappe-bench"):
            current = report()
            current["images"]["erpnext"]["history"] = [
                "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                "WORKDIR " + workdir,
                "RUN |1 NODE_VERSION=24 /bin/sh -c cd /tmp && chmod -R g=u . # buildkit",
                "RUN |1 VALUE=one two /bin/sh -c echo '&&' cd /tmp # buildkit",
            ]
            self.assertEqual(sizes.compare(current, report(), POLICY)[1], [])

    def test_image_sets_cannot_silently_change(self):
        previous = report()
        previous["images"]["base"] = previous["images"]["erpnext"]
        with self.assertRaisesRegex(ValueError, "different image targets"):
            sizes.compare(report(), previous, POLICY)


class PermissionTests(unittest.TestCase):
    def test_builder_permissions_and_nonrecursive_runtime_permissions_are_safe(self):
        self.assertEqual(
            sizes.permission_errors(
                [
                    "FROM base AS builder",
                    "RUN chmod -R g=u /home/frappe/frappe-bench",
                    "FROM base AS backend",
                    "COPY --from=builder /home/frappe/frappe-bench /home/frappe/frappe-bench",
                    "WORKDIR /home/frappe/frappe-bench",
                    "RUN chmod g=u /home/frappe/frappe-bench",
                    "RUN chmod -R g=u /etc/nginx",
                ]
            ),
            [],
        )

    def test_recursive_changes_after_copy_are_rejected(self):
        for command in (
            "RUN chmod -R g=u /home/frappe/frappe-bench",
            "RUN chown --recursive frappe:0 /home/frappe",
            "RUN chgrp -Rf 0 .",
            "RUN chmod -R g=u /",
        ):
            with self.subTest(command=command):
                self.assertTrue(
                    sizes.permission_errors(
                        [
                            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                            "WORKDIR /home/frappe/frappe-bench",
                            command,
                        ]
                    )
                )

    def test_multiline_commands_and_inherited_runtime_stage(self):
        commands = sizes.instructions(
            "FROM base AS runtime\n"
            "COPY --from=builder /home/frappe/frappe-bench /home/frappe/frappe-bench\n"
            "FROM runtime AS final\n"
            "RUN echo preparing && \\\n"
            "# This comment does not end the RUN instruction.\n"
            " chmod -R g=u /home/frappe/frappe-bench\n"
        )
        self.assertEqual(len(commands), 4)
        self.assertTrue(sizes.permission_errors(commands))

    def test_current_recipes_pass(self):
        self.assertEqual(sizes.guard(), [])

    def test_cd_out_of_bench_allows_safe_relative_permissions(self):
        for command in (
            "RUN cd /tmp && chmod -R g=u .",
            "RUN cd -- /tmp; chown -R frappe:0 .",
            "RUN cd ../.. && chgrp -R 0 /tmp",
            "RUN cd '/tmp/safe directory' && chmod -R g=u .",
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    sizes.permission_errors(
                        [
                            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                            "WORKDIR /home/frappe/frappe-bench",
                            command,
                        ]
                    ),
                    [],
                )

    def test_cd_into_bench_rejects_relative_permissions(self):
        for command in (
            "RUN cd /home/frappe/frappe-bench && chmod -R g=u .",
            "RUN cd ../home/frappe/frappe-bench && chown -R frappe:0 apps",
            "RUN cd /home/frappe/frappe-bench/apps && chgrp -R 0 ../env",
        ):
            with self.subTest(command=command):
                self.assertTrue(
                    sizes.permission_errors(
                        [
                            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                            "WORKDIR /tmp",
                            command,
                        ]
                    )
                )

    def test_cd_changes_do_not_leak_between_run_instructions(self):
        self.assertTrue(
            sizes.permission_errors(
                [
                    "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                    "WORKDIR /home/frappe/frappe-bench",
                    "RUN cd /tmp && chmod -R g=u .",
                    "RUN chmod -R g=u .",
                ]
            )
        )

    def test_subshell_cd_does_not_change_the_parent_directory(self):
        self.assertTrue(
            sizes.permission_errors(
                [
                    "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                    "WORKDIR /home/frappe/frappe-bench",
                    "RUN (cd /tmp && chmod -R g=u .) && chmod -R g=u .",
                ]
            )
        )

    def test_quoted_cd_text_does_not_change_directory(self):
        self.assertTrue(
            sizes.permission_errors(
                [
                    "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                    "WORKDIR /home/frappe/frappe-bench",
                    "RUN echo 'cd /tmp' && chmod -R g=u .",
                ]
            )
        )

    def test_pipeline_cd_does_not_change_the_parent_directory(self):
        for command in (
            "RUN echo ignored | cd /tmp && chmod -R g=u .",
            "RUN cd /tmp | cat && chmod -R g=u .",
        ):
            with self.subTest(command=command):
                self.assertTrue(
                    sizes.permission_errors(
                        [
                            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                            "WORKDIR /home/frappe/frappe-bench",
                            command,
                        ]
                    )
                )

    def test_cd_back_to_bench_and_failed_cd_fallback_are_rejected(self):
        for command in (
            "RUN cd /tmp && cd - && chmod -R g=u .",
            "RUN cd /missing || chmod -R g=u .",
        ):
            with self.subTest(command=command):
                self.assertTrue(
                    sizes.permission_errors(
                        [
                            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                            "WORKDIR /home/frappe/frappe-bench",
                            command,
                        ]
                    )
                )

    def test_normalized_paths_distinguish_bench_from_sibling_directories(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /tmp",
        ]
        self.assertTrue(
            sizes.permission_errors(
                prefix + ["RUN chmod -R g=u ../home/frappe/frappe-bench"]
            )
        )
        self.assertEqual(
            sizes.permission_errors(
                prefix + ["RUN chmod -R g=u /home/frappe/frappe-bench-cache"]
            ),
            [],
        )

    def test_compound_commands_track_literal_cd(self):
        prefix = ["COPY /home/frappe/frappe-bench /home/frappe/frappe-bench"]
        for workdir, target, expected in (
            ("/tmp", "/home/frappe/frappe-bench", True),
            ("/home/frappe/frappe-bench", "/tmp", False),
        ):
            for command in (
                f"RUN if true; then cd {target}; fi; chmod -R g=u .",
                f"RUN {{ cd {target}; }}; chmod -R g=u .",
                f"RUN command cd {target} && chmod -R g=u .",
                f"RUN builtin cd {target} && chmod -R g=u .",
                f"RUN if false; then cd /unreachable; elif true; then cd {target}; else cd /; fi; chmod -R g=u .",
            ):
                with self.subTest(workdir=workdir, command=command):
                    self.assertEqual(
                        bool(
                            sizes.permission_errors(
                                prefix + ["WORKDIR " + workdir, command]
                            )
                        ),
                        expected,
                    )

    def test_unexecuted_cd_branches_do_not_change_directory(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /home/frappe/frappe-bench",
        ]
        for command in (
            "RUN if false; then cd /tmp; fi; chmod -R g=u .",
            "RUN while false; do cd /tmp; done; chmod -R g=u .",
            "RUN false && cd /tmp; chmod -R g=u .",
            "RUN true || cd /tmp; chmod -R g=u .",
        ):
            with self.subTest(command=command):
                self.assertTrue(sizes.permission_errors(prefix + [command]))

    def test_finite_for_loops_apply_directory_changes(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /home/frappe/frappe-bench",
        ]
        self.assertEqual(
            sizes.permission_errors(
                prefix + ["RUN for item in once; do cd /tmp; done; chmod -R g=u ."]
            ),
            [],
        )
        self.assertTrue(
            sizes.permission_errors(
                prefix + ["RUN for item in; do cd /tmp; done; chmod -R g=u ."]
            )
        )

    def test_quoted_operators_remain_arguments(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /home/frappe/frappe-bench",
        ]
        self.assertTrue(
            sizes.permission_errors(
                prefix + ["RUN echo '&&' cd /tmp && chmod -R g=u ."]
            )
        )
        self.assertEqual(
            sizes.permission_errors(
                prefix + ["RUN cd /tmp && echo '(' && chmod -R g=u . && echo ')' "]
            ),
            [],
        )
        self.assertEqual(
            sizes.permission_errors(prefix + ["RUN echo chmod -R g=u ."]), []
        )

    def test_relative_and_quoted_workdir_instructions_are_resolved(self):
        for commands in (
            ["WORKDIR /home/frappe/frappe-bench", "WORKDIR apps"],
            ['WORKDIR "/home/frappe/frappe-bench"', 'WORKDIR "apps"'],
        ):
            self.assertTrue(
                sizes.permission_errors(
                    [
                        "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                        *commands,
                        "RUN chmod -R g=u .",
                    ]
                )
            )

    def test_relative_copy_destination_marks_the_bench(self):
        self.assertTrue(
            sizes.permission_errors(
                [
                    "WORKDIR /home/frappe/frappe-bench",
                    "COPY --from=builder /home/frappe/frappe-bench .",
                    "RUN chmod -R g=u .",
                ]
            )
        )

    def test_variable_copy_and_add_destinations_cannot_skip_the_bench(self):
        for operation in ("COPY --from=builder", "ADD"):
            for destination in ("$BENCH_DIR", "${BENCH_DIR}", "/home/${BENCH_NAME}"):
                for arguments in (
                    f"/home/frappe/frappe-bench {destination}",
                    json.dumps(["/home/frappe/frappe-bench", destination]),
                ):
                    with self.subTest(operation=operation, arguments=arguments):
                        source = (
                            "ENV BENCH_DIR=/home/frappe/frappe-bench\n"
                            "ENV BENCH_NAME=frappe-bench\n"
                            f"{operation} {arguments}\n"
                        )
                        prefix = sizes.instructions(source)
                        self.assertTrue(
                            sizes.permission_errors(
                                prefix
                                + [
                                    "RUN chmod -R g=u /home/frappe/frappe-bench",
                                ]
                            )
                        )
                        self.assertEqual(
                            sizes.permission_errors(
                                prefix
                                + [
                                    "RUN chmod -R g=u /tmp",
                                ]
                            ),
                            [],
                        )

    def test_json_run_forms(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /tmp",
        ]
        for command, expected in (
            ('RUN ["chmod", "-R", "g=u", "/home/frappe/frappe-bench"]', True),
            (
                'RUN ["/bin/sh", "-c", "cd /home/frappe/frappe-bench && chmod -R g=u ."]',
                True,
            ),
            ('RUN ["chmod", "-R", "g=u", "/tmp"]', False),
            (
                'RUN ["echo", "&&", "cd", "/home/frappe/frappe-bench", "chmod", "-R", "g=u", "."]',
                False,
            ),
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    bool(sizes.permission_errors(prefix + [command])), expected
                )

    def test_combined_shell_flags_inspect_the_command_string(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /tmp",
        ]
        for interpreter, flags in (
            ("/bin/sh", "-ec"),
            ("bash", "-euxc"),
            ("dash", "-xc"),
        ):
            for target, expected in (
                ("/home/frappe/frappe-bench", True),
                ("/tmp", False),
            ):
                script = "chmod -R g=u " + target
                for run in (
                    "RUN " + json.dumps([interpreter, flags, script]),
                    f"RUN {interpreter} {flags} '{script}'",
                ):
                    with self.subTest(run=run):
                        self.assertEqual(
                            bool(sizes.permission_errors(prefix + [run])), expected
                        )

    def test_globs_are_expanded_only_for_shell_words(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /tmp",
        ]
        for run, expected in (
            ("RUN chmod -R g=u /home/frappe/*", True),
            ("RUN chmod -R g=u /home/frappe/frappe-?ench", True),
            ("RUN chmod -R g=u /home/[f]rappe/*", True),
            ("RUN chmod -R g=u /tmp/*", False),
            ("RUN chmod -R g=u /home/**", True),
            ("RUN chmod -R g=u /tmp/**", False),
            ("RUN chmod -R g=u /home/frappe/*-other", False),
            ("RUN chmod -R g=u '/home/frappe/*'", False),
            (r"RUN chmod -R g=u /home/frappe/\*", False),
            ('RUN ["chmod", "-R", "g=u", "/home/frappe/*"]', False),
            ("RUN cd /home/frappe/* && chmod -R g=u .", True),
            ("RUN cd /tmp/* && chmod -R g=u .", False),
        ):
            with self.subTest(run=run):
                self.assertEqual(
                    bool(sizes.permission_errors(prefix + [run])), expected
                )

    def test_negative_chmod_modes_keep_the_target_operand(self):
        prefix = ["COPY /home/frappe/frappe-bench /home/frappe/frappe-bench"]
        for mode in ("-w", "-rwx", "-w,u+r"):
            for target, expected in (
                ("/home/frappe/frappe-bench", True),
                ("/tmp", False),
            ):
                for run in (
                    f"RUN chmod -R {mode} {target}",
                    "RUN " + json.dumps(["chmod", "--recursive", mode, target]),
                ):
                    with self.subTest(run=run):
                        self.assertEqual(
                            bool(sizes.permission_errors(prefix + [run])), expected
                        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "tree"
            root.mkdir(mode=0o755)
            root.chmod(0o755)
            sample = root / "sample"
            sample.write_text("test")
            sample.chmod(0o644)
            try:
                subprocess.run(["chmod", "-R", "-w", str(root)], check=True)
                self.assertEqual(root.stat().st_mode & 0o777, 0o555)
                self.assertEqual(sample.stat().st_mode & 0o777, 0o444)
            finally:
                subprocess.run(["chmod", "-R", "u+w", str(root)], check=True)

    def test_heredoc_expansions_execute_but_quoted_data_does_not(self):
        prefix = "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench\nWORKDIR /home/frappe/frappe-bench\n"
        for run, expected in (
            ("RUN cat <<EOF\n$(chmod -R g=u .)\nEOF\n", True),
            ("RUN cat <<EOF\n`chmod -R g=u .`\nEOF\n", True),
            ("RUN cat <<EOF\n'$(chmod -R g=u .)'\nEOF\n", True),
            ('RUN cat <<EOF\ntext " $(chmod -R g=u .)\nEOF\n', True),
            ("RUN cat <<'EOF'\n$(chmod -R g=u .)\nEOF\n", False),
            ('RUN cat <<"EOF"\n`chmod -R g=u .`\nEOF\n', False),
            ("RUN cat <<EOF\n\\$(chmod -R g=u .)\nEOF\n", False),
            ("RUN cat <<EOF\n$(chmod -R g=u /tmp)\nEOF\n", False),
            ("RUN cat <<EOF\n$\\\n(chmod -R g=u .)\nEOF\n", True),
        ):
            with self.subTest(run=run):
                self.assertEqual(
                    bool(sizes.permission_errors(sizes.instructions(prefix + run))),
                    expected,
                )

    def test_loop_bodies_are_revisited_after_directory_changes(self):
        prefix = [
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
            "WORKDIR /tmp",
        ]
        for run in (
            "RUN printf '%s\\n' first second | while read item; do chmod -R g=u .; cd /home/frappe/frappe-bench; done",
            "RUN until test -f /stop; do chmod -R g=u .; cd /home/frappe/frappe-bench; done",
            "RUN for item in $ITEMS; do chmod -R g=u .; cd /home/frappe/frappe-bench; done",
        ):
            with self.subTest(run=run):
                self.assertTrue(sizes.permission_errors(prefix + [run]))
        self.assertEqual(
            sizes.permission_errors(
                prefix
                + [
                    "RUN printf '%s\\n' first second | while read item; do chmod -R g=u .; cd /tmp; done",
                ]
            ),
            [],
        )

    def test_nonlocal_shell_control_cannot_hide_later_permissions(self):
        prefix = ["COPY /home/frappe/frappe-bench /home/frappe/frappe-bench"]
        for run in (
            "RUN while true; do break; done; chmod -R g=u /home/frappe/frappe-bench",
            "RUN for item in once; do continue; done; chmod -R g=u /home/frappe/frappe-bench",
            "RUN f() { while true; do return; done; }; f; chmod -R g=u /home/frappe/frappe-bench",
            "RUN (while true; do exit; done); chmod -R g=u /home/frappe/frappe-bench",
            "RUN while true; do command break; done; chmod -R g=u /home/frappe/frappe-bench",
        ):
            with self.subTest(run=run):
                with self.assertRaisesRegex(ValueError, "non-local shell control"):
                    sizes.permission_errors(prefix + [run])
        self.assertEqual(
            sizes.permission_errors(prefix + ["RUN echo 'break continue return exit'"]),
            [],
        )

    def test_shell_comments_do_not_create_heredocs(self):
        prefix = "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench\n"
        for run in (
            "RUN echo safe # example: cat <<EOF\n",
            "RUN <<SCRIPT\n# example: cat <<EOF\necho safe\nSCRIPT\n",
            "RUN <<SCRIPT\necho safe;# example: cat <<EOF\nSCRIPT\n",
            "RUN <<SCRIPT\necho safe # comment with an unmatched ' and <<EOF\necho still-safe\nSCRIPT\n",
        ):
            with self.subTest(run=run):
                self.assertEqual(
                    sizes.permission_errors(sizes.instructions(prefix + run)), []
                )

    def test_literal_hashes_do_not_hide_real_heredocs(self):
        prefix = "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench\n"
        for header in (
            "cat word#literal <<EOF",
            r"cat word\ #literal <<EOF",
            r"cat \#literal <<EOF",
            "cat <<EOF # example: cat <<OTHER",
        ):
            run = f"RUN {header}\n$(chmod -R g=u /home/frappe/frappe-bench)\nEOF\n"
            with self.subTest(header=header):
                self.assertTrue(
                    sizes.permission_errors(sizes.instructions(prefix + run))
                )
        source = (
            prefix
            + "RUN <<SCRIPT\n# example: cat <<IGNORED\ncat <<EOF\n$(chmod -R g=u /home/frappe/frappe-bench)\nEOF\nSCRIPT\n"
        )
        self.assertTrue(sizes.permission_errors(sizes.instructions(source)))

    def test_heredoc_run_forms_and_data(self):
        prefix = (
            "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench\nWORKDIR /tmp\n"
        )
        for command, expected in (
            ("RUN <<EOF\ncd /home/frappe/frappe-bench\nchmod -R g=u .\nEOF\n", True),
            ("RUN <<'EOF'\nchmod -R g=u /home/frappe/frappe-bench\nEOF\n", True),
            ("RUN <<-EOF\n\tchmod -R g=u /home/frappe/frappe-bench\n\tEOF\n", True),
            ("RUN sh <<EOF\nchmod -R g=u /home/frappe/frappe-bench\nEOF\n", True),
            ("RUN <<EOF sh\nchmod -R g=u /home/frappe/frappe-bench\nEOF\n", True),
            ("RUN\t<<EOF\nchmod -R g=u /home/frappe/frappe-bench\nEOF\n", True),
            ("RUN <<EOF\ncd /tmp\nchmod -R g=u .\nEOF\n", False),
            ("RUN cat <<EOF\nchmod -R g=u /home/frappe/frappe-bench\nEOF\n", False),
            ("RUN echo '<<EOF'\n", False),
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    bool(sizes.permission_errors(sizes.instructions(prefix + command))),
                    expected,
                )

    def test_all_recipes_reject_runtime_permission_forms(self):
        for filename in (sizes.ROOT / "images").glob("*/Containerfile"):
            source = filename.read_text()
            marker = next(
                line
                for line in source.splitlines()
                if line.startswith("COPY --from=builder")
            )
            for command in (
                'RUN ["chmod", "-R", "g=u", "/home/frappe/frappe-bench"]',
                "RUN <<EOF\nchmod -R g=u /home/frappe/frappe-bench\nEOF",
                'RUN ["/bin/sh", "-ec", "chmod -R g=u /home/frappe/frappe-bench"]',
                "RUN chmod -R g=u /home/frappe/*",
                "RUN chmod -R -w /home/frappe/frappe-bench",
                "RUN cat <<EOF\n$(chmod -R g=u /home/frappe/frappe-bench)\nEOF",
                "WORKDIR /tmp\nRUN printf '%s\\n' first second | while read item; do chmod -R g=u .; cd /home/frappe/frappe-bench; done",
            ):
                with self.subTest(filename=filename, command=command):
                    modified = source.replace(marker, marker + "\n" + command, 1)
                    self.assertTrue(
                        sizes.permission_errors(sizes.instructions(modified))
                    )

    def test_unsupported_shell_and_unterminated_heredoc_fail_explicitly(self):
        with self.assertRaises(ValueError):
            sizes.instructions("RUN <<EOF\nchmod -R g=u /home/frappe/frappe-bench\n")
        with self.assertRaises(ValueError):
            sizes.permission_errors(
                [
                    "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                    "RUN echo $((1 + 2))",
                ]
            )
        with self.assertRaisesRegex(ValueError, "brace expansion"):
            sizes.permission_errors(
                [
                    "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench",
                    "RUN bash -c 'chmod -R g=u /home/frappe/{frappe-bench,other}'",
                ]
            )

    def test_directory_analysis_agrees_with_real_shell_execution(self):
        bench = "/home/frappe/frappe-bench"
        cases = [
            (bench, "cd /tmp && chmod -R g=u ."),
            ("/tmp", f"if true; then cd {bench}; fi; chmod -R g=u ."),
            (bench, "if true; then cd /tmp; fi; chmod -R g=u ."),
            ("/tmp", f"{{ cd {bench}; }}; chmod -R g=u ."),
            (bench, "command cd /tmp && chmod -R g=u ."),
            (bench, "echo '&&' cd /tmp && chmod -R g=u ."),
            (bench, "cd /tmp && echo '(' && chmod -R g=u . && echo ')'"),
            (bench, "if false; then cd /tmp; fi; chmod -R g=u ."),
            (bench, "cat <<EOF\n$(chmod -R g=u .)\nEOF\n"),
            (bench, "cat <<'EOF'\n$(chmod -R g=u .)\nEOF\n"),
            (bench, "cat <<EOF\n`chmod -R g=u .`\nEOF\n"),
            (bench, "cat <<EOF\n'$(chmod -R g=u .)'\nEOF\n"),
            (bench, "cat <<EOF\n\\$(chmod -R g=u .)\nEOF\n"),
            (bench, "cat <<EOF\n$\\\n(chmod -R g=u .)\nEOF\n"),
            (
                "/tmp",
                "printf '%s\\n' first second | while read item; do chmod -R g=u .; cd /home/frappe/frappe-bench; done",
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual_bench, outside = root / "bench", root / "outside"
            actual_bench.mkdir()
            outside.mkdir()
            recording = root / "recording"
            # Record the directory only. Never execute the real chmod command.
            stub = 'chmod() { printf "%s\\n" "$PWD" >> "$PERMISSION_RECORD"; }; '
            for directory, script in cases:
                with self.subTest(directory=directory, script=script):
                    recording.write_text("")
                    executable = script.replace("/tmp", str(outside)).replace(
                        bench, str(actual_bench)
                    )
                    subprocess.run(
                        ["/bin/sh", "-c", stub + executable],
                        cwd=actual_bench if directory == bench else outside,
                        env={**os.environ, "PERMISSION_RECORD": str(recording)},
                        capture_output=True,
                        check=True,
                    )
                    executed_in_bench = (
                        str(actual_bench) in recording.read_text().splitlines()
                    )
                    errors = sizes.permission_errors(
                        [
                            f"COPY {bench} {bench}",
                            "WORKDIR " + directory,
                            "RUN " + script,
                        ]
                    )
                    self.assertEqual(bool(errors), executed_in_bench)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.run = {
            "id": 10,
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "head_repository": {"full_name": REPOSITORY},
            "path": WORKFLOW,
        }
        self.artifacts = [
            {
                "id": 101 + index,
                "name": sizes.artifact_name("erpnext", "16", arch),
                "expired": False,
                "workflow_run": {
                    "id": 10,
                    "head_branch": "main",
                    "repository_id": 1,
                    "head_repository_id": 1,
                },
            }
            for index, arch in enumerate(sizes.ARCHITECTURES)
        ]

    def api(self, endpoint, binary=False):
        self.calls.append(endpoint)
        if "/zip" in endpoint:
            self.assertTrue(binary)
            return archive(report())
        if "/runs/10/artifacts" in endpoint:
            return {"artifacts": self.artifacts}
        if endpoint.endswith("/runs/10"):
            return self.run
        if "/actions/artifacts?" in endpoint:
            return {"artifacts": self.artifacts[:1]}
        self.fail(f"Unexpected API call: {endpoint}")

    def find(self):
        return sizes.find_baseline(REPOSITORY, WORKFLOW, "erpnext", "16", 20, self.api)

    def test_successful_main_run_provides_both_architectures(self):
        baseline, ids = self.find()
        self.assertEqual(baseline["source"]["run_id"], 10)
        self.assertEqual(ids, {"amd64": 101, "arm64": 102})

    def test_failed_pr_wrong_branch_repository_and_workflow_are_rejected(self):
        for change in (
            {"conclusion": "failure"},
            {"conclusion": None},
            {"event": "pull_request"},
            {"event": "pull_request_target"},
            {"head_branch": "feature"},
            {"head_repository": {"full_name": "someone/frappe_docker"}},
            {"path": ".github/workflows/unrelated.yml"},
        ):
            with self.subTest(change=change):
                with patch.dict(self.run, change):
                    self.assertEqual(self.find(), (None, {}))

    def test_expired_fork_and_future_artifacts_are_rejected_before_download(self):
        for change in (
            {"expired": True},
            {
                "workflow_run": {
                    **self.artifacts[0]["workflow_run"],
                    "head_repository_id": 2,
                }
            },
            {"workflow_run": {**self.artifacts[0]["workflow_run"], "id": 21}},
        ):
            with self.subTest(change=change):
                self.calls.clear()
                with patch.dict(self.artifacts[0], change):
                    self.assertEqual(self.find(), (None, {}))
                self.assertEqual(len(self.calls), 1)

    def test_missing_architecture_prevents_partial_baseline(self):
        self.artifacts.pop()
        self.assertEqual(self.find(), (None, {}))

    def test_a_failed_newer_run_does_not_replace_a_successful_baseline(self):
        previous_api = self.api
        newer = copy.deepcopy(self.artifacts[0])
        newer["id"] = 103
        newer["workflow_run"]["id"] = 11

        def api(endpoint, binary=False):
            if "/actions/artifacts?" in endpoint:
                return {"artifacts": [newer, self.artifacts[0]]}
            if endpoint.endswith("/runs/11"):
                return {**self.run, "id": 11, "conclusion": "failure"}
            return previous_api(endpoint, binary=binary)

        baseline, ids = sizes.find_baseline(
            REPOSITORY, WORKFLOW, "erpnext", "16", 20, api
        )
        self.assertEqual(baseline["source"]["run_id"], 10)
        self.assertEqual(ids, {"amd64": 101, "arm64": 102})

    def test_an_older_run_finishing_late_does_not_replace_a_newer_baseline(self):
        previous_api = self.api
        newer = copy.deepcopy(self.artifacts)
        for item in newer:
            item["id"] += 100
            item["workflow_run"]["id"] = 11

        def api(endpoint, binary=False):
            if "/actions/artifacts?" in endpoint:
                return {"artifacts": [self.artifacts[0], newer[0]]}
            if endpoint.endswith("/runs/11"):
                return {**self.run, "id": 11}
            if "/runs/11/artifacts" in endpoint:
                return {"artifacts": newer}
            if endpoint.endswith("/201/zip"):
                return archive(report(run_id=11))
            return previous_api(endpoint, binary=binary)

        baseline, ids = sizes.find_baseline(
            REPOSITORY, WORKFLOW, "erpnext", "16", 20, api
        )
        self.assertEqual(baseline["source"]["run_id"], 11)
        self.assertEqual(ids, {"amd64": 201, "arm64": 202})

    def test_api_failure_is_not_treated_as_first_run(self):
        with patch.object(sizes, "github_api", side_effect=RuntimeError("unavailable")):
            with self.assertRaises(RuntimeError):
                sizes.find_baseline(
                    REPOSITORY, WORKFLOW, "erpnext", "16", 20, sizes.github_api
                )

    def test_pr_versions_are_taken_from_the_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "outputs"
            environment = {
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW}@refs/pull/1/merge",
                "GITHUB_RUN_ID": "20",
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_OUTPUT": str(output),
            }
            with (
                patch.dict(os.environ, environment),
                patch.object(
                    sizes, "find_baseline", return_value=(report(), {"amd64": 101})
                ),
                patch.object(sizes, "get_latest_tag") as resolve,
            ):
                sizes.prepare(argparse.Namespace(repo="erpnext", version="16"))
                resolve.assert_not_called()
            self.assertIn("frappe_version=v16.52.0\n", output.read_text())
            self.assertIn("erpnext_version=v16.51.1\n", output.read_text())

    def test_main_and_first_run_resolve_latest_versions_automatically(self):
        for event, baseline in (("push", report()), ("pull_request", None)):
            with self.subTest(event=event), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "outputs"
                environment = {
                    "GITHUB_REPOSITORY": REPOSITORY,
                    "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW}@refs/heads/main",
                    "GITHUB_RUN_ID": "20",
                    "GITHUB_EVENT_NAME": event,
                    "GITHUB_OUTPUT": str(output),
                }
                with (
                    patch.dict(os.environ, environment),
                    patch.object(sizes, "find_baseline", return_value=(baseline, {})),
                    patch.object(
                        sizes, "get_latest_tag", return_value="v16.99.0"
                    ) as resolve,
                ):
                    sizes.prepare(argparse.Namespace(repo="erpnext", version="16"))
                self.assertEqual(resolve.call_count, 2)
                self.assertIn("frappe_version=v16.99.0\n", output.read_text())


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.routes = {}
        self.requests = []
        self.config = {
            "os": "linux",
            "architecture": "amd64",
            "history": [
                {
                    "created_by": "COPY /home/frappe/frappe-bench /home/frappe/frappe-bench"
                },
                {
                    "created_by": "WORKDIR /home/frappe/frappe-bench",
                    "empty_layer": True,
                },
                {"created_by": "RUN chmod g=u /home/frappe/frappe-bench"},
                {"created_by": 'CMD ["start.sh"]', "empty_layer": True},
            ],
        }
        self.manifest = {
            "schemaVersion": 2,
            "config": {"digest": "sha256:config"},
            "layers": [
                {"digest": "sha256:bench", "size": 900 * MIB},
                {"digest": "sha256:assets", "size": 100 * MIB},
            ],
        }
        index = {
            "manifests": [
                {
                    "digest": "sha256:attestation",
                    "platform": {"os": "unknown", "architecture": "unknown"},
                },
                {
                    "digest": "sha256:amd64",
                    "platform": {"os": "linux", "architecture": "amd64"},
                },
                {
                    "digest": "sha256:arm64",
                    "platform": {"os": "linux", "architecture": "arm64"},
                },
            ]
        }
        for name, tag in (
            ("base", "v16.52.0"),
            ("build", "v16.51.1"),
            ("erpnext", "v16.51.1"),
        ):
            prefix = f"/v2/frappe/{name}"
            self.routes[f"{prefix}/manifests/{tag}"] = index
            self.routes[f"{prefix}/manifests/sha256:amd64"] = self.manifest
            self.routes[f"{prefix}/blobs/sha256:config"] = self.config
        routes, requests = self.routes, self.requests

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                payload = routes.get(self.path)
                self.send_response(200 if payload else 404)
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.registry = f"127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_index_platform_selection_and_empty_history_entries(self):
        image = sizes.measure_image(self.registry, "erpnext", "v16.51.1", "amd64")
        self.assertEqual(image["compressed_bytes"], 1000 * MIB)
        self.assertEqual(len(image["layers"]), 2)
        self.assertEqual(len(image["history"]), 4)
        self.assertEqual(
            image["layers"][1]["command"], self.config["history"][2]["created_by"]
        )
        self.assertEqual(
            len(self.requests), 3
        )  # Index, manifest, config; no filesystem blobs.

    def test_wrong_platform_is_an_error(self):
        self.config["architecture"] = "arm64"
        with self.assertRaisesRegex(ValueError, "Wrong platform"):
            sizes.measure_image(self.registry, "erpnext", "v16.51.1", "amd64")

    def test_arm64_manifest_is_selected_and_verified(self):
        prefix = "/v2/frappe/erpnext"
        arm_manifest = copy.deepcopy(self.manifest)
        arm_manifest["config"]["digest"] = "sha256:config-arm64"
        self.routes[f"{prefix}/manifests/sha256:arm64"] = arm_manifest
        self.routes[f"{prefix}/blobs/sha256:config-arm64"] = {
            **self.config,
            "architecture": "arm64",
        }
        image = sizes.measure_image(self.registry, "erpnext", "v16.51.1", "arm64")
        self.assertEqual(image["compressed_bytes"], 1000 * MIB)
        self.assertIn(f"{prefix}/manifests/sha256:arm64", self.requests)
        self.assertNotIn(f"{prefix}/manifests/sha256:amd64", self.requests)

    def test_mislabeled_arm64_build_reports_the_actual_platform(self):
        index = self.routes["/v2/frappe/erpnext/manifests/v16.51.1"]
        index["manifests"] = [index["manifests"][1]]
        with self.assertRaisesRegex(ValueError, "linux/arm64.*available: linux/amd64"):
            sizes.measure_image(self.registry, "erpnext", "v16.51.1", "arm64")

    def test_inconsistent_history_is_an_error(self):
        self.config["history"].pop(0)
        with self.assertRaisesRegex(ValueError, "history does not match"):
            sizes.measure_image(self.registry, "erpnext", "v16.51.1", "amd64")

    def test_cli_reports_failure_and_keeps_measurements(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            previous = report(700 * MIB)
            previous["images"]["base"] = copy.deepcopy(previous["images"]["erpnext"])
            previous["images"]["build"] = copy.deepcopy(previous["images"]["erpnext"])
            baseline = directory / "baseline.json"
            baseline.write_text(json.dumps(previous))
            output = directory / "report.json"
            summary = directory / "summary.md"
            environment = {
                **os.environ,
                **{key.upper(): value for key, value in report()["inputs"].items()},
            }
            environment["GITHUB_STEP_SUMMARY"] = str(summary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(sizes.__file__)),
                    "check",
                    "--repo",
                    "erpnext",
                    "--version",
                    "16",
                    "--arch",
                    "amd64",
                    "--registry",
                    self.registry,
                    "--baseline",
                    str(baseline),
                    "--output",
                    str(output),
                ],
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("size limit exceeded", result.stdout)
            self.assertIn("FAIL", summary.read_text())
            self.assertEqual(
                json.loads(output.read_text())["images"]["erpnext"]["compressed_bytes"],
                1000 * MIB,
            )
            self.assertEqual(len(self.requests), 9)


if __name__ == "__main__":
    unittest.main()
