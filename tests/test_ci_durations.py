"""The CI test lines of this repository print their slowest tests: for every ``pytest`` and ``python -m unittest``
invocation of ``.github/workflows`` the configuration that effectively applies (the ini file pytest discovers, its
``addopts``, a ``-o addopts=`` or ``-c`` on the line, the line's own options) must give ``--durations=25
--durations-min=1.0`` (pytest) or ``--durations 25`` (unittest). The resolution below is a copy of the shared guard of
the organisation's ``.github`` repository (``guards/durations.py``), without its script check; the fixtures show what
fails (the invocation is named) and what passes."""
import configparser
import re
import shlex
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PYTEST_DURATIONS, PYTEST_DURATIONS_MIN, UNITTEST_DURATIONS = 25, 1.0, 25
_VALUE_OPTS = {"-m", "-k", "-p", "-c", "-o", "-n", "-W", "--maxfail", "--junitxml", "--durations", "--durations-min",
               "--timeout", "--cov-report", "--cov", "--tb", "--color", "--deselect", "--confcutdir", "--basetemp",
               "--ignore", "--ignore-glob", "--override-ini", "--config-file", "--import-mode", "--log-level"}
_COLLECT_ONLY = {"--collect-only", "--co"}
_ENV = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_PYTHON = re.compile(r"python[\d.]*$")


def _segments(text):
    """``(line number, tokens)`` of every command of the file: continuation lines joined, comments cut, split at
    ``&&``, ``||``, ``;`` and ``|``, a leading ``run:`` / ``- `` / env assignment dropped."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        start, line = i + 1, lines[i]
        while line.rstrip().endswith("\\") and i + 1 < len(lines):
            i += 1
            line = line.rstrip()[:-1] + " " + lines[i]
        i += 1
        line = re.sub(r"(^|\s)#.*$", "", line)
        for part in re.split(r"&&|\|\||;|\|", line):
            try:
                tokens = shlex.split(part.replace("$(", "$ (").replace("${{", "$ {{"))
            except ValueError:
                tokens = part.split()
            while tokens and tokens[0] in ("-", "run:"):
                tokens = tokens[1:]
            if tokens and tokens[0].endswith(":"):                      # a key of another kind (name:, uses:, env: ...)
                continue
            while tokens and _ENV.match(tokens[0]):
                tokens = tokens[1:]
            if tokens:
                yield start, tokens


def _steps(text):
    """``(first line, last line, working-directory or None)`` of every step of the file; ``defaults`` raise."""
    lines = text.splitlines()
    out = []
    for n, line in enumerate(lines):
        m = re.match(r"(\s*)- \S", line)
        if not m:
            continue
        indent, end, wd = len(m.group(1)), n, None
        while end + 1 < len(lines) and (not lines[end + 1].strip() or len(lines[end + 1]) - len(lines[end + 1].lstrip()) > indent):
            end += 1
        for k in range(n, end + 1):
            w = re.match(r"\s*(?:- )?working-directory:\s*(\S+)", lines[k])
            if w and len(lines[k]) - len(lines[k].lstrip()) <= indent + 2:
                wd = w.group(1).strip("'\"")
        out.append((n + 1, end + 1, wd))
    return out


def _is_defaults_wd(text):
    """True when a ``defaults:`` block of the file sets a ``working-directory``."""
    lines = text.splitlines()
    return any(re.match(r"\s*defaults:\s*$", ln) and any("working-directory:" in x for x in lines[n + 1:n + 5])
               for n, ln in enumerate(lines))


def _invocation(tokens):
    """``("pytest" | "unittest", index after the command word)`` or None."""
    for k, t in enumerate(tokens):
        prev = tokens[k - 1] if k else ""
        if t in ("pytest", "py.test") and (k == 0 or prev in ("-m", "run", "exec") or _PYTHON.match(prev.rsplit("/", 1)[-1])):
            return "pytest", k + 1
        if t == "unittest" and prev == "-m":
            return "unittest", k + 1
    return None


def _addopts(f):
    """The ``addopts`` list of a pytest configuration file, or None when it has no pytest table."""
    text = f.read_text()
    if f.name.endswith(".toml"):
        table = tomllib.loads(text).get("tool", {}).get("pytest", {}).get("ini_options")
        if table is None:
            return None
        v = table.get("addopts", "")
    else:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read_string(text)
        section = "tool:pytest" if f.name == "setup.cfg" else "pytest"
        if not cp.has_section(section):
            return None
        v = cp.get(section, "addopts", fallback="")
    return list(v) if isinstance(v, list) else shlex.split(v.replace("\n", " "))


def _inifile(root, start):
    """The configuration file pytest's discovery picks from directory ``start`` upwards, or None."""
    d = start
    while True:
        for name in ("pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"):
            f = root / d / name
            if f.is_file():
                if name in ("pytest.ini", ".pytest.ini") or _addopts(f) is not None:
                    return f
        if d == Path("."):
            return None
        d = d.parent


