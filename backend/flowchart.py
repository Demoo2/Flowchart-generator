#!/usr/bin/env python3
"""Generate flowcharts (vývojové diagramy) from Python code.

Usage:
    python3 flowchart.py                     # every .py / .ipynb in current folder
    python3 flowchart.py subor.py graph.ipynb
    python3 flowchart.py --lang en --format svg

Output: flowcharts/<file>.<format> - one diagram per file. Each function is drawn
in a dashed frame; calls jump into it and its end jumps back to the caller.
From other code (web API): flowchart_bytes(code_text, filename) -> image bytes.
Needs: pip install graphviz  and the Graphviz program (brew install graphviz).
"""
import argparse
import ast
import html
import json
import sys
import textwrap
from pathlib import Path

import graphviz

TEXT = {
    "sk": dict(start="Začiatok", end="Koniec", ret="Návrat", call="volanie",
               yes="áno", no="nie", next="ďalší", done="hotovo"),
    "en": dict(start="Start", end="End", ret="Return", call="call",
               yes="yes", no="no", next="next", done="done"),
}

STYLE = {
    "terminal": dict(shape="box", style="rounded,filled", fillcolor="#e0e7ff"),
    "process": dict(shape="box", style="filled", fillcolor="#ffffff"),
    "io": dict(shape="parallelogram", style="filled", fillcolor="#dcfce7"),
    "decision": dict(shape="diamond", style="filled", fillcolor="#fef3c7"),
    "loop": dict(shape="hexagon", style="filled", fillcolor="#fce7f3"),
    "call": dict(shape="plain"),
    "join": dict(shape="point", width="0.08"),
}
CALL_EDGE = dict(style="dashed", color="#2563eb", fontcolor="#2563eb")
FRAME = dict(style="rounded,dashed", color="#94a3b8", margin="14")

SKIP = (ast.Pass, ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
        ast.ClassDef, ast.Global, ast.Nonlocal)
TRY = tuple(t for t in (getattr(ast, "Try", None), getattr(ast, "TryStar", None)) if t)
WIDTH = 50


def src(node):
    return ast.unparse(node)


def wrap(lines, width):
    out = []
    for line in lines:
        for part in line.splitlines() or [""]:
            out += textwrap.wrap(part, width) or [""]
    return out


def label(lines, left=True, width=WIDTH):
    """Label in dot string syntax; left=True aligns each line to the left."""
    esc = [l.replace("\\", "\\\\").replace('"', '\\"') for l in wrap(lines, width)]
    return "\\l".join(esc) + "\\l" if left else "\\n".join(esc)


def call_label(text):
    """Subroutine symbol: box with a vertical bar on each side."""
    br = '<BR ALIGN="LEFT"/>'
    body = br.join(html.escape(l) for l in wrap([text], WIDTH)) + br
    return (f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="#e0f2fe">'
            f'<TR><TD WIDTH="6"></TD><TD>{body}</TD><TD WIDTH="6"></TD></TR></TABLE>>')


def is_true(expr):
    return isinstance(expr, ast.Constant) and expr.value is True


