# 目录地图

仓库按运行时代码、FPGA 工程、应用功能、实验记录与技术文档组织。按日期命名的目录保存设计过程与验证证据。

## 一、核心运行时代码

| 目录 | 作用 | 关键文件 |
|---|---|---|
| `board/` | 板端 Flask 应用与推理引擎 | `app.py`、`engine.py`、`fpga_worker.py`、`static/index.html` |
| `model/` | 62 维契约与三份 npz | `contract.json`、`original.npz`、`lowrank_4_64.npz`、`lowrank_4_96.npz` |
| `standalone_terminal/` | 触屏终端与 systemd 单元 | `terminal_service.py`、`terminal_ui.py`、`touch_input.py`、`*.service` |
| `host/` | 主机端构建/部署/校验/预览 | `deploy.py`、`start_services.py`、`validate_cpu_web.py`、`preview.py` |
| `tests/` | 自检 | `check_engine.py`、`check_guards.py` |
| `tools/` | 可拷到板端的只读工具 | `benchmark_reference.py`、`collect_board_info.py`、`inspect_and_probe.py` |

## 二、FPGA 工程

| 目录 | 作用 |
|---|---|
| `hls/` | 低秩定点核：`nihss_lowrank.cpp`、`model_types.h`、`model_weights.h`、`testbench.cpp`、构建 Tcl、`artifacts/bit+hwh`、实现报告 |
| `batch8_candidate/` | 批量 1–8 条候选核：源码、`runtime/`、`fixtures/`、`artifacts/`、`reports/` |
| `camera_capture_20261103/` | OV5640 单帧采集工程：`build.tcl`、`hardware/camera_pins.xdc`、`rtl/`、`sim/`、`host/`、`artifacts/` |
| `display_wiring/` | RGB 屏接线方案、XDC、线路核对脚本与厂商资料核对记录 |
| `display_manual_review_20261101/` | 7 寸 HDMI 屏手册核对结论 |

## 三、应用侧功能

| 目录 | 作用 | 交付内容 |
|---|---|---|
| `photo_intake/` | 病例截图 OCR → 字段候选 → 人工确认 → 回填 | Windows 本机应用与验证记录 |
| `photo_demo_20261103/` | 板端拍照、照片显示与合成范例运算 | 单帧采集、显示恢复、固定范例回填与预测归因 |
| `hdmi_terminal/` | HDMI 终端 UI 与只读诊断（含 PYNQ 库只读参考副本） | 界面可渲染 |
| `photo_intake_board_20261103/` | 板端图片录入接口开发记录 | 候选代码、基线备份与联调记录 |

## 四、阶段实验记录（按时间）

| 目录 | 主题 | 结论 |
|---|---|---|
| `web_touch_20261101/` | 触屏网页、校准、启动预算、图表、键盘响应 | 触控与界面已验证 |
| `web_hdmi_20261101/` | 浏览器显示方案、依赖打包、黑屏排查 | 浏览器显示实验记录 |
| `fast_boot_20261102/` | 启动时间预算与快速启动 | 独立冷启动记录为 61.02 s |
| `age_integer_20261102/` | 年龄改为整数、吸烟改是/否 | 已部署并检查 |
| `touch_choices_20261102/` | 触屏选项控件 | 已验收 |
| `keyboard_response_20261102/` | 键盘响应与渲染缓存修复 | 已验收 |
| `power_lifecycle_20261102/` | 正常关机、上电周期 | 已验收 |
| `power_diagnosis_20261101/` | 供电与重启事件诊断 | 诊断脚本与事件记录 |
| `camera_*_20261103/` | 相机接入、接线与恢复采集实验 | 单帧采集成果与过程记录 |
| `data/` | `web_dnn_manifest.json`（导出时的接口清单） | 归档 |
| `evidence/` | 数值审计与低秩探针的聚合证据、只读脚本 | 归档 |
| `reports/` | 各阶段验证报告（已脱敏） | 证据 |
| `skill/` | 可复用的 PYNQ 验证流程与失效条件 | 文档 |

## 五、文档

| 位置 | 内容 |
|---|---|
| `README.md` / `README.en.md` | 项目总览 |
| `docs/01`–`docs/11` | 架构、硬件、数值、结果、复现、部署、相机显示、使用说明、隐私、本文件、FAQ |
| `docs/项目进展记录_20261028-1103.md` | 从 0 到首次上板的逐日记录（原工程 readme） |
| README 与 `docs/07_camera_and_display.md` | 功能结构与 OCR 流程的 Mermaid 图 |
| `docs/images/` | 历史方案图归档 |
| `LICENSE` / `NOTICE.md` / `THIRD_PARTY.md` / `CITATION.cff` | 许可与来源 |

## 六、不在仓库里的东西

| 内容 | 原因 |
|---|---|
| `MODEL_DNN.h5`（6 MB） | 上游授权待确认，仓库提供导出 npz 与哈希 |
| Vivado 构建目录（`board_build/`、`fpga_build/` 等，约 900 MB） | 可由 Tcl 重建 |
| 板卡原始工程备份 | 含第三方 Notebook 与板端原始代码 |
| Chrome 用户配置、浏览器缓存 | 无归档价值，涉及本机信息 |
| 患者记录、真实病例照片 | 隐私 |
| 第三方厂商手册、PYNQ vendor IP | 版权，按引用处理 |
| 板卡串口/启动日志 | 含内网地址与系统信息 |