def _option(tokens, name):
    """The last value of ``name`` among ``tokens`` (``--name=v`` or ``--name v``), or None."""
    val = None
    for i, t in enumerate(tokens):
        if t.startswith(name + "="):
            val = t.split("=", 1)[1]
        elif t == name and i + 1 < len(tokens):
            val = tokens[i + 1]
    return val


def _pytest(root, wd, args):
    """``None`` when the invocation prints 25 slowest at 1.0 s, else the reason."""
    if any(t.startswith("--rootdir") for t in args):
        return "uses --rootdir; the guard cannot resolve the configuration that applies"
    if any("$" in t and t.startswith("-") for t in args):
        return "an option made of a variable; the guard cannot resolve what pytest receives"
    if _COLLECT_ONLY & set(args):
        return None
    paths, i = [], 0
    while i < len(args):
        t = args[i]
        if t.startswith("-"):
            i += 2 if (t in _VALUE_OPTS and "=" not in t) else 1
            continue
        paths.append(t)
        i += 1
    ancestors, unresolved = [], False
    for p in paths:
        p = re.split(r"::", p)[0]
        if "$" in p:
            unresolved = True                                   # a path made of a variable: any directory below may apply
            continue
        p = re.split(r"[*?\[]", p)[0].rstrip("/") or "."
        q = (wd / p) if wd else Path(p)
        if (root / q).exists():
            ancestors.append(q if (root / q).is_dir() else q.parent)
    start = wd or Path(".")
    if ancestors:
        parts = [a.parts for a in ancestors]
        common = []
        for group in zip(*parts):
            if len(set(group)) != 1:
                break
            common.append(group[0])
        start = Path(*common) if common else Path(".")
    starts = [start]
    if unresolved:
        starts += _config_dirs(root, start)
    for s in starts:
        reason = _judge(root, wd, args, s)
        if reason:
            return reason + (f" (for a path made of a variable: as run from {s})" if s != start else "")
    return None


def _config_dirs(root, start):
    """The directories below ``start`` that hold a pytest configuration file."""
    found = []
    for f in sorted((root / start).rglob("*")):
        rel = f.relative_to(root)
        if f.name in ("pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg") and f.is_file() \
                and not {".git", "node_modules"} & set(rel.parts):
            if f.name in ("pytest.ini", ".pytest.ini") or _addopts(f) is not None:
                found.append(rel.parent)
    return [d for d in dict.fromkeys(found) if d != start]


def _judge(root, wd, args, start):
    """``None`` when pytest, run with ``args`` as discovered from ``start``, prints 25 slowest at 1.0 s, else the reason."""
    cfg = _option(args, "-c") or _option(args, "--config-file")
    if wd is not None and not (root / wd).exists():
        base = []                                               # a second checkout: no configuration of this repository
    elif cfg:
        f = root / (wd or ".") / cfg
        if not f.is_file():
            return f"names the configuration file {cfg}, which the guard cannot read"
        base = _addopts(f)
        if base is None:
            base = []
    else:
        f = _inifile(root, start)
        base = _addopts(f) if f else []
    override = [t.split("=", 1)[1] for t in args if t.startswith("addopts=")]
    for i, t in enumerate(args):
        if t in ("-o", "--override-ini") and i + 1 < len(args) and args[i + 1].startswith("addopts="):
            override.append(args[i + 1].split("=", 1)[1])
        if t.startswith("-oaddopts="):
            override.append(t.split("=", 1)[1])
    if override:
        base = shlex.split(override[-1])
    effective = base + args
    if _COLLECT_ONLY & set(effective):
        return None
    for i, t in enumerate(effective):
        if t in ("-p", ) and i + 1 < len(effective) and effective[i + 1] in ("no:terminal", "no:terminalreporter"):
            return "disables the terminal reporter (-p no:terminal), so no durations are printed"
        if t in ("-pno:terminal", "-pno:terminalreporter"):
            return "disables the terminal reporter, so no durations are printed"
    n, m = _option(effective, "--durations"), _option(effective, "--durations-min")
    try:
        ok = n is not None and int(n) == PYTEST_DURATIONS
        ok2 = m is not None and float(m) == PYTEST_DURATIONS_MIN
    except ValueError:
        return f"has --durations={n} --durations-min={m}, which the guard cannot read"
    if ok and ok2:
        return None
    shown = f"--durations={n}" if n is not None else "no --durations"
    shown += f" --durations-min={m}" if m is not None else ", no --durations-min"
    return (f"effective pytest options have {shown}; need --durations={PYTEST_DURATIONS} "
            f"--durations-min={PYTEST_DURATIONS_MIN} (in addopts of the applying configuration or on the line)")


