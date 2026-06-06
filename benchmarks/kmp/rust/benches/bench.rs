use std::hint::black_box;
use std::path::Path;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};
use kmp::kmp_find_all;

const TEXT_SIZES: &[usize] = &[1_000, 10_000, 100_000, 1_000_000];

fn data_path(file: &str) -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/prepared")
        .join(file)
}

fn bench_kmp(c: &mut Criterion) {
    let text_full = std::fs::read(data_path("kmp_text.txt"))
        .expect("kmp_text.txt not found - run benchmarks/data/prepare_data.py first");
    let pattern = std::fs::read(data_path("kmp_pattern.txt"))
        .expect("kmp_pattern.txt not found - run benchmarks/data/prepare_data.py first");

    let mut group = c.benchmark_group("kmp");

    for &n in TEXT_SIZES {
        let text = text_full[..n].to_vec();
        group.throughput(criterion::Throughput::Bytes(n as u64));
        group.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| black_box(kmp_find_all(black_box(&pattern), black_box(&text))))
        });
    }
    group.finish();
}

criterion_group!(benches, bench_kmp);
criterion_main!(benches);
