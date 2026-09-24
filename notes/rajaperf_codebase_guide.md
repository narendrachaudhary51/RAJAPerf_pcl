# RAJAPerf — Codebase Guide

A learning companion for the RAJA Performance Suite. Start here, then open the
diagrams (`.svg`/`.png`) and the other guides in this folder.

Files in this folder:
- `rajaperf_architecture.dot/.png/.svg` — high-level architecture graph
- `rajaperf_execution_flow.md` — step-by-step run sequence (with Mermaid diagram)
- `rajaperf_kernel_anatomy.md` — how ONE kernel is structured across backends
- `rajaperf_add_kernel_guide.md` — how to add a new kernel
- `rajaperf_glossary.md` — key terms & concepts
- `rajaperf_reading_path.md` — the order to read files to learn fastest

---

## 1. What RAJAPerf is
RAJAPerf is a **benchmark suite** that measures the performance of many compute
kernels, each written in several equivalent forms ("variants"):

- **Base** — hand-written raw C++ loop (baseline)
- **Lambda** — same loop body wrapped in a C++ lambda
- **RAJA** — the same body expressed through the RAJA portability abstraction

By comparing Base vs RAJA on the same hardware, you measure the *overhead* (or
lack of it) introduced by the RAJA abstraction across many backends (Sequential,
OpenMP, OpenMP-Target, CUDA, HIP, SYCL, Kokkos).

## 2. The big picture
```
main() ─▶ Executor ─▶ RunParams        (parse CLI)
                   └▶ RAJAPerfSuite     (which kernels/variants → factory)
                   └▶ KernelBase[]      (run each: setUp → run → checksum → tearDown)
                   └▶ Output CSVs       (timing, checksum, fom)
```
See `rajaperf_architecture.svg` for the full graph.

## 3. Directory map
| Path | Purpose |
|------|---------|
| `src/RAJAPerfSuiteDriver.cpp` | `main()` — 5-step run flow |
| `src/common/` | Framework core (Executor, KernelBase, RunParams, Suite enums, DataUtils) |
| `src/basic/` | Simple kernels (DAXPY, INIT3, MULADDSUB…) — best place to learn |
| `src/lcals/` | Livermore Compiler Analysis Loop Suite kernels |
| `src/polybench/` | Polyhedral benchmark kernels (nested loops) |
| `src/stream/` | STREAM-style memory-bandwidth kernels |
| `src/apps/` | Application-style / physics kernels (ENERGY, PRESSURE, VOL3D…) |
| `src/algorithm/` | Sort, scan, reduction algorithms |
| `src/comm/` | MPI communication kernels |
| `src/*-kokkos/` | Kokkos re-implementations of the above groups |
| `tpl/`, `blt/` | Third-party libs (RAJA, camp, Kokkos, Caliper) and the BLT/CMake build system |
| `docs/` | Upstream Sphinx documentation |

## 4. Two enums that drive everything
Defined in `src/common/RAJAPerfSuite.hpp`:
- **KernelID** — one entry per kernel (e.g. `Basic_DAXPY`). Must stay 1:1 with the
  `KernelNames[]` string array in `RAJAPerfSuite.cpp`.
- **VariantID** — Base/Lambda/RAJA × {Seq, OpenMP, OpenMPTarget, CUDA, HIP, SYCL} +
  `Kokkos_Lambda`.

A factory (`getKernelObject()`) turns a `KernelID` into the concrete kernel object.

## 5. How to run it (quick reference)
```bash
# List everything the build supports
./bin/raja-perf.exe --help

# Dry run: print what WOULD run, then exit
./bin/raja-perf.exe --dryrun

# Run selected kernels + variants at a chosen size
./bin/raja-perf.exe --kernels DAXPY ENERGY --variants RAJA_OpenMP --size 1000000 \
                    --outdir results --outfile mydata
```
Key flags (all **global to the run** — see `RunParams.cpp`):
`--kernels/-k`, `--variants/-v`, `--tunings`, `--size`, `--sizefact`,
`--min-size`, `--memory-*`, `--npasses`, `--repfact`, `--outdir/-od`, `--outfile/-of`.

> Note: `--size` applies to *every* kernel in a run; there is no per-kernel size
> in a single invocation (that requires the wrapper approach discussed earlier).

## 6. Output files
`outputRunData()` (in `Executor.cpp`) writes:
- `*-timing.csv` — mean time/rep, bandwidth, FLOP rate (this is the file you charted)
- `*-checksum.csv` — per-variant checksums for correctness verification
- `*-fom.csv` — Figure-of-Merit comparisons (e.g., RAJA vs Base speedups)
- Optional Caliper `.cali` traces if built with Caliper.
