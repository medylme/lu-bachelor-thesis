// measures peak heap allocation of kmp_search at n=1_000_000 dna4 symbols.
// build and run via cmake: ./build/mem

#include "../../common/cpp/mem_track.hpp"

#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <seqan3/alphabet/nucleotide/dna4.hpp>

#include "kmp.cpp"

static std::string load_file(const std::string& path)
{
    std::ifstream ifs(path, std::ios::binary);
    if (!ifs)
        throw std::runtime_error("Cannot open " + path +
            " - run benchmarks/data/prepare_data.py first");
    std::string s((std::istreambuf_iterator<char>(ifs)), {});
    while (!s.empty() && (s.back() == '\n' || s.back() == '\r'))
        s.pop_back();
    return s;
}

static std::vector<seqan3::dna4> to_dna4(const std::string& s)
{
    std::vector<seqan3::dna4> out(s.size());
    for (std::size_t i = 0; i < s.size(); ++i)
        out[i] = seqan3::assign_char_to(s[i], seqan3::dna4{});
    return out;
}

int main()
{
    const auto text    = to_dna4(load_file("../../data/prepared/kmp_text.txt"));
    const auto pattern = to_dna4(load_file("../../data/prepared/kmp_pattern.txt"));

    mem_track::reset();
    auto result = thesis_kmp::kmp_search(pattern, text);
    volatile std::size_t sink = result.size();
    (void)sink;
    const std::size_t peak = mem_track::peak_bytes();

    std::printf("{\"peak_bytes\": %zu}\n", peak);
    return 0;
}
