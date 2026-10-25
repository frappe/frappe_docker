"""Analyse Dockerfile source without executing shell commands or image history."""

from __future__ import annotations

import json
import posixpath
import re
import shlex
from dataclasses import dataclass

BENCH = "/home/frappe/frappe-bench"
HEREDOC = re.compile(
    r"'[^']*'|\"(?:\\.|[^\"\\])*\"|\\.|"
    r"(?P<doc><<(?P<tabs>-?)\s*(?P<delimiter>(?:'[^']*'|\"(?:\\.|[^\"\\])*\"|[^\s'\";|&<>()])+))"
)


def heredocs(header: str):
    return [
        (
            match.start(),
            match.end(),
            shlex.split(match["delimiter"])[0],
            bool(match["tabs"]),
        )
        for match in HEREDOC.finditer(header)
        if match["doc"] is not None
    ]


def instructions(text: str) -> list[str]:
    """Keep RUN heredoc bodies attached to their Dockerfile instruction."""
    lines = iter(text.splitlines())
    result = []
    pending = ""
    escape = "\\"
    for raw in lines:
        directive = re.fullmatch(r"\s*#\s*escape\s*=\s*([`\\])\s*", raw, re.I)
        if directive:
            escape = directive[1]
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        line = raw.lstrip()
        if line.endswith(escape):
            pending += line[:-1]
            continue
        header = pending + line
        pending = ""
        parts = header.split(None, 1)
        operation, value = parts[0], parts[1] if len(parts) > 1 else ""
        markers = heredocs(value) if operation.upper() in ("RUN", "COPY", "ADD") else []
        body = []
        for _, _, delimiter, tabs in markers:
            for line in lines:
                body.append(line)
                if (line.lstrip("\t") if tabs else line) == delimiter:
                    break
            else:
                raise ValueError(f"Unterminated Dockerfile heredoc: {delimiter}")
        result.append(header + ("\n" + "\n".join(body) if body else ""))
    if pending:
        raise ValueError("Unterminated Dockerfile continuation")
    return result


def resolve(directory: str | None, target: str | None) -> str | None:
    if target is None or (directory is None and not target.startswith("/")):
        return None
    return posixpath.normpath(posixpath.join(directory or "/", target))


def touches_bench(target: str | None, directory: str | None) -> bool:
    path = resolve(directory, target)
    return path is None or (
        path == BENCH
        or path.startswith(BENCH + "/")
        or BENCH.startswith(path.rstrip("/") + "/")
    )


@dataclass(frozen=True)
class Directory:
    current: str | None
    previous: str | None = None


