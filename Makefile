RUST_CRATES := \
	benchmarks/kmp/rust \
	benchmarks/smith_waterman/rust \
	benchmarks/needleman_wunsch/rust \
	benchmarks/tree_traversal/rust

CPP_DIRS := \
	benchmarks/kmp/cpp \
	benchmarks/smith_waterman/cpp \
	benchmarks/tree_traversal/cpp

.PHONY: all build build-rust build-cpp bench clean

all: build bench

build: build-rust build-cpp

build-rust:
	@for dir in $(RUST_CRATES); do \
		echo "==> cargo build --release  $$dir"; \
		cargo build --release --manifest-path $$dir/Cargo.toml || exit 1; \
	done

build-cpp:
	@for dir in $(CPP_DIRS); do \
		echo "==> cmake  $$dir"; \
		cmake -S $$dir -B $$dir/build -DCMAKE_BUILD_TYPE=Release -Wno-dev --log-level=WARNING || exit 1; \
		cmake --build $$dir/build --parallel || exit 1; \
	done

bench:
	python -m orchestrator.run_benchmarks

bench-rust:
	python -m orchestrator.run_benchmarks --rust-only

bench-cpp:
	python -m orchestrator.run_benchmarks --cpp-only

bench-r:
	python -m orchestrator.run_benchmarks --r-only

bench-mem:
	python -m orchestrator.run_benchmarks --mem-only

clean:
	@for dir in $(RUST_CRATES); do \
		echo "==> cargo clean  $$dir"; \
		cargo clean --manifest-path $$dir/Cargo.toml; \
	done
	@for dir in $(CPP_DIRS); do \
		echo "==> rm  $$dir/build"; \
		rm -rf $$dir/build; \
	done
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name 'dhat-heap.json' -delete 2>/dev/null || true

clean-results:
	rm -rf results/
