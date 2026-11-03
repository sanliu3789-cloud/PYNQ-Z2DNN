# 智脑先导 · PYNQ-Z2 脑卒中严重度评分加速终端

**Zhinao Xiandao — a PYNQ-Z2 edge terminal for stroke severity (ΔNIHSS) prediction, approximate Shapley attribution and touch-screen operation.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.12-informational)](requirements.txt)
[![Board](https://img.shields.io/badge/board-PYNQ--Z2%20%28Zynq--7020%29-orange)](docs/02_hardware.md)
[![Toolchain](https://img.shields.io/badge/Vivado%20%2F%20HLS-2018.3-lightgrey)](docs/05_reproduction.md)
[![Status](https://img.shields.io/badge/status-research%20prototype-red)](docs/08_limitations_and_safety.md)

> 这是一个**工程验证原型**，不是医疗器械，也不是已经验证过临床效果的产品。所有数字都标注了测量口径，未测的项目在本文里明确写成"未测"。

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

![系统总体结构](docs/images/system_architecture.png)

```mermaid
flowchart TB
    Screen[7 寸 HDMI 触屏 · 已验证] <--> Web[PS 本地网页 · 已验证]
    Camera[OV5640 相机 · 单帧已验证] -.-> DVP[PL 单帧采集 · 离线工程]
    DVP -.-> OCR[PS OCR · 未实现]
    OCR -.-> Review[字段校验与人工确认 · 未实现]
    Review -.-> Web
    Web --> ARM[ARM NumPy 后端 · 已验证]
    Web -. 联合 Overlay 待完成 .-> DNN[低秩 DNN PL 核 · 独立验证]
    Video[PL HDMI · 彩条已验证] --> Screen
```

---

## 二、当前做到哪一步（请先读这一节）

| 能力 | 状态 | 依据 |
|---|---|---|
| 62 维输入校验、预测、4 条排列路径近似 Shapley 归因 | ✅ 已验证（CPU / ARM / 定点核三种后端） | `tests/check_engine.py`、`reports/cpu_web_verified_20261030.json` |
| 板端 Flask 网页 + 触屏交互 + 开机自启 | ✅ 已验证 | `standalone_terminal/README.md`、`web_touch_20261101/` |
| 低秩 4/64 + 16 位定点 HLS 核 | ✅ 已上板 3 次，PS 端到端 **1.42–1.58 ms** | `hls/`、`reports/` |
| 批量 1–8 条候选核 | ⚠️ C/RTL 协同仿真 + 100 MHz 实现通过，**未上板** | `batch8_candidate/` |
| OV5640 相机单帧 320×240 采集 | ✅ 已读到 ID `0x5640` 并采到图像 | `camera_capture_20261103/` |
| 病例截图 OCR → 字段回填 | ⚠️ 仅电脑验证版（Windows.Media.Ocr），板上未实现 | `photo_intake/` |
| HDMI 与 DNN 同 Overlay、板上 OCR、功耗实测 | ❌ 未完成 | 见 `docs/08_limitations_and_safety.md` |
| 独立临床精度验证 | ❌ 未做 | 模型源自课题组前期研究，测试集未独立 |

**一个必须说清楚的问题**：原 FPGA 核（浮点、单条）实测 140.32 ms，新定点核 1.42–1.58 ms。这个差值同时包含低秩分解、定点化和硬件结构变化，**不是同模型同精度下的纯硬件加速比**。对照口径见 `docs/04_results.md`。

---

## 三、关键数字

| 项目 | 结果 | 口径 |
|---|---:|---|
| 原 H5 模型 | 62-500-500-500-1，533,001 参数 | `model/contract.json` |
| 低秩结构 | 62-500-**4**-500-**64**-500-1 | MAC 从 531,500 降到 99,500 |
| 低秩 4/64 vs 原模型 | 最大 0.0086 ΔNIHSS | 32 组合成探针，FP32 |
| 定点 vs 同一低秩 FP32 | 最大 0.00074 ΔNIHSS | 同上 |
| 新定点核上板 | 1.42–1.58 ms | 3 个合成输入，PS 端到端，样本不足以给 P95 |
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
docs/                     架构、硬件、数值口径、复现、部署、限制、隐私
```

每个目录的定位见 [docs/10_repository_map.md](docs/10_repository_map.md)。历史阶段脚本按原样保留，是因为它们记录了"为什么这么做"，而不是因为它们都是产品代码。

---

## 六、文档索引

| 文档 | 内容 |
|---|---|
| [docs/01_architecture.md](docs/01_architecture.md) | 数据流、三种后端、归因算法、进程与 IPC |
| [docs/02_hardware.md](docs/02_hardware.md) | PYNQ-Z2 资源、HLS 微架构、寄存器、时序 |
| [docs/03_model_and_numerics.md](docs/03_model_and_numerics.md) | 62 维契约、定点格式、误差分解、Sigmoid 查表 |
| [docs/04_results.md](docs/04_results.md) | 所有实测数字与口径，含"不能这么比"的说明 |
| [docs/05_reproduction.md](docs/05_reproduction.md) | 工具版本、构建步骤、已知坑 |
| [docs/06_deployment_on_pynq.md](docs/06_deployment_on_pynq.md) | 板端目录、环境变量、服务、电源门控 |
| [docs/07_camera_and_display.md](docs/07_camera_and_display.md) | OV5640 接线与采集、HDMI/触屏现状 |
| [docs/08_limitations_and_safety.md](docs/08_limitations_and_safety.md) | 未完成项、温度与供电保护、临床边界 |
| [docs/09_privacy.md](docs/09_privacy.md) | 数据与隐私处理、脱敏规则 |
| [docs/10_repository_map.md](docs/10_repository_map.md) | 目录级说明 |
| [docs/11_faq.md](docs/11_faq.md) | 常见误解与问题 |
| [docs/12_publish_checklist.md](docs/12_publish_checklist.md) | 发布到 GitHub 前的检查清单 |

---

## 七、边界与免责声明

- **不是医疗器械**：不用于诊断、分诊或治疗决策；输出仅为研究演示。
- **不生成治疗指令**：原网页中的治疗建议没有移植到本工程。
- **模型有效性未独立验证**：现有数据来自课题组前期研究，尚缺独立测试集与前瞻性验证。
- **精度口径**：低秩近似误差与定点量化误差分别记录，不能简单相加当作最大误差。
- **硬件安全**：板端 60 °C 暂停阈值、单任务互斥、请求 ≤20 KB、每分钟评估上限；发生过一次 USB 供电下的非人为重启，原因未定，因此新增了独立供电确认门槛。
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

This is **not** a medical device. Clinical accuracy has not been validated independently, HDMI and the DNN are not yet in one overlay, and the board once restarted unexpectedly under USB power, so hardware loading is gated behind an explicit external-power confirmation. Every number in this repository is reported with its measurement scope; see [docs/04_results.md](docs/04_results.md).

Licensed under MIT. See [README.en.md](README.en.md) for the English version.
