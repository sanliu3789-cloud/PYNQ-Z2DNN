# Zhinao Xiandao — PYNQ-Z2 stroke-severity edge terminal

**A research prototype that runs a 62-input clinical DNN on a PYNQ-Z2 (Zynq-7020), with a low-rank fixed-point HLS kernel, approximate Shapley attribution and a touch-screen UI.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Board](https://img.shields.io/badge/board-PYNQ--Z2-orange)](docs/02_hardware.md)
[![Toolchain](https://img.shields.io/badge/Vivado%20%2F%20HLS-2018.3-lightgrey)](docs/05_reproduction.md)
[![Project](https://img.shields.io/badge/project-FPGA%20competition-teal)](docs/04_results.md)

> Designed for competition and research demonstrations, with implemented features, hardware designs and measured results documented below. Every performance figure includes its measurement scope.

---

## What it does

Given 62 clinical features (age, blood pressure, glucose, platelets, NIHSS items, ...), the system predicts the **24-hour change in NIHSS (ΔNIHSS)** and attributes it to the 62 features with an approximate Shapley explainer.

Three interchangeable backends share one input contract:

| Backend | Implementation | Purpose |
|---|---|---|
| PC preview | NumPy (`host/preview.py`) | Development without hardware |
| ARM | Cortex-A9, single-threaded BLAS | On-board functional baseline |
| FPGA | HLS fixed-point kernel, AXI-Lite, on-chip resident weights | Acceleration study |

The network (62-500-500-500-1, 533,001 parameters) is factorised to 62-500-**4**-500-**64**-500-1, cutting MACs from 531,500 to 99,500, then quantised to 16-bit weights with wider input/accumulator formats.

### Functional architecture

The touch application uses ARM inference. The FPGA kernel and camera have separate hardware verification paths; OCR runs locally on Windows.

```mermaid
flowchart TB
    subgraph Terminal[On-board touch application]
        Screen[7-inch HDMI touch screen] <--> Web[Local web UI and 62-feature validation]
        Web --> ARM[ARM NumPy prediction and Shapley attribution]
        ARM --> Result[Prediction and feature contributions]
    end
    subgraph Accelerator[FPGA accelerator · separate board tests]
        Input[62-feature input] --> DNN[Low-rank 4/64 fixed-point HLS kernel]
        DNN --> Timing[1.42–1.58 ms PS end-to-end]
    end
    subgraph Capture[Single-frame camera capture]
        Camera[OV5640] --> DVP[PL DVP capture]
        DVP --> Frame[320×240 image readback]
    end
    subgraph Intake[Windows OCR application]
        Picture[Image upload] --> OCR[OCR and field extraction]
        OCR --> Review[Human review and form filling]
    end
```

---

## Project achievements

| Deliverable | Implementation and verification |
|---|---|
| Input validation, prediction and approximate Shapley | Shared 62-feature contract across three backends; 4 paths, 252 evaluations and additivity checks |
| Board web UI and touch terminal | Touch interaction, numeric keyboard, result display and boot autostart verified |
| Low-rank fixed-point HLS kernel | 3 board tests, **1.42–1.58 ms** PS end-to-end |
| Batch 1–8 kernel | C/RTL co-simulation and 100 MHz place-and-route verification completed |
| OV5640 single-frame capture | Chip ID `0x5640` read and **320×240** frame captured |
| On-board photo and sample demonstration | Photo capture and display, fixed synthetic 62-feature sample loading, prediction and attribution |
| OCR and form filling | Windows-local OCR, field extraction, human review and form filling verified |

**Performance result:** the original float FPGA core measured 140.32 ms per sample; the new fixed-point core measured 1.42–1.58 ms. The change combines low-rank approximation, quantisation and hardware architecture improvements. Numerical errors and test conditions are reported separately.

---

## Results

| Item | Value | Scope |
|---|---:|---|
| Low-rank 4/64 vs original | max 0.0086 ΔNIHSS | 32 synthetic probes, FP32 |
| Fixed-point vs same low-rank FP32 | max 0.00074 ΔNIHSS | same probes |
| New kernel on board | 1.42–1.58 ms | 3 synthetic inputs, PS end-to-end |
| Original float kernel | 140.32 ms | includes copies, flush, wait, invalidate |
| ARM same round | 7.24 ms (1000-rep P50 6.59 ms) | same vector |
| Attribution | 252 model evaluations, 4 paths | ~260 ms on ARM |
| Resources (with PS/AXI, no HDMI) | LUT 11,367 / FF 8,108 / BRAM 83.5 / DSP 101 | 100 MHz, WNS +0.866 ns |

Full methodology and comparison scope: [docs/04_results.md](docs/04_results.md).

---

## Quick start

```bash
python -m pip install -r requirements.txt
python -B tests/check_engine.py      # input contract, batch cap, additivity
python -B tests/check_guards.py      # temperature / shape / power gates
python -B host/preview.py            # http://127.0.0.1:8765 (CPU only)
```

On the board (set `PYNQ_HOST`, `PYNQ_PASSWORD`, `PYNQ_HOSTKEY` first — see `.env.example`):

```bash
python -B host/deploy.py
python -B host/start_services.py
python -B host/validate_cpu_web.py
```

FPGA backend requires an explicit external-power confirmation file and matching bit/hwh hashes; the worker refuses to load otherwise. See [docs/06_deployment_on_pynq.md](docs/06_deployment_on_pynq.md).

Rebuilding hardware requires Vivado / VHDL-HLS 2018.3 — [docs/05_reproduction.md](docs/05_reproduction.md).

---

## Repository layout

```
board/ model/ hls/ batch8_candidate/      core: runtime, contract, FPGA kernels
standalone_terminal/ photo_intake/        touch terminal, camera OCR intake
photo_demo_20261103/ camera_capture_20261103/  camera capture path
hdmi_terminal/ display_wiring/            display experiments
web_touch_20261101/ fast_boot_20261102/ ...    date-stamped stage experiments
host/ tools/ tests/ reports/ docs/        tooling, evidence, documentation
```

Per-directory purpose: [docs/10_repository_map.md](docs/10_repository_map.md).

---

## Usage notes

- Outputs are for competition and research demonstrations, not diagnosis or treatment decisions.
- The model comes from prior research; this repository documents deployment, hardware optimisation and engineering verification.
- Hardware protection includes external-power confirmation, temperature checks, task exclusion and request limits.
- Low-rank and quantisation errors are reported separately for the documented synthetic probes.

Usage scope and engineering safeguards: [documentation](docs/08_limitations_and_safety.md).

---

## Licence and citation

Code under [MIT](LICENSE). Model-weight provenance and licensing caveats: [NOTICE.md](NOTICE.md). Third-party components: [THIRD_PARTY.md](THIRD_PARTY.md).

```bibtex
@software{zhinao_xiandao_pynq_2026,
  title  = {Zhinao Xiandao: a PYNQ-Z2 terminal for stroke severity prediction},
  year   = {2026},
  note   = {Low-rank fixed-point DNN accelerator with approximate Shapley attribution}
}
```

中文说明见 [README.md](README.md).