class ShellGuard:
    """Conservatively propagate directories through a parsed shell syntax tree."""

    def __init__(self, directory: str | None):
        self.directory = directory
        self.unsafe = False
        self.functions = {}
        self.calls = set()
        self.known = {"/", "/tmp", BENCH}
        for path in (directory, BENCH):
            while path:
                self.known.add(path)
                parent = posixpath.dirname(path)
                if parent == path:
                    break
                path = parent

    def shell(self, script, states):
        import bashlex

        try:
            nodes = bashlex.parse(script)
        except (bashlex.errors.ParsingError, NotImplementedError) as exc:
            raise ValueError(f"Cannot analyse runtime shell syntax: {exc}") from exc
        return self.sequence(nodes, states)

    def sequence(self, nodes, states):
        flow = states, set()
        for node in nodes:
            if node.kind not in ("reservedword", "operator", "pipe"):
                flow = self.visit(node, flow[0] | flow[1])
        return flow

    def visit(self, node, states):
        if not states:
            return set(), set()
        if node.kind == "command":
            for part in node.parts:
                self.substitutions(part, states)
            words = [part for part in node.parts if part.kind == "word"]
            argv = [None if word.parts else word.word for word in words]
            redirects = [part for part in node.parts if part.kind == "redirect"]
            return self.command(argv, states, redirects)
        if node.kind == "list":
            flow = states, set()
            origin = states
            operator = ";"
            for part in node.parts:
                if part.kind == "operator":
                    operator = part.op
                    if operator == "&":
                        flow = origin, set()
                    continue
                origin = flow[0] | flow[1]
                if operator == "&&":
                    success, failure = self.visit(part, flow[0])
                    flow = success, flow[1] | failure
                elif operator == "||":
                    success, failure = self.visit(part, flow[1])
                    flow = flow[0] | success, failure
                else:
                    flow = self.visit(part, origin)
            return flow
        if node.kind == "compound":
            flow = self.sequence(node.list, states)
            if node.list and getattr(node.list[0], "word", None) == "(":
                return (
                    set(states) if flow[0] else set(),
                    set(states) if flow[1] else set(),
                )
            return flow
        if node.kind == "pipeline":
            for part in node.parts:
                if part.kind not in ("pipe", "reservedword"):
                    self.visit(part, states)
            return set(states), set(states)
        if node.kind == "if":
            success, failure = set(), set()
            pending = states
            index = 0
            while index < len(node.parts):
                part = node.parts[index]
                if getattr(part, "word", None) in ("if", "elif"):
                    yes, pending = self.visit(node.parts[index + 1], pending)
                    good, bad = self.visit(node.parts[index + 3], yes)
                    success |= good
                    failure |= bad
                    index += 4
                elif getattr(part, "word", None) == "else":
                    good, bad = self.visit(node.parts[index + 1], pending)
                    success |= good
                    failure |= bad
                    pending = set()
                    index += 2
                else:
                    index += 1
            return success | pending, failure
        if node.kind in ("while", "until"):
            yes, no = self.visit(node.parts[1], states)
            enter, skip = (no, yes) if node.kind == "until" else (yes, no)
            good, bad = self.visit(node.parts[3], enter)
            after = skip | good | bad
            if after != states:
                after.add(Directory(None))
            return after, set()
        if node.kind == "for":
            body = next(part for part in node.parts if part.kind == "list")
            keywords = [getattr(part, "word", None) for part in node.parts]
            if "in" in keywords:
                items = [
                    part
                    for part in node.parts[
                        keywords.index("in") + 1 : keywords.index("do")
                    ]
                    if part.kind == "word"
                ]
                if all(
                    not part.parts and not any(char in part.word for char in "*?[")
                    for part in items
                ):
                    flow = states, set()
                    for _ in items:
                        flow = self.visit(body, flow[0] | flow[1])
                    return flow
            good, bad = self.visit(body, states)
            after = states | good | bad
            if after != states:
                after.add(Directory(None))
            return after, set()
        if node.kind == "function":
            self.functions[node.parts[0].word] = node.parts[-1]
            return set(states), set()
        raise ValueError(f"Cannot analyse runtime shell construct: {node.kind}")

    def substitutions(self, node, states):
        if node.kind in ("commandsubstitution", "processsubstitution"):
            self.visit(node.command, states)
        for child in getattr(node, "parts", []):
            self.substitutions(child, states)

    def command(self, argv, states, redirects=()):
        if not argv:
            return set(states), set()
        if argv[0] is None:
            raise ValueError("Cannot analyse a dynamically selected runtime command")
        name = posixpath.basename(argv[0])
        if name in ("command", "builtin", "exec"):
            if any(arg in ("-v", "-V") for arg in argv[1:2]):
                return set(states), set(states)
            args = argv[1:]
            while args and args[0] in ("--", "-p"):
                args = args[1:]
            return self.command(args, states, redirects)
        if name in ("env", "sudo"):
            args = argv[1:]
            while (
                args
                and args[0] is not None
                and (args[0].startswith("-") or "=" in args[0])
            ):
                args = args[1:]
            good, bad = self.command(args, states, redirects)
            return (set(states) if good else set(), set(states) if bad else set())
        if name in ("true", ":"):
            return set(states), set()
        if name == "false":
            return set(), set(states)
        if name == "cd":
            args = [arg for arg in argv[1:] if arg not in ("--", "-L", "-P")]
            good, bad = set(), set()
            for state in states:
                target = (
                    state.previous
                    if args == ["-"]
                    else (args[0] if len(args) == 1 else None)
                )
                path = resolve(state.current, target)
                good.add(Directory(path, state.current))
                if path not in self.known and target != state.previous:
                    bad.add(state)
            return good, bad
        if name in ("sh", "bash", "dash", "ash"):
            if "-c" in argv[1:]:
                index = argv.index("-c") + 1
                if index >= len(argv) or argv[index] is None:
                    raise ValueError("Cannot analyse a dynamic runtime shell script")
                self.shell(argv[index], states)
            else:
                for redirect in redirects:
                    if getattr(redirect, "heredoc", None):
                        self.shell(redirect.heredoc.value.rsplit("\n", 1)[0], states)
            return set(states), set(states)
        if name in self.functions:
            if name in self.calls:
                raise ValueError("Cannot analyse recursive runtime shell functions")
            self.calls.add(name)
            try:
                return self.visit(self.functions[name], states)
            finally:
                self.calls.remove(name)
        if name in ("chmod", "chown", "chgrp"):
            recursive = False
            reference = False
            operands = []
            options = True
            for arg in argv[1:]:
                if options and arg == "--":
                    options = False
                elif options and arg is not None and arg.startswith("-"):
                    recursive |= arg == "--recursive" or (
                        not arg.startswith("--") and "R" in arg
                    )
                    reference |= arg.startswith("--reference=")
                else:
                    operands.append(arg)
            targets = operands if reference else operands[1:]
            if recursive and any(
                touches_bench(target, state.current)
                for state in states
                for target in targets
            ):
                self.unsafe = True
        return set(states), set(states)

    def run(self, value: str) -> bool:
        while value.startswith("--"):
            match = re.match(r"--(?:[^\s'\"]|'[^']*'|\"[^\"]*\")+\s+", value)
            if not match:
                raise ValueError("Cannot analyse Dockerfile RUN options")
            value = value[match.end() :]
        state = {Directory(self.directory)}
        if value.startswith("["):
            argv = json.loads(value)
            if not isinstance(argv, list) or not all(
                isinstance(word, str) for word in argv
            ):
                raise ValueError("Invalid JSON RUN instruction")
            self.command(argv, state)
        else:
            header, _, body = value.partition("\n")
            markers = heredocs(header)
            if len(markers) == 1 and markers[0][0] == 0:
                start, end, delimiter, tabs = markers[0]
                suffix = header[end:].strip()
                if not suffix:
                    lines = body.splitlines()
                    if (
                        not lines
                        or (lines[-1].lstrip("\t") if tabs else lines[-1]) != delimiter
                    ):
                        raise ValueError("Unterminated RUN heredoc")
                    script = "\n".join(
                        line.lstrip("\t") if tabs else line for line in lines[:-1]
                    )
                    if script.startswith("#!") and not re.match(
                        r"#![^\n]*\b(?:sh|bash|dash|ash)\b", script
                    ):
                        raise ValueError("Cannot analyse a non-shell RUN heredoc")
                    self.shell(script, state)
                else:
                    self.shell(value, state)
            else:
                self.shell(value, state)
        return self.unsafe


