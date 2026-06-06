// Source:  https://github.com/seqan/seqan3 (v3.4.2)
// License: BSD-3-Clause
// Adapted: SeqAn3 does not implement KMP; this file hand-rolls a generic
//          C++20 Knuth-Morris-Pratt search templated over ranges whose
//          value type models `seqan3::alphabet`. The SeqAn3 dependency is
//          pulled in for its alphabet/concept machinery (e.g. dna4/dna5
//          rank-encoded alphabets and the std::ranges integration), not
//          for any built-in pattern matcher.

#include <concepts>
#include <cstddef>
#include <ranges>
#include <vector>

#include <seqan3/alphabet/concept.hpp>

namespace thesis_kmp
{

/*!\brief Builds the KMP failure table for `pattern`.
 *
 * The failure table f has length `pattern.size()`. f[i] is the length of the
 * longest proper prefix of pattern[0..=i] that is also a suffix.
 */
template <std::ranges::random_access_range pattern_t>
    requires seqan3::semialphabet<std::ranges::range_value_t<pattern_t>>
[[nodiscard]] inline std::vector<std::size_t> build_failure_table(pattern_t const & pattern)
{
    auto const m = static_cast<std::size_t>(std::ranges::size(pattern));
    std::vector<std::size_t> failure(m, 0);

    if (m == 0)
        return failure;

    std::size_t k = 0;
    for (std::size_t i = 1; i < m; ++i)
    {
        while (k > 0 && pattern[k] != pattern[i])
            k = failure[k - 1];

        if (pattern[k] == pattern[i])
            ++k;

        failure[i] = k;
    }
    return failure;
}

/*!\brief Returns 0-based start positions of every occurrence of `pattern`
 *        in `text`.
 *
 * Both `pattern` and `text` must be random-access ranges over the same
 * alphabet type, and that alphabet must model `seqan3::semialphabet`. This
 * lets the function be instantiated for `seqan3::dna4`, `seqan3::dna5`,
 * `seqan3::aa27`, `char`, etc. without changing the algorithm.
 */
template <std::ranges::random_access_range pattern_t,
          std::ranges::random_access_range text_t>
    requires seqan3::semialphabet<std::ranges::range_value_t<pattern_t>>
          && std::same_as<std::ranges::range_value_t<pattern_t>,
                          std::ranges::range_value_t<text_t>>
[[nodiscard]] std::vector<std::size_t> kmp_search(pattern_t const & pattern, text_t const & text)
{
    auto const m = static_cast<std::size_t>(std::ranges::size(pattern));
    auto const n = static_cast<std::size_t>(std::ranges::size(text));

    std::vector<std::size_t> hits;
    if (m == 0 || n < m)
        return hits;

    auto const failure = build_failure_table(pattern);

    std::size_t q = 0;
    for (std::size_t i = 0; i < n; ++i)
    {
        while (q > 0 && pattern[q] != text[i])
            q = failure[q - 1];

        if (pattern[q] == text[i])
            ++q;

        if (q == m)
        {
            hits.push_back(i + 1 - m);
            q = failure[q - 1];
        }
    }
    return hits;
}

} // namespace thesis_kmp
