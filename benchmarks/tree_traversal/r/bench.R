# bench::mark (CRAN bench >= 1.1.4)
# runs traverse_newick() across four tree sizes, writes CSV to stdout.
# inputs: benchmarks/data/prepared/ - run prepare_data.py first.
# usage: Rscript bench.R > results/tree_traversal_r.csv

script_dir <- local({
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
  if (length(file_arg) > 0) {
    normalizePath(dirname(file_arg))
  } else if (!is.null(sys.frame(1)$ofile)) {
    dirname(normalizePath(sys.frame(1)$ofile))
  } else {
    getwd()
  }
})
source(file.path(script_dir, "traversal.R"))

data_dir <- normalizePath(file.path(script_dir, "..", "..", "data", "prepared"))

sizes <- c(100L, 1000L, 10000L, 100000L)

rows <- vector("list", length(sizes))

for (i in seq_along(sizes)) {
  n      <- sizes[[i]]
  newick <- readLines(file.path(data_dir, paste0("tree_", n, ".nwk")), warn = FALSE)

  result <- bench::mark(
    traverse_newick(newick),
    iterations = 20L,
    check = FALSE
  )

  rows[[i]] <- data.frame(
    algorithm       = "tree_traversal",
    language        = "r",
    n               = n,
    min_ns          = as.numeric(result$min)    * 1e9,
    median_ns       = as.numeric(result$median) * 1e9,
    itr_per_sec     = result$`itr/sec`,
    mem_alloc_bytes = as.numeric(result$mem_alloc),
    n_gc            = result$n_gc,
    stringsAsFactors = FALSE
  )
}

output <- do.call(rbind, rows)
write.csv(output, stdout(), row.names = FALSE)
