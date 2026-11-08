"""Minimal S-expression reader/writer for KiCad files."""
import re


class Q(str):
    """A quoted string atom."""


_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    stack, cur = [], []
    for m in _tok.finditer(text):
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Q(m.group(3).replace('\\"', '"').replace("\\\\", "\\")))
        elif m.group(4):
            cur.append(m.group(4))
    return cur[0]


def dump(node, indent=0):
    pad = "\t" * indent
    if not isinstance(node, list):
        if isinstance(node, Q):
            return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
        if isinstance(node, float):
            return f"{node:.4f}".rstrip("0").rstrip(".")
        return str(node)
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return pad + "(" + " ".join(dump(x) for x in node) + ")"
    out = pad + "(" + " ".join(dump(x) for x in node if not isinstance(x, list))
    for x in node:
        if isinstance(x, list):
            out += "\n" + dump(x, indent + 1)
    return out + "\n" + pad + ")"


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None
