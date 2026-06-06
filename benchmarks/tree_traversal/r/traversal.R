# Source:  https://github.com/emmanuelparadis/ape (CRAN v5.8-1, 2024-12-16)
# License: GPL-2 | GPL-3 (dual)
#          NOTE: this is a copyleft license; redistribution of code that
#          attaches `ape` inherits GPL terms.
# Adapted: parses a Newick string with `ape::read.tree`, runs a postorder
#          traversal over the `phylo$edge` matrix using the indices returned
#          by `ape::postorder`, and returns aggregate statistics.

#' Traverse a Newick-encoded phylogeny in postorder and return basic stats.
#'
#' @param newick character scalar containing a Newick-encoded tree.
#'
#' @return a named list with components
#'   \describe{
#'     \item{n_tips}{number of leaf tips, from `ape::Ntip`.}
#'     \item{n_internal_nodes}{number of internal nodes, from `ape::Nnode`.}
#'     \item{n_edges}{number of edges visited (== `nrow(tree$edge)`).}
#'     \item{total_branch_length}{sum of `tree$edge.length` over the
#'       postorder traversal.}
#'   }
traverse_newick <- function(newick) {
  stopifnot(is.character(newick), length(newick) == 1L)

  tree <- ape::read.tree(text = newick)

  total_bl   <- 0
  edge_count <- 0L
  for (i in ape::postorder(tree)) {
    total_bl   <- total_bl + tree$edge.length[i]
    edge_count <- edge_count + 1L
  }

  list(
    n_tips              = ape::Ntip(tree),
    n_internal_nodes    = ape::Nnode(tree),
    n_edges             = edge_count,
    total_branch_length = total_bl
  )
}
