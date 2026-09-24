# RAJAPerf — Glossary & Reading Path

## Reading path (fastest way to learn the codebase)
Read in this order — each step builds on the last:

1. `src/RAJAPerfSuiteDriver.cpp` — the 5-step `main()`. See the whole run in one screen.
2. `src/common/Executor.hpp` then `Executor.cpp` — `setupSuite → runSuite →
   outputRunData`. Focus on `runKernel()`.
3. `src/common/KernelBase.hpp` — the abstract interface every kernel implements
   (`setUp`, `run*Variant`, `updateChecksum`, `tearDown`, timers, checksums).
4. `src/common/RAJAPerfSuite.hpp` — the `KernelID`/`VariantID`/`GroupID`/`FeatureID`
   enums and the factory idea.
5. `src/common/RunParams.hpp`/`.cpp` — how CLI flags become run configuration.
6. One full kernel: `src/basic/DAXPY.hpp` → `DAXPY.cpp` → `DAXPY-Seq.cpp`.
   (See `rajaperf_kernel_anatomy.md`.)
7. A second, harder kernel to confirm the pattern: `src/apps/ENERGY*` or a
   `src/polybench/*` nested-loop kernel.
8. `src/common/DataUtils.*` and `OutputUtils.*` — data alloc/init and CSV writing.

## Glossary
- **Kernel** — a single benchmark (e.g. DAXPY). One `KernelBase` subclass.
- **Group** — a family of kernels: `basic`, `lcals`, `polybench`, `stream`,
  `apps`, `algorithm`, `comm`, and their `-kokkos` versions.
- **Variant** — an implementation style × backend, e.g. `RAJA_OpenMP`,
  `Base_CUDA`, `Lambda_Seq`. Enumerated in `VariantID`.
  - **Base** — raw hand-written loop (baseline).
  - **Lambda** — same body in a C++ lambda.
  - **RAJA** — body dispatched through RAJA (the thing being evaluated).
- **Tuning** — a variation of a variant (e.g. block size / execution policy).
  Selected with `--tunings`; a kernel may expose several via `addVariantTunings()`.
- **Feature** — a RAJA capability a kernel exercises (`Forall`, `Kernel`, `Launch`,
  `Reduction`, `Scan`, `Sort`, `Workgroup`, `Atomic`, `View`...). `FeatureID` enum.
- **Rep (repetition)** — the kernel is run many times in a timed loop for stable
  timing. `getRunReps()`, scaled by `--repfact`.
- **Pass** — the whole suite is executed `--npasses` times; results are averaged.
- **Problem size** — number of elements/iterations; `setDefaultProblemSize()`,
  overridden globally by `--size`/`--sizefact`/`--memory-*`.
- **Checksum** — a reduction of a kernel's output; used to verify every variant
  computes the same result (the `PASSED` column).
- **FOM (Figure of Merit)** — derived comparison metric (e.g. RAJA vs Base speedup)
  in `*-fom.csv`.
- **Complexity** — declared algorithmic complexity (e.g. `Complexity::N`) used in
  reporting.
- **BLT** — Build, Link, Test: the CMake macro layer (`blt/`) used to build.
- **TPL** — Third-Party Libraries (`tpl/`): RAJA, camp, Kokkos, Caliper.
- **Caliper** — optional performance-profiling integration (produces `.cali` traces).

## Key metadata setters (define what the CSV metrics mean)
| Setter | Meaning |
|--------|---------|
| `setDefaultProblemSize / setDefaultReps` | baseline work amount |
| `setBytesReadPerRep` | bytes read from memory per repetition |
| `setBytesWrittenPerRep / setBytesModifyWrittenPerRep` | bytes written / read-modify-written |
| `setFLOPsPerRep` | floating-point ops per repetition |
| `setItsPerRep` | loop iterations per repetition |
| `setUsesFeature` | which RAJA feature the kernel exercises |
| `setComplexity` | algorithmic complexity class |

These feed the **Mean Bandwidth** and **Mean flops** columns you analyzed —
`bandwidth = bytes/time`, `flops = FLOPs/time`.
