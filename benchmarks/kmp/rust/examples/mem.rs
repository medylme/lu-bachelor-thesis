// measures peak heap allocation of kmp_find_all at n=1_000_000.
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
    let text_full = std::fs::read(data_path("kmp_text.txt"))
        .expect("kmp_text.txt not found - run benchmarks/data/prepare_data.py first");
    let pattern = std::fs::read(data_path("kmp_pattern.txt"))
        .expect("kmp_pattern.txt not found - run benchmarks/data/prepare_data.py first");

    let _profiler = dhat::Profiler::builder().testing().build();

    black_box(kmp::kmp_find_all(black_box(&pattern), black_box(&text_full)));

    let stats = dhat::HeapStats::get();
    println!("{{\"peak_bytes\": {}}}", stats.max_bytes);
}
