Please implement this in Rust (stable, 2021 edition or later). The project must be a standard Cargo project, buildable and runnable as:

```
cargo build --release
cargo run --release -- <arguments>
```

Use only the Rust standard library — do not declare any external dependencies in `Cargo.toml`. The `[dependencies]` table must remain empty.

Place all project files in the `output/` directory relative to your current working directory. `output/Cargo.toml` must be the package manifest, and the binary entry point must live under `output/src/` (e.g. `output/src/main.rs`). The harness builds your program with `cargo build --release --manifest-path output/Cargo.toml` and then invokes the compiled release binary with `<arguments>`.
