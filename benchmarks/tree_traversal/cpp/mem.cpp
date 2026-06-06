// Measures peak heap allocation of compact_tree traversal at 100_000 tips.
// Prints: {"peak_bytes": <N>}

#include "../../common/cpp/mem_track.hpp"

#include <cstdio>
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

int main()
{
    const auto newick = load_file("../../data/prepared/tree_100000.nwk");

    mem_track::reset();

    compact_tree tree(newick, /*is_fn=*/false);
    double total = 0.0;
    for (auto it = tree.postorder_begin(); it != tree.postorder_end(); ++it)
        total += static_cast<double>(tree.get_edge_length(*it));

    if (total < 0) std::printf("(impossible)\n");

    const std::size_t peak = mem_track::peak_bytes();
    std::printf("{\"peak_bytes\": %zu}\n", peak);
    return 0;
}
