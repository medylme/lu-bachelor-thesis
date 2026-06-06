use std::hint::black_box;
use std::path::Path;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};
use tree_traversal::traverse_newick;

const TIP_COUNTS: &[usize] = &[100, 1_000, 10_000, 100_000];

fn data_path(file: &str) -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/prepared")
        .join(file)
}

fn bench_tree(c: &mut Criterion) {
    let mut group = c.benchmark_group("tree_traversal");

    for &n in TIP_COUNTS {
        let newick =
            std::fs::read_to_string(data_path(&format!("tree_{n}.nwk"))).unwrap_or_else(|_| {
                panic!("tree_{n}.nwk not found - run benchmarks/data/prepare_data.py first")
            });
        group.throughput(criterion::Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| black_box(traverse_newick(black_box(&newick))))
        });
    }
    group.finish();
}

criterion_group!(benches, bench_tree);
criterion_main!(benches);