def permission_errors(commands: list[str]) -> list[str]:
    copied = False
    directory = "/"
    stages = {}
    stage = ""
    errors = []
    for instruction in commands:
        match = re.match(r"(\S+)\s+([\s\S]*)", instruction)
        if not match:
            continue
        operation, value = match[1].upper(), match[2]
        if operation == "FROM":
            words = shlex.split(value)
            words = [word for word in words if not word.startswith("--")]
            copied, directory = stages.get(words[0].lower(), (False, "/"))
            stage = words[-1].lower() if len(words) >= 3 else ""
        elif operation in ("COPY", "ADD"):
            header = value.partition("\n")[0]
            while header.startswith("--"):
                match = re.match(r"--(?:[^\s'\"]|'[^']*'|\"[^\"]*\")+\s+", header)
                if not match:
                    raise ValueError("Cannot analyse Dockerfile COPY options")
                header = header[match.end() :]
            paths = (
                json.loads(header) if header.startswith("[") else shlex.split(header)
            )
            destination = resolve(directory, paths[-1])
            if (
                destination is None
                or destination == BENCH
                or destination.startswith(BENCH + "/")
            ):
                copied = True
            elif BENCH in paths[:-1] and touches_bench(destination, directory):
                copied = True
        elif operation == "WORKDIR":
            target = " ".join(shlex.split(value))
            directory = resolve(directory, None if "$" in target else target)
        elif operation == "RUN" and copied and ShellGuard(directory).run(value):
            errors.append(
                "Recursive permissions after the bench COPY duplicate its files: "
                + instruction
            )
        if stage:
            stages[stage] = copied, directory
    return errors
