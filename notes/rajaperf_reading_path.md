# RAJAPerf — Codebase Reading Path

The fastest order to read files and *understand* the RAJA Performance Suite.
Follow the tiers top-to-bottom. Each tier builds on the previous one. Line numbers
are approximate anchors (verified against the current checkout) to help you jump in.

---

## Tier 0 — Orientation (10 min, no code)
Get the mental model before opening source.
1. `README.md` (repo root) — what the suite is and how to build/run it.
2. `notes/rajaperf_codebase_guide.md` — directory map + big-picture diagram.
3. `notes/rajaperf_architecture.svg` — look at the architecture graph once.

**Goal:** know that the flow is `main → Executor → (RunParams, Suite, KernelBase[]) → CSV`.

---

## Tier 1 — The run flow (the spine of the program)
Read these in order; this is 80% of understanding *how it executes*.

1. `src/RAJAPerfSuiteDriver.cpp` — the entire `main()`. Five calls:
   `Executor(argc,argv) → setupSuite() → reportRunSummary() → runSuite() → outputRunData()`.
2. `src/common/Executor.hpp` — the public API you just saw called.
3. `src/common/Executor.cpp` — read these functions in this order:
   - `setupSuite()`            (~line 370) — turns CLI selections into a kernel list.
   - `runSuite()`              (~line 985) — the outer loop over kernels.
   - `runKernel()`             (~line 1012) — **the heart**: setUp → run → checksum → tearDown.
   - `outputRunData()`         (~line 1212) — writes the CSV reports.

**Goal:** you can trace one kernel from selection to timed execution to CSV row.
**Companion:** `notes/rajaperf_execution_flow.md` (sequence diagram).

---

## Tier 2 — The core abstraction (what every kernel must provide)
1. `src/common/KernelBase.hpp` (~830 lines) — skim, don't read every line. Focus on:
   - the pure virtuals: `setUp()`, `updateChecksum()`, `tearDown()` (~line 635).
   - the timer helpers: `startTimer()` / `stopTimer()` (~line 604).
   - the metadata setters: `setBytes*PerRep`, `setFLOPsPerRep`, `setItsPerRep`,
     `setActualProblemSize`, `setUsesFeature`.
2. `src/common/KernelBase.cpp` — how timing and checksums are actually recorded.

**Goal:** understand the contract every kernel fulfills and where bandwidth/FLOP
numbers originate.

---

## Tier 3 — Configuration & the kernel registry
1. `src/common/RAJAPerfSuite.hpp` — the enums that name everything:
   - `KernelID` (~line 76, e.g. `Basic_DAXPY`), `VariantID` (~line 238),
     `GroupID`, `FeatureID`.
2. `src/common/RAJAPerfSuite.cpp` — the `KernelNames[]` array (must match `KernelID`
   1:1) and the **factory** `getKernelObject()` that maps an id → a `new Kernel`.
3. `src/common/RunParams.hpp` then `RunParams.cpp` — how CLI flags become config.
   Look at `--kernels`, `--variants`, `--tunings`, and the `--size` / `size_meaning`
   logic (~lines 463–530). This explains why `--size` is global to a run.

**Goal:** know how "which kernels/variants at what size" is decided.

---

## Tier 4 — One real kernel, end to end
Read a *whole* kernel now that you know the framework. Start simple:
1. `src/basic/DAXPY.hpp` — the `DAXPY_BODY` macro (the math) + class declaration.
2. `src/basic/DAXPY.cpp` — constructor (registers size/reps/features), `setSize()`
   (declares bytes & FLOPs per rep), `setUp/updateChecksum/tearDown`.
3. `src/basic/DAXPY-Seq.cpp` — the timed `switch(vid)` with Base / Lambda / RAJA.
4. Then skim `DAXPY-OMP.cpp` and `DAXPY-Cuda.cpp` — same pattern, different backend
   and RAJA execution policy.

**Goal:** you can now open any kernel and know exactly what each file does.
**Companion:** `notes/rajaperf_kernel_anatomy.md`.

---

## Tier 5 — Widen to harder patterns
Confirm the pattern generalizes:
1. `src/apps/ENERGY*` — a multi-array physics kernel (6 kernels/rep).
2. A `src/polybench/*` kernel — nested loops using RAJA `Kernel`/`Launch` (not just `Forall`).
3. `src/algorithm/*` — reductions / scans / sorts (the `Reduction`, `Scan`, `Sort` features).
4. `src/comm/*` — MPI halo-exchange kernels (only built with MPI).

**Goal:** understand how `Forall` vs `Kernel` vs `Launch` and reductions differ.

---

## Tier 6 — Support machinery (read as needed)
- `src/common/DataUtils.{hpp,cpp}` — `allocAndInitData`, `deallocData`, checksums.
- `src/common/OutputUtils.{hpp,cpp}` — CSV writing helpers.
- `src/common/*DataUtils.hpp` (Cuda/Hip/Sycl/OpenMPTarget) — device memory helpers.
- `src/common/GPUUtils.hpp`, `CudaGridScan.hpp`, `HipGridScan.hpp` — GPU launch utils.
- `CMakeLists.txt` + `src/*/CMakeLists.txt` + `blt/` — how it all builds.

---

## Suggested schedule
| Session | Tiers | Outcome |
|---------|-------|---------|
| Day 1   | 0–1   | Trace a run from `main` to CSV |
| Day 2   | 2–3   | Understand KernelBase + how kernels are selected |
| Day 3   | 4     | Read DAXPY end-to-end; run it yourself |
| Day 4   | 5–6   | Generalize to GPU/nested/MPI kernels + build system |

## Tips while reading
- Keep `notes/rajaperf_glossary.md` open for terms (variant, tuning, rep, pass, FOM).
- Build once early (`my-build/`) and run `./bin/raja-perf.exe --dryrun` and
  `--kernels DAXPY --variants RAJA_Seq --size 100000` so you can match code to output.
- The suite is **deliberately repetitive** — once one kernel clicks, the other ~70
  follow the same shape. Don't try to read them all.
