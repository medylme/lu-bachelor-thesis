# bench::mark (CRAN bench >= 1.1.4)
# runs needleman_wunsch() across four sequence lengths, writes CSV to stdout.
# inputs: benchmarks/data/prepared/ - run prepare_data.py first.
# usage: Rscript bench.R > results/needleman_wunsch_r.csv

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
source(file.path(script_dir, "nw.R"))

data_dir <- normalizePath(file.path(script_dir, "..", "..", "data", "prepared"))

seq_a_full <- readLines(file.path(data_dir, "seq_pair_a.txt"), warn = FALSE)
seq_b_full <- readLines(file.path(data_dir, "seq_pair_b.txt"), warn = FALSE)

# Sequence sizes (bp). NW is O(n*m) so capped at 5000 bp for iterative runs.
sizes <- c(100L, 500L, 1000L, 5000L)

rows <- vector("list", length(sizes))

for (i in seq_along(sizes)) {
  n    <- sizes[[i]]
  seq1 <- substr(seq_a_full, 1L, n)
  seq2 <- substr(seq_b_full, 1L, n)

  result <- bench::mark(
    needleman_wunsch(seq1, seq2),
    iterations = 20L,
    check = FALSE
  )

  rows[[i]] <- data.frame(
    algorithm       = "needleman_wunsch",
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
