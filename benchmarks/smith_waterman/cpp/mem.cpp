// Measures peak heap allocation of sw_align at the largest benchmark input
// size (5_000 bp). Prints a single JSON line to stdout.

#include "../../common/cpp/mem_track.hpp"

#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>

#include "sw.cpp"

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

int main()
{
    const auto query   = load_file("../../data/prepared/seq_pair_a.txt");
    const auto subject = load_file("../../data/prepared/seq_pair_b.txt");

    mem_track::reset();
    auto result = thesis_sw::sw_align(query, subject);
    volatile uint16_t sink = result.sw_score;
    (void)sink;
    const std::size_t peak = mem_track::peak_bytes();

    std::printf("{\"peak_bytes\": %zu}\n", peak);
    return 0;
}