def _unittest(args):
    n = _option(args, "--durations")
    if n is not None and n.isdigit() and int(n) == UNITTEST_DURATIONS:
        return None
    return f"unittest has {'--durations ' + n if n is not None else 'no --durations'}; need --durations {UNITTEST_DURATIONS}"


def findings(root):
    """``file:line: `command`: reason`` for every test invocation of the workflows under ``root`` that misses the option."""
    root, out = Path(root), []
    for f in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        text = f.read_text()
        steps = _steps(text)
        for line, tokens in _segments(text):
            inv = _invocation(tokens)
            if not inv:
                continue
            wd = next((Path(s[2]) for s in steps if s[0] <= line <= s[1] and s[2]), None)
            if _is_defaults_wd(text):
                reason = "a job `defaults` working-directory applies; cannot be resolved"
            else:
                reason = _pytest(root, wd, tokens[inv[1]:]) if inv[0] == "pytest" else _unittest(tokens[inv[1]:])
            if reason:
                out.append(f"{f.name}:{line}: `{' '.join(tokens)[:110]}`: {reason}")
    return out


FLAGS = "--durations=25 --durations-min=1.0"


def _tree(files):
    d = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (d / name).parent.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text)
    return d


def _wf(run):
    return {".github/workflows/t.yml": f"jobs:\n  t:\n    steps:\n      - run: {run}\n"}


class TestDurationsPrinted(unittest.TestCase):
    def test_every_test_invocation_of_this_repository_prints_its_durations(self):
        self.assertEqual(findings(ROOT), [])

    def test_fixture_without_the_option_fails_naming_the_invocation(self):
        msg = findings(_tree({"pyproject.toml": '[tool.pytest.ini_options]\naddopts = "-v"\n', **_wf("pytest -q tests")}))
        self.assertEqual(len(msg), 1)
        self.assertIn("`pytest -q tests`: effective pytest options have no --durations", msg[0])
        print(msg[0])

    def test_fixture_with_the_central_option_passes_and_a_wrong_value_or_override_fails(self):
        cfg = {"pyproject.toml": f'[tool.pytest.ini_options]\naddopts = "{FLAGS}"\n'}
        self.assertEqual(findings(_tree({**cfg, **_wf("pytest -q tests")})), [])
        wrong = findings(_tree({**cfg, **_wf("pytest -q --durations=10 tests")}))
        self.assertEqual(len(wrong), 1)
        self.assertIn("--durations=10", wrong[0])
        print(wrong[0])
        override = findings(_tree({**cfg, **_wf('pytest -o addopts="-q" tests')}))
        self.assertEqual(len(override), 1)
        self.assertIn("no --durations", override[0])
        print(override[0])

    def test_fixture_unittest_without_durations_fails_and_with_it_passes(self):
        msg = findings(_tree(_wf("python -m unittest discover -s tools -v")))
        self.assertEqual(len(msg), 1)
        self.assertIn("unittest has no --durations; need --durations 25", msg[0])
        print(msg[0])
        self.assertEqual(findings(_tree(_wf("python -m unittest discover -s tools --durations 25 -v"))), [])


if __name__ == "__main__":
    unittest.main()