class Diagram:
    def __init__(self, lang, fmt):
        self.t = TEXT[lang]
        self.g = graphviz.Digraph(format=fmt)
        self.g.attr(fontname="Helvetica", nodesep="0.35", ranksep="0.35", newrank="true")
        if fmt == "png":
            self.g.attr(dpi="150")
        self.g.attr("node", fontname="Helvetica", fontsize="11", margin="0.15,0.07")
        self.g.attr("edge", fontname="Helvetica", fontsize="10", arrowsize="0.7")
        self.cur = self.g     # graph (main or a function frame) that receives new nodes
        self.count = 0
        self.targets = {}     # id(def node) -> (start node, end node) of its chart
        self.funcs = {}       # function name -> (start, end) visible to calls
        self.methods = {}     # method name -> (start, end)
        self.calls = []       # (calling node, (start, end))
        self.loops = []       # (continue target, break exits) for each enclosing loop
        self.returns = []     # exits that jump straight to the end of the chart

    def chart(self, graph, title, body, end_label, start=None, end=None):
        self.cur, self.loops, self.returns = graph, [], []
        start = self.node("terminal", label([title], left=False), name=start)
        exits = self.block(body, [(start, None)])
        end = self.node("terminal", end_label, name=end)
        self.connect(exits + self.returns, end)

    def node(self, kind, text, name=None, source=None):
        if name is None:
            self.count += 1
            name = f"n{self.count}"
        self.cur.node(name, text, **STYLE[kind])
        if source is not None:
            self.calls += [(name, target) for target in self.called(source)]
        return name

    def called(self, *trees):
        """Charts of the user functions called anywhere inside trees."""
        found = []
        for tree in trees:
            for n in ast.walk(tree):
                if not isinstance(n, ast.Call):
                    continue
                if isinstance(n.func, ast.Name):
                    target = self.funcs.get(n.func.id)
                elif isinstance(n.func, ast.Attribute):
                    target = self.methods.get(n.func.attr)
                else:
                    target = None
                if target and target not in found:
                    found.append(target)
        return found

    def define(self, stmt):
        """A def/class seen while walking code makes its functions callable from here on."""
        if id(stmt) in self.targets:
            self.funcs[stmt.name] = self.targets[id(stmt)]
        elif isinstance(stmt, ast.ClassDef):
            for m in stmt.body:
                if id(m) in self.targets:
                    self.methods[m.name] = self.targets[id(m)]

    def connect(self, exits, target):
        if len(exits) > 1:  # branches meet in one point before continuing
            join = self.node("join", "")
            self.connect_all(exits, join, arrow=False)
            exits = [(join, None)]
        self.connect_all(exits, target)

    def connect_all(self, exits, target, arrow=True):
        for source, text in exits:
            attrs = {} if arrow else {"arrowhead": "none"}
            if text:
                attrs["label"] = f" {text} "
            self.cur.edge(source, target, **attrs)

    def kind(self, stmt):
        if isinstance(stmt, SKIP):
            return "skip"
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            return "skip"  # docstring / bare literal
        if not isinstance(stmt, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr, ast.Delete, ast.Assert)):
            return "compound"
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("print", "input")
               for n in ast.walk(stmt)):
            return "io"
        if self.called(stmt):
            return "call"
        return "process"

    def block(self, stmts, exits):
        batch = []  # consecutive plain statements share one box
        for stmt in stmts:
            if not exits:
                break  # code after break/continue/return is unreachable
            kind = self.kind(stmt)
            if kind == "skip":
                self.define(stmt)
                continue
            if kind == "process":
                batch.append(stmt)
                continue
            exits = self.statement(stmt, kind, self.flush(batch, exits))
            batch = []
        return self.flush(batch, exits)

    def flush(self, batch, exits):
        if not batch:
            return exits
        n = self.node("process", label([src(s) for s in batch]))
        self.connect(exits, n)
        return [(n, None)]

    def step(self, kind, text, exits, *source):
        n = self.node(kind, text)
        self.calls += [(n, target) for target in self.called(*source)]
        self.connect(exits, n)
        return n

    def statement(self, s, kind, exits):
        t = self.t
        if kind == "io":
            return [(self.step("io", label([src(s)], left=False), exits, s), None)]
        if kind == "call":
            return [(self.step("call", call_label(src(s)), exits, s), None)]

        if isinstance(s, ast.If):
            d = self.step("decision", label([src(s.test) + " ?"], left=False, width=24), exits, s.test)
            return self.block(s.body, [(d, t["yes"])]) + self.block(s.orelse, [(d, t["no"])])

        if isinstance(s, ast.While):
            d = self.step("decision", label([src(s.test) + " ?"], left=False, width=24), exits, s.test)
            return self.loop(s, d, t["yes"], t["no"], endless=is_true(s.test))

        if isinstance(s, (ast.For, ast.AsyncFor)):
            text = f"for {src(s.target)} in {src(s.iter)}"
            h = self.step("loop", label([text], left=False, width=30), exits, s.iter)
            return self.loop(s, h, t["next"], t["done"])

        if isinstance(s, ast.Return):
            if s.value is not None:
                exits = [(self.step("process", label([src(s)]), exits, s), None)]
            self.returns += exits
            return []

        if isinstance(s, ast.Break):
            if self.loops:
                self.loops[-1][1].extend(exits)
            return []

        if isinstance(s, ast.Continue):
            if self.loops:
                self.connect(exits, self.loops[-1][0])
            return []

        if TRY and isinstance(s, TRY):
            return self.block(s.body + s.orelse + s.finalbody, exits)

        if isinstance(s, (ast.With, ast.AsyncWith)):
            text = "with " + ", ".join(src(i) for i in s.items)
            n = self.step("process", label([text]), exits, *(i.context_expr for i in s.items))
            return self.block(s.body, [(n, None)])

        # anything else (match, raise, ...): show its first line
        return [(self.step("process", label([src(s).splitlines()[0]]), exits), None)]

    def loop(self, s, head, yes, no, endless=False):
        breaks = []
        self.loops.append((head, breaks))
        body_exits = self.block(s.body, [(head, yes)])
        self.loops.pop()
        self.connect(body_exits, head)
        after = [] if endless else self.block(s.orelse, [(head, no)])
        return after + breaks


