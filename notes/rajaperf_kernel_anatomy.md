# RAJAPerf — Anatomy of One Kernel (DAXPY example)

Every kernel is one C++ class deriving from `KernelBase`, split across files by
backend. Understanding DAXPY (`src/basic/DAXPY*`) teaches you all of them.

## The files
| File | Role |
|------|------|
| `DAXPY.hpp` | class declaration + the `DAXPY_BODY` macro (the actual math) + `run<Backend>Variant` decls |
| `DAXPY.cpp` | constructor (registers metadata), `setSize()`, `setUp()`, `updateChecksum()`, `tearDown()` |
| `DAXPY-Seq.cpp` | Base/Lambda/RAJA **Sequential** implementations |
| `DAXPY-OMP.cpp` | OpenMP implementations |
| `DAXPY-OMPTarget.cpp` | OpenMP target-offload implementations |
| `DAXPY-Cuda.cpp` | CUDA implementations |
| `DAXPY-Hip.cpp` | HIP implementations |
| `DAXPY-Sycl.cpp` | SYCL implementations |

## 1. The body macro (in `.hpp`)
The computation is written **once** as a macro so every backend runs identical math:
```cpp
#define DAXPY_BODY  \
  y[i] += a * x[i];
```

## 2. The constructor (`DAXPY.cpp`) — registers metadata
```cpp
DAXPY::DAXPY(const RunParams& params) : KernelBase(rajaperf::Basic_DAXPY, params) {
  setDefaultProblemSize(1000000);
  setDefaultReps(500);
  setSize(params.getTargetSize(getDefaultProblemSize()), params.getReps(getDefaultReps()));
  setComplexity(Complexity::N);
  setUsesFeature(Forall);      // which RAJA feature it exercises
  addVariantTunings();         // register available variants/tunings
}
```

## 3. `setSize()` — declares work & memory traffic (drives bandwidth/FLOP metrics)
```cpp
setItsPerRep(getActualProblemSize());
setBytesReadPerRep( sizeof(Real_type) * N );          // x
setBytesModifyWrittenPerRep( sizeof(Real_type) * N ); // y (read+write)
setFLOPsPerRep( 2 * N );                              // 1 mul + 1 add per element
```
These numbers are exactly what produce the "Mean Bandwidth" and "Mean flops"
columns in the output CSV.

## 4. setUp / updateChecksum / tearDown (lifecycle, per variant)
```cpp
void DAXPY::setUp(vid, tune) {           // allocate + init on the right memory space
  allocAndInitDataConst(m_y, N, 0.0, vid);
  allocAndInitData(m_x, N, vid);
  initData(m_a, vid);
}
void DAXPY::updateChecksum(vid, tune) { addToChecksum(m_y, N, vid); }
void DAXPY::tearDown(vid, tune)      { deallocData(m_x, vid); deallocData(m_y, vid); }
```

## 5. A backend variant (`DAXPY-Seq.cpp`) — the timed loop
```cpp
void DAXPY::runSeqVariant(VariantID vid) {
  const Index_type run_reps = getRunReps();
  const Index_type iend = getActualProblemSize();
  DAXPY_DATA_SETUP;

  auto daxpy_lam = [=](Index_type i){ DAXPY_BODY; };   // Lambda/RAJA reuse this

  switch (vid) {
    case Base_Seq:                                   // raw loop
      startTimer();
      for (irep=0; irep<run_reps; ++irep)
        for (i=0; i<iend; ++i) { DAXPY_BODY; }
      stopTimer();
      break;

    case Lambda_Seq:                                 // same body via lambda
      startTimer();
      for (irep...) for (i...) daxpy_lam(i);
      stopTimer();
      break;

    case RAJA_Seq:                                   // via RAJA::forall
      startTimer();
      for (irep...)
        RAJA::forall<RAJA::seq_exec>(res, RAJA::RangeSegment(0,iend), daxpy_lam);
      stopTimer();
      break;
  }
}
```
The **only difference** between the three cases is *how* the loop is expressed —
the math (`DAXPY_BODY`) is identical. That's the whole point of the suite: compare
Base vs Lambda vs RAJA overhead. OpenMP/CUDA/HIP/SYCL files follow the exact same
`switch(vid)` pattern with their respective RAJA execution policies.

## Mental model
```
DAXPY.hpp (BODY macro + class)
        │
        ├── DAXPY.cpp        → metadata, data lifecycle
        └── DAXPY-<Backend>  → one timed switch(vid) per backend
                               Base | Lambda | RAJA  (same body, different dispatch)
```
