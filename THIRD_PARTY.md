# THIRD_PARTY — 第三方组件清单

本仓库**不包含**下列第三方源码或文档，只声明依赖关系。运行/构建时需要自行获取。

## 运行期 Python 依赖

| 组件 | 版本约束 | 许可 | 用途 |
|---|---|---|---|
| NumPy | `>=1.21,<2` | BSD-3-Clause | 推理与数值验证 |
| Flask | `==1.1.1` | BSD-3-Clause | 板端网页服务 |
| Jinja2 | `<3.1` | BSD-3-Clause | Flask 模板 |
| Werkzeug | `<2.1` | BSD-3-Clause | Flask 依赖 |
| itsdangerous | `<2.1` | BSD-3-Clause | Flask 依赖 |
| Pillow | 板端镜像自带 | HPND | 触屏终端渲染、OCR 预处理 |

版本钉死是因为板端 PYNQ 3.0.1 镜像内的 Python 3.10 环境；在 PC 上用 Python 3.12 验证过 `tests/`。

## 板端运行环境

| 组件 | 版本 | 说明 |
|---|---|---|
| PYNQ | 3.0.1 | 板卡镜像，含 `pynq` 包与 Jupyter |
| XRT | 镜像自带 | 需要 `XILINX_XRT=/usr`（非交互 SSH 环境常见坑） |
| Python | 3.10（镜像 venv） | `/usr/local/share/pynq-venv/bin/python3` |

## 构建工具

| 组件 | 版本 | 许可 | 说明 |
|---|---|---|---|
| Vivado | 2018.3 | AMD 商业许可 | 综合、实现、比特流 |
| Vivado HLS | 2018.3 | AMD 商业许可 | C 综合、IP 打包 |
| Node.js | 18+ | MIT | 仅 `host/verify_web.mjs` 浏览器检查 |
| Google Chrome | 任意现代版 | 专有 | 仅界面自动化检查 |

**没有**在仓库中分发 Vivado 生成的第三方 IP 源码（`rgb2dvi`、`dvi2rgb`、`axi_dynclk`、`processing_system7` 等）。`hls/` 与各 `*.srcs/` 目录里只保留本项目自己的源文件与 IP-XACT 描述。

## 文档与数据手册（未分发）

| 素材 | 版权方 | 用途 |
|---|---|---|
| PYNQ-Z2 User Manual v1.1 | Digilent / TUL | 排针定义、启动模式、供电要求 |
| 树莓派 7/10/11.6/13.3 寸屏说明书 | Raspberry Pi | 7 寸 1024×600 HDMI 屏时序 |
| 野火 7 寸屏 + GT911 数据手册 | 野火电子 / Goodix | 早期 RGB 屏方案核对 |
| AMD AR76960 | AMD | HLS date revision 溢出处理 |
| Microsoft Windows.Media.Ocr 文档 | Microsoft | OCR 接口说明 |

## 引用式依赖（代码中出现的链接）

- PYNQ：<https://github.com/Xilinx/PYNQ>
- PYNQ-Z2 供电要求：<https://www.sparkle-embedded.com.tw/en/PYNQ-Z2>
- AMD AR76960：<https://docs.amd.com/r/en-US/76960>
- Windows.Media.Ocr：<https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine>
- Tesseract：<https://tesseract-ocr.github.io/tessdoc/Installation.html>

如发现遗漏的第三方组件，请开 issue 指正。
