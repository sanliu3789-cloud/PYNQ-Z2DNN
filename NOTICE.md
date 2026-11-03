# NOTICE — 来源、授权与致谢

本文件说明仓库内哪些是本项目原创，哪些来自第三方或课题组前期研究。

## 一、本项目原创部分

以下代码、文档与图为本次工程新增，按 [MIT](LICENSE) 发布：

- `board/`、`host/`、`tests/`、`standalone_terminal/`、`photo_intake/`、`photo_demo_20261103/` 中的 Python / HTML / JS 代码；
- `hls/` 中的定点核源码、权重头、测试台与 Tcl 脚本（权重数值来自下游模型）；
- `batch8_candidate/` 中的批量核源码、runtime 与验证脚本；
- `camera_capture_20261103/`、`display_wiring/` 中的 PL 工程源码、XDC 与核对脚本；
- `docs/` 下的全部文档与 `docs/images/system_architecture.png`、`photo_ocr_pipeline.png`。

## 二、模型权重

| 文件 | 来源 | 状态 |
|---|---|---|
| `model/original.npz` | 由课题组既有网页版本的 `MODEL_DNN.h5` 只读导出（结构 62-500-500-500-1，533,001 参数） | **上游授权未在资料中体现** |
| `model/lowrank_4_64.npz` | 对本项目导出的 `original.npz` 做秩 4/64 分解 | 派生自上一行 |
| `model/lowrank_4_96.npz` | 同上，秩 4/96 | 派生自上一行 |
| `model/contract.json` | 62 维特征名、训练均值、取值范围、SHA256 | 由同一次导出产生 |

`contract.json` 中的 `source_h5_sha256` 记录了原始 H5 的哈希，便于核对。原始 H5 因体积与授权原因未随仓库提供。

**公开或商用前，请与课题组确认训练数据与模型权重的授权范围。** 在授权确认前，建议将本仓库作为代码与方法的公开，模型权重按需提供。

## 三、课题组前期研究

62 维特征定义、模型训练与临床背景来自课题组前期工作（DNN 与 KAN 相关工作）。本仓库只包含部署侧的重新实现，不包含原始训练数据、患者记录或论文稿件。引用相关成果时请引用课题组原始论文。

## 四、第三方组件

见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 五、未随仓库分发的素材

以下素材属于第三方版权，仅在本地核对时使用，未复制进仓库：

- Digilent / TUL《PYNQ-Z2 User Manual》；
- 树莓派 7/10/11.6/13.3 寸显示屏说明书；
- 野火（EmbedFire）7 寸屏与 GT911 触摸数据手册；
- PYNQ 官方 IP（`rgb2dvi`、`dvi2rgb`、`axi_dynclk` 等）与 PYNQ 运行时库；
- AMD/Xilinx 文档摘录。

需要复现时请从厂商官方渠道获取，并按各自的许可使用。

## 六、致谢

- PYNQ 项目与 Xilinx/AMD 大学计划提供的开源框架；
- Digilent PYNQ-Z2 硬件；
- 课题组前期研究提供的模型与临床问题定义。
