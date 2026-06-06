"""
prepare_data.py - this script generates prepared input data for the benchmarks

From raw data:
    ecoli_k12.fasta.gz   - E. coli K-12 MG1655 complete genome (NC_000913.3)
                           Downloaded from NCBI; the .gz extension is a
                           misnomer: the file is an uncompressed FASTA with a
                           spurious 20-byte gzip preamble prepended (a
                           Windows-download artefact). We skip the preamble
                           and read the FASTA directly.
    opentree16.1_tree.tgz - Open Tree of Life synthetic tree v16.1, grafted
                            solution (~159 925 tips). Downloaded from
                            https://files.opentreeoflife.org/synthesis/

Outputs:
    kmp_text.txt          1 000 000 bp  - E. coli positions 0-999 999
    kmp_pattern.txt              20 bp  - E. coli positions 500 000-500 019
    seq_pair_a.txt         5 000 bp    - E. coli positions 1 500 000-1 504 999
    seq_pair_b.txt         5 000 bp    - E. coli positions 3 000 000-3 004 999
    tree_100.nwk           100 tips    - pruned from OTT grafted solution
    tree_1000.nwk         1 000 tips   - pruned from OTT grafted solution
    tree_10000.nwk       10 000 tips   - pruned from OTT grafted solution
    tree_100000.nwk     100 000 tips   - pruned from OTT grafted solution
"""

from __future__ import annotations

import random
import sys
import tarfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = DATA_DIR / "prepared"

FASTA_GZ = DATA_DIR / "ecoli_k12.fasta.gz"
TREE_TGZ = DATA_DIR / "opentree16.1_tree.tgz"

TREE_MEMBER = "opentree16.1_tree/grafted_solution/grafted_solution.tre"

KMP_TEXT_START  = 0
KMP_TEXT_END    = 1_000_000
KMP_PAT_START   = 500_000
KMP_PAT_END     = 500_020
SEQ_A_START     = 1_500_000
SEQ_A_END       = 1_505_000
SEQ_B_START     = 3_000_000
SEQ_B_END       = 3_005_000

TREE_SIZES = [100, 1_000, 10_000, 100_000]
PRUNE_SEED = 42

# E. coli FASTA extraction
def load_ecoli_sequence() -> str:
    """
    Read the E. coli FASTA, skipping the empty 20-byte gzip preamble.
    """
    raw = FASTA_GZ.read_bytes()

    content = raw[20:]
    newline_pos = content.find(b"\n")
    if newline_pos == -1:
        raise ValueError("No newline found in FASTA content after preamble")

    seq_bytes = content[newline_pos + 1:]

    seq = seq_bytes.replace(b"\r", b"").replace(b"\n", b"").decode("ascii")
    print(f"  Loaded E. coli genome: {len(seq):,} bp", flush=True)
    return seq


def write_sequence_files(seq: str) -> None:
    kmp_text    = seq[KMP_TEXT_START:KMP_TEXT_END]
    kmp_pattern = seq[KMP_PAT_START:KMP_PAT_END]
    seq_a       = seq[SEQ_A_START:SEQ_A_END]
    seq_b       = seq[SEQ_B_START:SEQ_B_END]

    assert len(kmp_text)    == 1_000_000, f"kmp_text is {len(kmp_text)} bp"
    assert len(kmp_pattern) == 20,        f"kmp_pattern is {len(kmp_pattern)} bp"
    assert len(seq_a)       == 5_000,     f"seq_pair_a is {len(seq_a)} bp"
    assert len(seq_b)       == 5_000,     f"seq_pair_b is {len(seq_b)} bp"

    _write(OUT_DIR / "kmp_text.txt",    kmp_text)
    _write(OUT_DIR / "kmp_pattern.txt", kmp_pattern)
    _write(OUT_DIR / "seq_pair_a.txt",  seq_a)
    _write(OUT_DIR / "seq_pair_b.txt",  seq_b)
    print(f"  kmp_text.txt     {len(kmp_text):>9,} bp  (positions {KMP_TEXT_START}-{KMP_TEXT_END-1})")
    print(f"  kmp_pattern.txt  {len(kmp_pattern):>9,} bp  (positions {KMP_PAT_START}-{KMP_PAT_END-1})")
    print(f"  seq_pair_a.txt   {len(seq_a):>9,} bp  (positions {SEQ_A_START}-{SEQ_A_END-1})")
    print(f"  seq_pair_b.txt   {len(seq_b):>9,} bp  (positions {SEQ_B_START}-{SEQ_B_END-1})")


class Node:
    __slots__ = ["label", "length", "children"]

    def __init__(self, label: str = "", length: float | None = None,
                 children: list["Node"] | None = None) -> None:
        self.label = label
        self.length = length
        self.children: list[Node] = children if children is not None else []

    @property
    def is_leaf(self) -> bool:
        return not self.children


def _read_label(s: str, pos: int) -> tuple[str, int]:
    n = len(s)
    j = pos
    while j < n and s[j] not in "(),;:\n\r\t ":
        j += 1
    return s[pos:j], j


def _read_length(s: str, pos: int) -> tuple[float | None, int]:
    if pos < len(s) and s[pos] == ":":
        pos += 1
        j = pos
        while j < len(s) and s[j] not in "(),;\n\r\t ":
            j += 1
        try:
            return float(s[pos:j]), j
        except ValueError:
            return None, j
    return None, pos


