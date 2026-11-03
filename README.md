# 智脑先导 · PYNQ-Z2 脑卒中严重度评分加速终端

**Zhinao Xiandao — a PYNQ-Z2 edge terminal for stroke severity (ΔNIHSS) prediction, approximate Shapley attribution and touch-screen operation.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.12-informational)](requirements.txt)
[![Board](https://img.shields.io/badge/board-PYNQ--Z2%20%28Zynq--7020%29-orange)](docs/02_hardware.md)
[![Toolchain](https://img.shields.io/badge/Vivado%20%2F%20HLS-2018.3-lightgrey)](docs/05_reproduction.md)
[![Project](https://img.shields.io/badge/project-FPGA%20competition-teal)](docs/04_results.md)

> 本项目围绕 **PYNQ-Z2 端侧推理、低秩定点加速和触屏交互**开展设计与验证。下文展示已实现的功能、硬件工程与实测结果，性能数据均附测试口径。项目用于竞赛展示与研究演示。

---

## 一、它做什么

输入 62 项临床指标（年龄、血压、血糖、血小板、NIHSS 分项等），输出**24 小时后 ΔNIHSS 的预测值**，并给出 62 项特征各自的近似 Shapley 贡献。

推理有三种后端，共用同一套 62 维接口契约：

| 后端 | 实现 | 用途 |
|---|---|---|
| CPU 本机预览 | NumPy（`host/preview.py`） | 无板卡时开发与演示 |
| ARM NumPy | 板上 Cortex-A9，单线程 BLAS | 板端功能基线 |
| FPGA 定点 | HLS 定点核 + AXI-Lite，权重常驻片上 | 加速实验 |

前端是板端 Flask 网页（62 项输入、数字键盘、预测、按需归因），另有独立的触屏终端进程（PYNQ framebuffer + evdev 触摸）。

### 功能与工程结构

下图按各模块的运行环境展示已完成的功能：触屏应用使用 ARM 后端，定点加速核采用独立上板测试，相机采用单帧采集工程，OCR 在 Windows 本机运行。

```mermaid
flowchart TB
    subgraph Terminal[板端触屏应用]
        Screen[7 寸 HDMI 触屏] <--> Web[PS 本地网页与 62 项输入校验]
        Web --> ARM[ARM NumPy 预测与近似 Shapley 归因]
        ARM --> Result[预测值与特征贡献展示]
    end
    subgraph Accelerator[FPGA 加速工程 · 独立上板验证]
        Input[62 维输入] --> DNN[低秩 4/64 · 16 位定点 HLS 核]
        DNN --> Timing[PS 端到端 1.42–1.58 ms]
    end
    subgraph Capture[相机单帧采集工程]
        Camera[OV5640 相机] --> DVP[PL DVP 采集]
        DVP --> Frame[320×240 图像读回]
    end
    subgraph Intake[Windows 本机 OCR 应用]
        Picture[病例图片上传] --> OCR[文字识别与字段提取]
        OCR --> Review[人工核对与表单回填]
    end
```

---

## 二、项目成果

| 成果 | 实现与验证结果 | 对应工程与证据 |
|---|---|---|
| 62 维输入校验、预测与近似 Shapley 归因 | 统一三种后端的输入契约，实现 4 条排列路径、252 次模型求值及贡献加和校验 | `tests/check_engine.py`、`reports/cpu_web_verified_20261030.json` |
| 板端 Flask 网页与触屏终端 | 完成触屏交互、数字键盘、结果展示与开机自启验证 | `standalone_terminal/README.md`、`web_touch_20261101/` |
| 低秩 4/64 + 16 位定点 HLS 核 | 完成 3 次上板测试，PS 端到端 **1.42–1.58 ms** | `hls/`、`reports/` |
| 批量 1–8 条候选核 | 完成 C/RTL 协同仿真与 100 MHz 布局布线验证 | `batch8_candidate/` |
| OV5640 相机单帧采集 | 读到芯片 ID `0x5640`，完成 **320×240** 图像采集 | `camera_capture_20261103/` |
| 板端拍照与范例运算演示 | 完成拍照、照片显示、合成范例 62 项固定数据回填、预测与归因展示 | `photo_demo_20261103/拍照演示说明.md` |
| 病例图片 OCR 与字段回填 | 在 Windows 本机完成文字识别、字段提取、人工核对与回填验证 | `photo_intake/` |

**性能优化成果**：原 FPGA 核（浮点、单条）实测 140.32 ms，新定点核为 1.42–1.58 ms。这是低秩分解、定点化与硬件结构优化共同带来的端到端结果，数值误差与测试条件分别记录于 [结果与测量口径](docs/04_results.md)。

---

## 三、关键数字

| 项目 | 结果 | 口径 |
|---|---:|---|
| 原 H5 模型 | 62-500-500-500-1，533,001 参数 | `model/contract.json` |
| 低秩结构 | 62-500-**4**-500-**64**-500-1 | MAC 从 531,500 降到 99,500 |
| 低秩 4/64 vs 原模型 | 最大 0.0086 ΔNIHSS | 32 组合成探针，FP32 |
| 定点 vs 同一低秩 FP32 | 最大 0.00074 ΔNIHSS | 同上 |
| 新定点核上板 | 1.42–1.58 ms | 3 个合成输入，PS 端到端范围 |
| 原硬件单条 | 140.32 ms | 含输入复制、flush、控制、等待、invalidate |
| 同轮 ARM 前向 | 7.24 ms；1000 次 P50 6.59 ms | 同一向量 |
| 近似归因 | 252 次模型求值，4 条路径 | ARM 后端约 260 ms |
| 资源（含 PS/AXI，不含 HDMI） | LUT 11,367 / 53,200；FF 8,108 / 106,400；BRAM 83.5 / 140；DSP 101 / 220 | 100 MHz，WNS +0.866 ns，WHS +0.061 ns |

---

## 四、快速开始

### 4.1 本机（不需要板卡）

```bash
python -m pip install -r requirements.txt
python -B tests/check_engine.py      # 输入校验、批量上限、归因加和
python -B tests/check_guards.py      # 温度/形状/供电门控
python -B host/preview.py            # http://127.0.0.1:8765 ，纯 CPU
```

`host/preview.py` 只监听回环地址，不连板、不加载 Overlay。网页与板端完全相同（同一份 `board/static/index.html`）。

### 4.2 部署到 PYNQ-Z2

```bash
# 参考部署路径：/home/xilinx/jupyter_notebooks/nihss_competition_v3
python -B host/deploy.py                 # 只传有变化的文件
python -B host/start_services.py         # CPU 后端，8080 端口
python -B host/validate_cpu_web.py       # 端到端数值一致性检查
```

环境变量见 `.env.example`：`PYNQ_HOST`、`PYNQ_PASSWORD`、`PYNQ_HOSTKEY`、`PYNQ_PLINK`。**代码里没有任何口令或板卡地址的默认值。**

硬件后端（谨慎）：

```bash
python -B host/deploy_bitstream.py       # 校验并传 bit/hwh + manifest
python -B host/start_services.py --backend fpga --external-power-confirmed
```

FPGA worker 在加载设计前会检查三件事：`runtime/power_clearance.json` 记录的外部供电确认、温度传感器可读、bit/hwh 哈希与 manifest 一致。缺一项就拒绝加载，不提供"重试绕过"。

详细步骤：[docs/06_deployment_on_pynq.md](docs/06_deployment_on_pynq.md)

### 4.3 重建 FPGA 硬件

```powershell
# 需要 Vivado / VHDL-HLS 2018.3
cd hls
vivado_hls -f build_hls.tcl          # C 仿真 + 综合 + 导出 IP
vivado -mode batch -source build_board.tcl
```

工具有两个已知坑，脚本里已经处理：中文路径（临时映射英文盘符）、旧版 HLS 的 date revision 溢出（[AMD AR76960](https://docs.amd.com/r/en-US/76960)）。细节见 [docs/05_reproduction.md](docs/05_reproduction.md)。

---

## 五、仓库结构

```
board/                    板端 Flask 应用、推理引擎、受限 FPGA worker、网页
model/                    62 维接口契约 + 原模型/低秩模型 npz
hls/                      低秩定点核：C++、权重头、测试台、Tcl、bit/hwh
batch8_candidate/         批量 1–8 条候选核（含独立 runtime 与验证报告）
standalone_terminal/      触屏终端、systemd 单元、开机自启
photo_intake/             病例截图 OCR → 字段候选 → 人工确认 → 回填
photo_demo_20261103/      板端摄像头采集与网页代理
camera_capture_20261103/  相机单帧采集工程（PL）
hdmi_terminal/            HDMI 终端 UI 与只读诊断
display_wiring/           RGB 屏接线方案、XDC、线路核对脚本
web_touch_20261101/       触屏网页各阶段部署脚本与验收记录
web_hdmi_20261101/        浏览器显示方案探索
fast_boot_20261102/ 等    阶段实验：启动预算、电源生命周期、键盘响应等
host/                     主机端构建/部署/校验/预览工具
tools/                    可复制到板端的 NumPy 基线、只读环境采集
tests/                    check_engine.py、check_guards.py
reports/                  各阶段验证报告（已脱敏）
docs/                     架构、硬件、数值口径、复现、部署、使用说明、隐私
```

每个目录的定位见 [docs/10_repository_map.md](docs/10_repository_map.md)。按日期命名的目录保存实验过程与验证证据，便于追溯设计和复现结果。

---

## 六、文档索引

| 文档 | 内容 |
|---|---|
| [docs/01_architecture.md](docs/01_architecture.md) | 数据流、三种后端、归因算法、进程与 IPC |
| [docs/02_hardware.md](docs/02_hardware.md) | PYNQ-Z2 资源、HLS 微架构、寄存器、时序 |
| [docs/03_model_and_numerics.md](docs/03_model_and_numerics.md) | 62 维契约、定点格式、误差分解、Sigmoid 查表 |
| [docs/04_results.md](docs/04_results.md) | 实测数据、仿真结果与对照口径 |
| [docs/05_reproduction.md](docs/05_reproduction.md) | 工具版本、构建步骤、已知坑 |
| [docs/06_deployment_on_pynq.md](docs/06_deployment_on_pynq.md) | 板端目录、环境变量、服务、电源门控 |
| [docs/07_camera_and_display.md](docs/07_camera_and_display.md) | OV5640 采集、HDMI 触屏与本机 OCR |
| [使用范围与工程保护](docs/08_limitations_and_safety.md) | 演示用途、温度与供电保护、数值说明 |
| [docs/09_privacy.md](docs/09_privacy.md) | 数据与隐私处理、脱敏规则 |
| [docs/10_repository_map.md](docs/10_repository_map.md) | 目录级说明 |
| [docs/11_faq.md](docs/11_faq.md) | 常见误解与问题 |
| [docs/12_publish_checklist.md](docs/12_publish_checklist.md) | 发布到 GitHub 前的检查清单 |

---

## 七、使用说明

- **用途**：用于竞赛展示与研究演示，不作为诊断、分诊或治疗依据。
- **模型来源**：课题组前期研究；本仓库展示模型部署、硬件优化与工程验证成果。
- **精度口径**：低秩近似误差与定点量化误差分别记录，结果对应文中注明的合成测试输入。
- **工程保护**：实现板端 60 °C 暂停、单任务互斥、请求 ≤20 KB、每分钟评估上限和独立供电确认。
- **第三方素材**：板卡手册、屏幕说明书、厂商数据手册不在本仓库内，按引用处理，见 [THIRD_PARTY.md](THIRD_PARTY.md)。

---

## 八、许可与引用

代码以 [MIT](LICENSE) 许可发布。模型权重的来源与授权说明见 [NOTICE.md](NOTICE.md)。引用格式见 [CITATION.cff](CITATION.cff)。

```bibtex
@software{zhinao_xiandao_pynq_2026,
  title  = {Zhinao Xiandao: a PYNQ-Z2 terminal for stroke severity prediction},
  year   = {2026},
  note   = {Low-rank fixed-point DNN accelerator with approximate Shapley attribution},
  url    = {https://github.com/<your-org>/pynq-stroke-ai}
}
```

---

## English summary

A research prototype that runs a 62-input clinical DNN on a PYNQ-Z2 (Zynq-7020). The network is factorised into a low-rank form (62-500-4-500-64-500-1) and implemented as a 16-bit fixed-point HLS kernel with on-chip resident weights, reaching 1.42–1.58 ms per sample end-to-end from the processing system. Around it there is a Flask UI on the ARM core, a 4-permutation approximate Shapley explainer (252 model evaluations), a touch terminal, and an OV5640 single-frame capture path.

The touch application runs on ARM; the FPGA kernel and camera capture have separate hardware verification paths, while OCR and form filling run on Windows. Results are reported with their measurement scope; see [docs/04_results.md](docs/04_results.md). The project is for competition and research demonstrations, not for clinical decisions.

Licensed under MIT. See [README.en.md](README.en.md) for the English version.
