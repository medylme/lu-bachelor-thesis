use std::hint::black_box;
use std::path::Path;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};
use needleman_wunsch::nw_align_default;

const SEQ_SIZES: &[usize] = &[100, 500, 1_000, 5_000];

fn data_path(file: &str) -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/prepared")
        .join(file)
}

fn bench_nw(c: &mut Criterion) {
    let seq_a_full = std::fs::read(data_path("seq_pair_a.txt"))
        .expect("seq_pair_a.txt not found - run benchmarks/data/prepare_data.py first");
    let seq_b_full = std::fs::read(data_path("seq_pair_b.txt"))
        .expect("seq_pair_b.txt not found - run benchmarks/data/prepare_data.py first");

    let mut group = c.benchmark_group("needleman_wunsch");

    for &n in SEQ_SIZES {
        let x = seq_a_full[..n].to_vec();
        let y = seq_b_full[..n].to_vec();
        group.throughput(criterion::Throughput::Bytes((n * 2) as u64));
        group.bench_with_input(BenchmarkId::from_parameter(n), &n, |b, _| {
            b.iter(|| black_box(nw_align_default(black_box(&x), black_box(&y))))
        });
    }
    group.finish();
}

criterion_group!(benches, bench_nw);
criterion_main!(benches);