def parse_newick(s: str) -> Node | None:
    """
    Iterative Newick parser.  Returns the root Node, or None if the string is empty.
    """
    pos = 0
    n = len(s)
    stack: list[list[Node]] = []
    root: Node | None = None

    while pos < n:
        c = s[pos]

        if c == "(":
            stack.append([])
            pos += 1

        elif c == ")":
            children = stack.pop()
            pos += 1
            label, pos = _read_label(s, pos)
            length, pos = _read_length(s, pos)
            node = Node(label=label, length=length, children=children)
            if stack:
                stack[-1].append(node)
            else:
                root = node

        elif c in ",;\n\r\t ":
            pos += 1

        else:
            label, pos = _read_label(s, pos)
            length, pos = _read_length(s, pos)
            node = Node(label=label, length=length, children=[])
            if stack:
                stack[-1].append(node)
            else:
                root = node  # bare-leaf tree

    return root


def collect_leaves(root: Node) -> list[Node]:
    """Return all leaf nodes in DFS order (iterative)."""
    leaves: list[Node] = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_leaf:
            leaves.append(node)
        else:
            for child in reversed(node.children):
                stack.append(child)
    return leaves


def prune_to_n_tips(root: Node, n_tips: int, seed: int = 42) -> Node | None:
    """
    Randomly select n_tips leaves and return a pruned copy of the tree containing 
    only those leaves and their ancestors. Internal nodes with a single surviving 
    child are collapsed (pass-through).
    """
    all_leaves = collect_leaves(root)
    if len(all_leaves) <= n_tips:
        return root

    rng = random.Random(seed)
    keep_ids = {id(leaf) for leaf in rng.sample(all_leaves, n_tips)}

    post_order: list[Node] = []
    stack2: list[tuple[Node, bool]] = [(root, False)]
    while stack2:
        node, visited = stack2.pop()
        if visited:
            post_order.append(node)
        else:
            stack2.append((node, True))
            for child in reversed(node.children):
                stack2.append((child, False))

    survives: dict[int, bool] = {}
    new_children: dict[int, list[Node]] = {}

    for node in post_order:
        nid = id(node)
        if node.is_leaf:
            survives[nid] = nid in keep_ids
        else:
            kept = [c for c in node.children if survives[id(c)]]
            survives[nid] = bool(kept)
            flat: list[Node] = []
            for c in kept:
                cid = id(c)
                if not c.is_leaf and len(new_children.get(cid, c.children)) == 1:
                    flat.extend(new_children.get(cid, c.children))
                else:
                    flat.append(c)
            new_children[nid] = flat

    if not survives.get(id(root), False):
        return None

    rebuild_stack: list[Node] = []
    visit_stack: list[tuple[Node, bool]] = [(root, False)]
    while visit_stack:
        node, visited = visit_stack.pop()
        if node.is_leaf:
            continue
        nid = id(node)
        nc = new_children.get(nid, [])
        if not visited:
            visit_stack.append((node, True))
            for child in nc:
                visit_stack.append((child, False))
        else:
            node.children = new_children.get(nid, [])

    return root


def serialize_newick(root: Node) -> str:
    """
    Convert a Node tree to a Newick string. Iterative to avoid recursion limits on large trees.
    """
    parts: list[str] = []
    stack: list[tuple[str, Node | str]] = [("node", root)]

    while stack:
        kind, item = stack.pop()
        if kind == "str":
            parts.append(item)  
        else:
            node: Node = item 
            if node.is_leaf:
                s = node.label
                if node.length is not None:
                    s += f":{node.length:.6g}"
                parts.append(s)
            else:
                suffix = node.label
                if node.length is not None:
                    suffix += f":{node.length:.6g}"
                stack.append(("str", ")" + suffix))
                for i, child in enumerate(reversed(node.children)):
                    stack.append(("node", child))
                    if i < len(node.children) - 1:
                        stack.append(("str", ","))
                stack.append(("str", "("))

    return "".join(parts) + ";"


def load_and_prune_trees() -> None:
    print(f"  Extracting {TREE_MEMBER} …", flush=True)
    with tarfile.open(TREE_TGZ, "r:gz") as tf:
        member = tf.getmember(TREE_MEMBER)
        fobj = tf.extractfile(member)
        if fobj is None:
            raise RuntimeError(f"Cannot extract {TREE_MEMBER}")
        newick_raw = fobj.read().decode("ascii").strip()

    print(f"  Newick string: {len(newick_raw):,} chars", flush=True)

    root0 = parse_newick(newick_raw)
    if root0 is None:
        raise RuntimeError("Newick parse returned None")
    print(f"  Full tree has {len(collect_leaves(root0)):,} tips", flush=True)
    del root0 

    for n_tips in TREE_SIZES:
        print(f"  Pruning to {n_tips:,} tips …", flush=True)
        root = parse_newick(newick_raw)
        assert root is not None
        pruned = prune_to_n_tips(root, n_tips, seed=PRUNE_SEED)
        if pruned is None:
            raise RuntimeError(f"Pruning to {n_tips} tips returned None")
        newick_out = serialize_newick(pruned)
        out_path = OUT_DIR / f"tree_{n_tips}.nwk"
        _write(out_path, newick_out)
        tip_check = newick_out.count(",") + 1
        print(f"    tree_{n_tips}.nwk  {len(newick_out):>10,} chars  ~{tip_check:,} tips")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="ascii")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("E. coli genome sequences")
    seq = load_ecoli_sequence()
    write_sequence_files(seq)

    print("\nPhylogenetic trees")
    load_and_prune_trees()

    print("\nFiles written to:", OUT_DIR)


if __name__ == "__main__":
    main()
