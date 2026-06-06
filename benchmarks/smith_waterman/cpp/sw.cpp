// Source:  https://github.com/mengyao/Complete-Striped-Smith-Waterman-Library
//          (master @ a66636b79ef36ac178122437053be0d8ef345271, post-v1.2.5)
// License: MIT
// Adapted: thin C++ wrapper around SSW's StripedSmithWaterman::Aligner that
//          performs a single Smith-Waterman local alignment of `query`
//          against `ref` and returns the resulting Alignment struct.

#include <algorithm>
#include <cstdint>
#include <string>

#include "ssw_cpp.h"

namespace thesis_sw
{

inline constexpr std::uint8_t DEFAULT_MATCH        = 2;
inline constexpr std::uint8_t DEFAULT_MISMATCH     = 2;
inline constexpr std::uint8_t DEFAULT_GAP_OPEN     = 3;
inline constexpr std::uint8_t DEFAULT_GAP_EXTEND   = 1;

/*!\brief Aligns `query` against `ref` and returns SSW's Alignment struct.
 *
 * Score parameters are SSW penalty magnitudes (uint8_t); SSW negates them
 * internally where appropriate. The Filter is left at SSW's defaults, which
 * already request begin position and CIGAR. `maskLen` is set per the SSW
 * upstream example to `max(query.size() / 2, 15)`; values below 15 silently
 * disable suboptimal-alignment fields.
 */
inline StripedSmithWaterman::Alignment sw_align(std::string const & query,
                                                std::string const & ref,
                                                std::uint8_t match_score   = DEFAULT_MATCH,
                                                std::uint8_t mismatch_pen  = DEFAULT_MISMATCH,
                                                std::uint8_t gap_open_pen  = DEFAULT_GAP_OPEN,
                                                std::uint8_t gap_extend_pen = DEFAULT_GAP_EXTEND)
{
    StripedSmithWaterman::Aligner   aligner(match_score, mismatch_pen, gap_open_pen, gap_extend_pen);
    StripedSmithWaterman::Filter    filter;
    StripedSmithWaterman::Alignment result;

    std::int32_t const mask_len = static_cast<std::int32_t>(
        std::max<std::size_t>(query.size() / 2, 15));

    aligner.Align(query.c_str(), query.size(),
                  ref.c_str(),   ref.size(),
                  filter, result, mask_len);
    return result;
}

} // namespace thesis_sw
