#include <benchmark/benchmark.h>
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

static std::vector<seqan3::dna4> to_dna4(const std::string& s, std::size_t n)
{
    std::vector<seqan3::dna4> out(n);
    for (std::size_t i = 0; i < n; ++i)
        out[i] = seqan3::assign_char_to(s[i], seqan3::dna4{});
    return out;
}

static void BM_kmp(benchmark::State& state)
{
    static const std::string text_full    = load_file("../../data/prepared/kmp_text.txt");
    static const std::string pattern_str  = load_file("../../data/prepared/kmp_pattern.txt");

    const auto n       = static_cast<std::size_t>(state.range(0));
    const auto text    = to_dna4(text_full, n);
    const auto pattern = to_dna4(pattern_str, pattern_str.size());

    for (auto _ : state)
        benchmark::DoNotOptimize(thesis_kmp::kmp_search(pattern, text));

    state.SetBytesProcessed(static_cast<int64_t>(state.iterations()) *
                            static_cast<int64_t>(n));
}

BENCHMARK(BM_kmp)->Arg(1'000)->Arg(10'000)->Arg(100'000)->Arg(1'000'000);

BENCHMARK_MAIN();
