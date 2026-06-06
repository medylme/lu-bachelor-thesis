# Source:  https://github.com/Bioconductor/Biostrings (v2.78.0, Bioc 3.22)
#          https://github.com/Bioconductor/pwalign  (v1.6.0,  Bioc 3.22)
# License: Artistic-2.0
# Adapted: Needleman-Wunsch global alignment of two DNA strings using the
#          Bioconductor stack. `pairwiseAlignment` migrated from Biostrings
#          to the new `pwalign` package in Bioconductor 3.19; the call is
#          formally defunct in Biostrings as of 3.22, so we call
#          `pwalign::pairwiseAlignment` and rely on Biostrings only for the
#          DNAString sequence container.

#' Globally aligns two DNA strings via Needleman-Wunsch.
#'
#' @param seq1 character scalar; pattern sequence (will be coerced to
#'   `Biostrings::DNAString`).
#' @param seq2 character scalar; subject sequence.
#' @param match score for a base match. Default 1.
#' @param mismatch score for a base mismatch. Default -3.
#' @param gapOpening cost to open a gap (positive). Default 5.
#' @param gapExtension cost per gap extension (positive). Default 2.
#'
#' @return a `pwalign::PairwiseAlignmentsSingleSubject` S4 object. Use
#'   `pwalign::score()`, `pwalign::alignedPattern()`, `pwalign::alignedSubject()`
#'   to query the result.
needleman_wunsch <- function(seq1, seq2,
                             match = 1, mismatch = -3,
                             gapOpening = 5, gapExtension = 2) {
  stopifnot(
    is.character(seq1), length(seq1) == 1L,
    is.character(seq2), length(seq2) == 1L
  )

  pattern <- Biostrings::DNAString(seq1)
  subject <- Biostrings::DNAString(seq2)

  submat <- pwalign::nucleotideSubstitutionMatrix(
    match    = match,
    mismatch = mismatch,
    baseOnly = TRUE
  )

  pwalign::pairwiseAlignment(
    pattern            = pattern,
    subject            = subject,
    type               = "global",
    substitutionMatrix = submat,
    gapOpening         = gapOpening,
    gapExtension       = gapExtension
  )
}