def parse(code, notebook=False):
    """Text of a .py file, or JSON text of a .ipynb notebook -> one ast.Module."""
    if notebook:
        nb = json.loads(code)
        if not isinstance(nb, dict):
            raise ValueError("not a Jupyter notebook")
        body = []
        for i, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            code = "".join(cell.get("source", ""))
            code = "\n".join(l for l in code.splitlines() if not l.lstrip().startswith(("%", "!")))
            try:
                body += ast.parse(code).body
            except SyntaxError as e:
                print(f"  ! cell {i + 1} skipped: {e.msg}", file=sys.stderr)
        return ast.Module(body=body, type_ignores=[])
    return ast.parse(code)


def functions(tree):
    """(display name, def node, is method) for top-level functions and class methods."""
    found = []
    for s in tree.body:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append((s.name, s, False))
        elif isinstance(s, ast.ClassDef):
            found += [(f"{s.name}.{m.name}", m, True) for m in s.body
                      if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return found


def diagram(tree, lang="sk", fmt="png"):
    """Whole flowchart of one module as a graphviz.Digraph."""
    d = Diagram(lang, fmt)
    t = d.t

    defs = functions(tree)
    for i, (_, f, is_method) in enumerate(defs):
        d.targets[id(f)] = (f"f{i}_start", f"f{i}_end")
        # inside function bodies every function is callable (last definition wins)
        (d.methods if is_method else d.funcs)[f.name] = d.targets[id(f)]

    frames = []
    for i, (name, f, _) in enumerate(defs):
        frame = graphviz.Digraph(name=f"cluster_{i}")
        frame.attr(**FRAME)
        start, end = d.targets[id(f)]
        d.chart(frame, f"{name}({src(f.args)})", f.body, t["ret"], start, end)
        frames.append(frame)

    has_main = any(not isinstance(s, SKIP) for s in tree.body)
    if not defs and not has_main:
        raise ValueError("no code to draw")
    if has_main:
        # top-level code only sees functions defined above the call
        d.funcs, d.methods = {}, {}
        d.chart(d.g, t["start"], tree.body, t["end"])

    for frame in frames:
        d.g.subgraph(frame)
    for caller, (start, end) in d.calls:
        d.g.edge(caller, start, label=f" {t['call']} ", **CALL_EDGE)
        # drawn caller -> end but with the arrow reversed: layout stays top-down, lines stay short
        d.g.edge(caller, end, dir="back", tailport="e", **CALL_EDGE)
    return d.g


def flowchart_bytes(code, filename="code.py", lang="sk", fmt="png"):
    """Image of the flowchart for uploaded code, rendered in memory (for the web API)."""
    tree = parse(code, notebook=filename.endswith(".ipynb"))
    return diagram(tree, lang, fmt).pipe()


def process(path, out_dir, lang, fmt):
    tree = parse(path.read_text(encoding="utf-8"), notebook=path.suffix == ".ipynb")
    out_dir.mkdir(parents=True, exist_ok=True)
    print("  ->", diagram(tree, lang, fmt).render(outfile=str(out_dir / f"{path.stem}.{fmt}"), cleanup=True))


def main():
    p = argparse.ArgumentParser(description="Generate flowcharts from Python code.")
    p.add_argument("files", nargs="*", type=Path, help=".py / .ipynb files or folders (default: current folder)")
    p.add_argument("--lang", choices=TEXT, default="sk", help="label language (default: sk)")
    p.add_argument("--format", default="png", help="png, svg, pdf, ... (default: png)")
    p.add_argument("-o", "--out", type=Path, default=Path("flowcharts"), help="output folder")
    args = p.parse_args()

    me = Path(__file__).resolve()
    paths = []
    for item in args.files or [Path(".")]:
        if item.is_dir():
            paths += sorted(f for f in item.iterdir() if f.suffix in (".py", ".ipynb") and f.resolve() != me)
        else:
            paths.append(item)

    for path in paths:
        print(path)
        try:
            process(path, args.out, args.lang, args.format)
        except SyntaxError as e:
            print(f"  ! syntax error line {e.lineno}: {e.msg}", file=sys.stderr)
        except ValueError as e:
            print(f"  ! {e}", file=sys.stderr)
        except graphviz.ExecutableNotFound:
            sys.exit("Graphviz program not found. Install it: brew install graphviz")


if __name__ == "__main__":
    main()
