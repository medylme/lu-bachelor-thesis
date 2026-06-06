// Source: https://github.com/sriram98v/phylo-rs (crate: phylo, v2.0.1)
//   (Note: the repository URL `sriramlab/phylo-rs` quoted in some references
//   does not exist; the canonical repo is sriram98v/phylo-rs. See:
//   Vijendran et al. 2025, "Phylo-rs: an extensible phylogenetic analysis
//   library in Rust", BMC Bioinformatics 26:197.)
// License: MIT
// Adapted: parses a Newick string, runs a postorder traversal accumulating
//          node count and total branch length, exposed as a callable
//          function for the benchmark harness.

use phylo::prelude::*;

/// Parses `newick` and returns `(node_count, total_branch_length)` after a
/// postorder traversal from the root.
///
/// Branch lengths are summed as `f32` because that is the on-tree weight
/// type used by the `phylo` crate; cast at the call site if `f64` precision
/// is required.
pub fn traverse_newick(newick: &str) -> (usize, f32) {
    let tree = PhyloTree::from_newick(newick.as_bytes()).expect("invalid Newick input");
    let root = tree.get_root_id();

    let mut node_count: usize = 0;
    let mut total_branch_length: f32 = 0.0;

    // `postord_nodes` yields `&Node` directly, avoiding a per-iteration
    // `get_node(id)` lookup. Note: upstream phylo 2.0.1 has an O(n^2)
    // `SimpleRootedTree::next_id` that dominates `from_newick` on large
    // inputs and inflates the n=100_000 row by ~700x relative to the
    // C++ (CompactTree) baseline.
    for node in tree.postord_nodes(root) {
        node_count += 1;
        total_branch_length += node.get_weight().unwrap_or(0.0);
    }

    (node_count, total_branch_length)
}
