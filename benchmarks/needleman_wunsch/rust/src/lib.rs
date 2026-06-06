// Source: https://github.com/rust-bio/rust-bio (crate: bio, v3.0.0)
// License: MIT
// Adapted: thin idiomatic wrapper around
//          `bio::alignment::pairwise::Aligner::global` that exposes
//          Needleman-Wunsch global alignment as a callable function.

use bio::alignment::pairwise::Aligner;
use bio::alignment::Alignment;

pub const DEFAULT_MATCH: i32 = 1;
pub const DEFAULT_MISMATCH: i32 = -1;
pub const DEFAULT_GAP_OPEN: i32 = -5;
pub const DEFAULT_GAP_EXTEND: i32 = -1;

/// Performs Needleman-Wunsch global alignment of `x` against `y` and
/// returns the resulting [`Alignment`].
///
/// `gap_open` and `gap_extend` are negative integers by rust-bio convention.
pub fn nw_align(
    x: &[u8],
    y: &[u8],
    match_score: i32,
    mismatch_score: i32,
    gap_open: i32,
    gap_extend: i32,
) -> Alignment {
    let score = move |a: u8, b: u8| {
        if a == b {
            match_score
        } else {
            mismatch_score
        }
    };
    let mut aligner = Aligner::with_capacity(x.len(), y.len(), gap_open, gap_extend, score);
    aligner.global(x, y)
}

/// Convenience wrapper using the default scoring constants.
pub fn nw_align_default(x: &[u8], y: &[u8]) -> Alignment {
    nw_align(
        x,
        y,
        DEFAULT_MATCH,
        DEFAULT_MISMATCH,
        DEFAULT_GAP_OPEN,
        DEFAULT_GAP_EXTEND,
    )
}
