# RAJAPerf — Adding a New Kernel (checklist)

Use an existing simple kernel (e.g. `src/basic/DAXPY`) as your template. The suite
is intentionally repetitive, so "copy DAXPY, rename, edit the body" gets you 90%
of the way.

## Steps
1. **Register the KernelID** in `src/common/RAJAPerfSuite.hpp`
   - Add `Basic_MYKERNEL` (or `<Group>_MYKERNEL`) to the `KernelID` enum.
   - Add the matching string to `KernelNames[]` in `src/common/RAJAPerfSuite.cpp`
     — the enum and array **must** stay 1:1 and in the same order.
   - In the factory (`getKernelObject()` in `RAJAPerfSuite.cpp`) add a `case`
     that returns `new MYKERNEL(run_params)`.

2. **Create the kernel files** in the group directory (e.g. `src/basic/`):
   - `MYKERNEL.hpp` — define a `MYKERNEL_BODY` macro (the math), declare the class
     `class MYKERNEL : public KernelBase`, and declare each `run<Backend>Variant`.
   - `MYKERNEL.cpp` — constructor (set default size/reps, features, tunings),
     `setSize()` (declare bytes read/written + FLOPs per rep), `setUp()`,
     `updateChecksum()`, `tearDown()`.
   - `MYKERNEL-Seq.cpp`, `-OMP.cpp`, `-OMPTarget.cpp`, `-Cuda.cpp`, `-Hip.cpp`,
     `-Sycl.cpp` — one `switch(vid)` per backend (Base/Lambda/RAJA).

3. **Add the files to the build**: edit the group's `CMakeLists.txt`
   (e.g. `src/basic/CMakeLists.txt`) to list your new `.cpp` files.

4. **Declare metadata correctly** (this is what makes the metrics meaningful):
   - `setBytesReadPerRep / setBytesWrittenPerRep / setBytesModifyWrittenPerRep`
   - `setFLOPsPerRep`
   - `setComplexity(...)`, `setItsPerRep(...)`, `setUsesFeature(...)`

5. **Build & verify**:
   ```bash
   cd my-build && make -j        # or your build dir
   ./bin/raja-perf.exe --kernels MYKERNEL --dryrun     # confirm it registers
   ./bin/raja-perf.exe --kernels MYKERNEL --variants RAJA_Seq --size 100000
   ```
   Check that all variants report the **same checksum** (PASSED) — that proves
   your Base/Lambda/RAJA implementations are equivalent.

## Gotchas
- The enum ↔ names array ↔ factory case must all agree. A mismatch causes wrong
  kernels to run or a crash at startup.
- Every backend `switch(vid)` needs a `default` that prints "Unknown variant id".
- Guard backend code with the correct macros (`RUN_RAJA_SEQ`, `RAJA_ENABLE_CUDA`,
  etc.) so it compiles even when that backend is disabled.
- Bytes/FLOPs per rep must reflect the *real* traffic or your bandwidth/efficiency
  numbers (and your CSV analysis) will be wrong.
