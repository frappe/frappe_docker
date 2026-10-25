"""Analyse Dockerfile source without executing shell commands or image history."""

from __future__ import annotations

import fnmatch
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
    path = posixpath.normpath(posixpath.join(directory or "/", target))
    return (
        Glob(path)
        if isinstance(target, Glob)
        or (isinstance(directory, Glob) and not target.startswith("/"))
        else path
    )


class Glob(str):
    """A pathname pattern with at least one unquoted expansion character."""

    def __eq__(self, other):
        return isinstance(other, Glob) and str.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((Glob, str(self)))


def touches_bench(target: str | None, directory: str | None) -> bool:
    path = resolve(directory, target)
    if isinstance(path, Glob):
        parts = path.strip("/").split("/")
        bench_parts = BENCH.strip("/").split("/")
        if "**" in parts:
            prefix = re.split(r"[*?\[]", path, maxsplit=1)[0].rstrip("/") or "/"
            return touches_bench(prefix, "/")
        return all(
            index >= len(bench_parts) or fnmatch.fnmatchcase(bench_parts[index], part)
            for index, part in enumerate(parts)
        )
    return path is None or (
        path == BENCH
        or path.startswith(BENCH + "/")
        or BENCH.startswith(path.rstrip("/") + "/")
    )


def shell_heredocs(script: str):
    """Make quoted delimiters parseable by bashlex, retaining expansion rules."""
    output = []
    documents = {}
    written = search = 0
    while match := HEREDOC.search(script, search):
        if match["doc"] is None:
            search = match.end()
            continue
        start = script.rfind("\n", 0, match.start()) + 1
        end = script.find("\n", match.end())
        if end < 0:
            raise ValueError("Unterminated shell heredoc")
        header = script[start:end]
        markers = heredocs(script[match.start() : end])
        offset = match.start() - start
        body_start = end + 1
        replacements = []
        bodies = []
        for left, right, delimiter, tabs in markers:
            left, right = left + offset, right + offset
            name = f"__FRAPPE_GUARD_HEREDOC_{len(documents)}__"
            while name in script or name in documents:
                name += "_"
            body_end = body_start
            while True:
                line_end = script.find("\n", body_end)
                if line_end < 0:
                    line_end = len(script)
                line = script[body_end:line_end]
                if (line.lstrip("\t") if tabs else line) == delimiter:
                    break
                if line_end == len(script):
                    raise ValueError(f"Unterminated shell heredoc: {delimiter}")
                body_end = line_end + 1
            body = script[body_start:body_end]
            quoted = any(char in header[left:right] for char in "'\"\\")
            documents[name] = body, not quoted
            replacements.append((left, right, ("<<-" if tabs else "<<") + name))
            bodies.append(body + name + "\n")
            body_start = line_end + 1 if line_end < len(script) else line_end
        for left, right, replacement in reversed(replacements):
            header = header[:left] + replacement + header[right:]
        output.extend((script[written:start], header, "\n", *bodies))
        written = search = body_start
    output.append(script[written:])
    return "".join(output), documents


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
        self.source = ""
        self.documents = {}
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

        previous = self.source, self.documents
        self.source, self.documents = shell_heredocs(script)
        try:
            nodes = bashlex.parse(self.source)
            return self.sequence(nodes, states)
        except (bashlex.errors.ParsingError, NotImplementedError) as exc:
            raise ValueError(f"Cannot analyse runtime shell syntax: {exc}") from exc
        finally:
            self.source, self.documents = previous

    def word(self, node):
        if node.parts:
            return None
        raw = self.source[node.pos[0] : node.pos[1]]
        quote = None
        escaped = False
        pattern = False
        unquoted = []
        for char in raw:
            if escaped:
                escaped = False
                unquoted.append(" ")
            elif char == "\\" and quote != "'":
                escaped = True
            elif char == quote:
                quote = None
            elif char in "'\"" and quote is None:
                quote = char
            elif quote is None and char in "*?[":
                pattern = True
                unquoted.append(char)
            elif quote is None:
                unquoted.append(char)
            else:
                unquoted.append(" ")
        if re.search(r"\{[^{}]*(?:,|\.\.)[^{}]*\}", "".join(unquoted)):
            raise ValueError("Cannot analyse shell brace expansion")
        return Glob(node.word) if pattern else node.word

    def loop(self, body, states, condition=None, until=False):
        pending, seen = set(states), set()
        exits = set(states) if condition is None else set()
        while pending:
            current = pending - seen
            if not current:
                break
            seen |= current
            if len(seen) > 64:
                unknown = {Directory(None)}
                if condition is not None:
                    self.visit(condition, unknown)
                self.visit(body, unknown)
                return exits | unknown, set()
            enter = current
            if condition is not None:
                yes, no = self.visit(condition, current)
                enter, skip = (no, yes) if until else (yes, no)
                exits |= skip
            good, bad = self.visit(body, enter)
            pending = good | bad
            if condition is None:
                exits |= pending
        return exits, set()

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
            argv = [self.word(word) for word in words]
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
            return self.loop(node.parts[3], states, node.parts[1], node.kind == "until")
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
                values = [self.word(part) for part in items]
                if all(
                    value is not None and not isinstance(value, Glob)
                    for value in values
                ):
                    flow = states, set()
                    for _ in items:
                        flow = self.visit(body, flow[0] | flow[1])
                    return flow
            return self.loop(body, states)
        if node.kind == "function":
            self.functions[node.parts[0].word] = node.parts[-1]
            return set(states), set()
        raise ValueError(f"Cannot analyse runtime shell construct: {node.kind}")

    def substitutions(self, node, states):
        if node.kind in ("commandsubstitution", "processsubstitution"):
            self.visit(node.command, states)
        if node.kind == "redirect" and getattr(node, "heredoc", None):
            body, expands = self.documents[node.output.word]
            if expands and body:
                self.heredoc_substitutions(body, states)
        for child in getattr(node, "parts", []):
            self.substitutions(child, states)

    def heredoc_substitutions(self, body, states):
        # bashlex 0.18 does not expand heredoc AST nodes. Reuse its pinned
        # here-document word expander, where quotes are data and $()/`...` run.
        from bashlex import errors, flags, parser, subst, tokenizer, utils

        # Unquoted heredocs join backslash-newline before expanding $()/backticks.
        joined = []
        index = 0
        while index < len(body):
            if body[index] == "\\" and index + 1 < len(body):
                if body[index + 1] == "\n":
                    index += 2
                    continue
                if body[index + 1] in "\\$`":
                    joined.append(body[index : index + 2])
                    index += 2
                    continue
            joined.append(body[index])
            index += 1
        body = "".join(joined)
        previous = self.source
        self.source = body
        try:
            word = tokenizer.token(
                tokenizer.tokentype.WORD,
                body,
                pos=(0, len(body)),
                flags=utils.typedset(
                    flags.word, [flags.word.DQUOTE, flags.word.NOTILDE]
                ),
            )
            parts, _ = subst._expandwordinternal(
                parser._parser(body), word, True, True, True, False
            )
            for part in parts:
                self.substitutions(part, states)
        except (errors.ParsingError, NotImplementedError) as exc:
            raise ValueError(f"Cannot analyse heredoc expansion: {exc}") from exc
        finally:
            self.source = previous

    def command(self, argv, states, redirects=()):
        if not argv:
            return set(states), set()
        if argv[0] is None or isinstance(argv[0], Glob):
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
            index = 1
            script = None
            stdin = False
            while index < len(argv):
                option = argv[index]
                if option is None:
                    raise ValueError("Cannot analyse dynamic shell options")
                if option == "--":
                    index += 1
                    break
                if not option.startswith(("-", "+")):
                    break
                stdin |= (
                    option.startswith("-")
                    and not option.startswith("--")
                    and "s" in option
                )
                if (
                    option.startswith("-")
                    and not option.startswith("--")
                    and "c" in option
                ):
                    if index + 1 >= len(argv) or argv[index + 1] is None:
                        raise ValueError(
                            "Cannot analyse a dynamic runtime shell script"
                        )
                    script = argv[index + 1]
                    break
                index += (
                    2
                    if option in ("-o", "+o", "-O", "+O", "--rcfile", "--init-file")
                    else 1
                )
            if script is not None:
                self.shell(script, states)
            elif stdin or index >= len(argv):
                inputs = [
                    redirect
                    for redirect in redirects
                    if getattr(redirect, "input", None) in (None, 0)
                ]
                if inputs and getattr(inputs[-1], "heredoc", None):
                    self.shell(self.documents[inputs[-1].output.word][0], states)
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
                elif (
                    name == "chmod"
                    and not operands
                    and arg is not None
                    and re.fullmatch(
                        r"[ugoa]*(?:[+=-][rwxXstugo]*)+(?:,[ugoa]*(?:[+=-][rwxXstugo]*)+)*",
                        arg,
                    )
                ):
                    operands.append(arg)
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
            target = paths[-1]
            destination = resolve(directory, None if "$" in target else target)
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
