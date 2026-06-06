// Source:  https://github.com/niemasd/CompactTree
//          (main @ 80bdf87d98fb770e37d0298d2aa56d4782fe5081, 2025-03-09)
// License: GPL-3.0
//          NOTE: this is a copyleft license; binaries linking compact_tree.h
//          inherit GPL-3 obligations on redistribution.
// Adapted: parses a Newick string into a `compact_tree`, runs a postorder
//          traversal, and accumulates total node count and summed branch
//          length into a small struct returned to the caller.

#include <cstddef>
#include <string>

#include "compact_tree.h"

namespace thesis_tree
{

struct TreeStats
{
    std::size_t num_nodes;
    double      total_branch_length;
};

/*!\brief Parses a Newick string and returns aggregate traversal statistics.
 *
 * The second constructor argument `is_fn = false` tells CompactTree that the
 * input is a Newick literal, not a filename. Forgetting that flag causes
 * CompactTree to attempt to open the string as a file path.
 */
inline TreeStats traverse_newick(std::string const & newick)
{
    compact_tree tree(newick, /*is_fn=*/false);

    TreeStats stats{0, 0.0};
    for (auto it = tree.postorder_begin(); it != tree.postorder_end(); ++it)
    {
        CT_NODE_T const node = *it;
        stats.num_nodes += 1;
        stats.total_branch_length += static_cast<double>(tree.get_edge_length(node));
    }
    return stats;
}

} // namespace thesis_tree
