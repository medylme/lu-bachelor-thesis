// measures peak heap allocation of traverse_newick at n=100_000.
// prints {"peak_bytes": <N>} to stdout.

#[global_allocator]
static ALLOC: dhat::Alloc = dhat::Alloc;

use std::hint::black_box;
use std::path::Path;

fn data_path(file: &str) -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/prepared")
        .join(file)
}

fn main() {
    let newick = std::fs::read_to_string(data_path("tree_100000.nwk"))
        .expect("tree_100000.nwk not found - run benchmarks/data/prepare_data.py first");

    let _profiler = dhat::Profiler::builder().testing().build();

    black_box(tree_traversal::traverse_newick(black_box(&newick)));

    let stats = dhat::HeapStats::get();
    println!("{{\"peak_bytes\": {}}}", stats.max_bytes);
}
