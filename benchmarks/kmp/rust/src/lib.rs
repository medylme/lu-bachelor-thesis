// Source: https://github.com/rust-bio/rust-bio (crate: bio, v3.0.0)
// License: MIT
// Adapted: thin idiomatic wrapper exposing rust-bio's
//          `bio::pattern_matching::kmp::KMP` as a callable function returning
//          all match start positions of `pattern` in `text`.

use bio::pattern_matching::kmp::KMP;

/// Returns 0-based starting positions of every occurrence of `pattern` in
/// `text`, in ascending order.
///
/// The KMP failure table is constructed from `pattern` on each call; if you
/// have many texts to search against the same pattern, prefer
/// [`kmp_for_pattern`] to amortise the construction cost.
pub fn kmp_find_all(pattern: &[u8], text: &[u8]) -> Vec<usize> {
    KMP::new(pattern).find_all(text).collect()
}

/// Builds a reusable KMP automaton from `pattern`. The returned closure
/// accepts a text and yields all match positions.
pub fn kmp_for_pattern(pattern: &[u8]) -> impl Fn(&[u8]) -> Vec<usize> + use<'_> {
    let kmp = KMP::new(pattern);
    move |text: &[u8]| kmp.find_all(text).collect()
}
