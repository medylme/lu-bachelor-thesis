#include <benchmark/benchmark.h>
#include <fstream>
#include <stdexcept>
#include <string>

#include "compact_tree.h"

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

static void BM_tree(benchmark::State& state)
{
    const auto n = static_cast<std::size_t>(state.range(0));
    const auto newick = load_file("../../data/prepared/tree_" + std::to_string(n) + ".nwk");

    for (auto _ : state) {
        compact_tree tree(newick, /*is_fn=*/false);
        double total = 0.0;
        for (auto it = tree.postorder_begin(); it != tree.postorder_end(); ++it)
            total += static_cast<double>(tree.get_edge_length(*it));
        benchmark::DoNotOptimize(total);
    }
    state.SetItemsProcessed(static_cast<int64_t>(state.iterations()) *
                            static_cast<int64_t>(n));
}

BENCHMARK(BM_tree)->Arg(100)->Arg(1'000)->Arg(10'000)->Arg(100'000);

BENCHMARK_MAIN();
