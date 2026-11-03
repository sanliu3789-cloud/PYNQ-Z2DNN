# 硬件与 HLS 实现

## 一、平台

| 项目 | 值 |
|---|---|
| 板卡 | PYNQ-Z2（Digilent） |
| 器件 | `xc7z020clg400-1`（Zynq-7020） |
| PS | 双核 Cortex-A9 @ 650 MHz，1 GB DDR3 |
| 镜像 | PYNQ 3.0.1（Ubuntu 22.04，Python 3.10） |
| 工具 | Vivado 2018.3 + Vivado HLS 2018.3 |
| PL 时钟 | 100 MHz（`FCLK_CLK0`） |

## 二、定点核微架构

源码：`hls/nihss_lowrank.cpp`，类型：`hls/model_types.h`。

| 类型 | 定义 | 用途 |
|---|---|---|
| `weight_t` | `ap_fixed<16,0,AP_RND_CONV,AP_SAT>` | 权重（Q0.15 纯小数） |
| `bias_t` | `ap_fixed<32,12>` | 偏置 |
| `data_t` | `ap_fixed<32,16>` | 激活值 / 输入 |
| `acc_t` | `ap_fixed<48,24>` | 累加器 |
| `sigmoid_t` | `ap_ufixed<18,1>` | Sigmoid 查表项 |

为什么这样切：

- 权重用整数 ROM 存储再解释为定点位型——旧版 HLS 对大量 `ap_fixed` 全局常量构造会编译失败（见 `CHANGELOG`/内部记录），改成原始整数数组规避。
- 输入/累加器放宽到 32/48 位，是因为原训练来源表 347×62 个元素中有 1117 个超出 `ap_fixed<16,6>`，用 16 位输入会饱和。
- 权重保持 16 位，是体积与精度的折中：定点化带来的最大偏差约 0.00074 ΔNIHSS（见 `docs/03_model_and_numerics.md`）。

### `dense` 模板

```cpp
template<int NI,int NO,int P,bool ACT>
static void dense(const data_t in[NI], data_t out[NO], const short w[NI][NO], const int b[NO])
```

- `#pragma HLS ARRAY_PARTITION variable=w cyclic factor=P dim=2`：权重按输出通道循环分块到 P 个 bank。
- 输出按 P 路并行累加（`sums[P]`），内层循环 `#pragma HLS PIPELINE II=1`。
- 每层实例化参数：

| 层 | NI→NO | P | 激活 |
|---|---:|---:|---|
| 1 | 62→500 | 8 | Sigmoid |
| 2 | 500→4 | 4 | 无 |
| 3 | 4→500 | 8 | Sigmoid |
| 4 | 500→64 | 8 | 无 |
| 5 | 64→500 | 8 | Sigmoid |
| 6 | 500→1 | 1 | 无 |

- Dense 函数 `INLINE off`，避免把 6 层展开成一个巨大函数导致布线爆炸。

### Sigmoid

```cpp
if (x <= -12) return 0;
if (x >= 12)  return 1;
pos = (x + 12) * (4096.0/24.0);   // 4096 段
```

4097 点表 + 线性插值，覆盖 [-12, 12]。超出区间直接饱和，这是为什么输入要限制在 ±8192 的保守范围内。

## 三、接口与寄存器

### 标量核（`nihss_lowrank.bit`）

```cpp
void nihss_lowrank(const float *x, float *y)  // m_axi + s_axilite
```

| 偏移 | 名称 | 说明 |
|---|---|---|
| `0x10` | x | 输入缓冲物理地址（62 × float32 = 248 B） |
| `0x18` | y | 输出缓冲物理地址（1 × float32） |
| — | ap_ctrl | 启动/完成由 HLS 控制寄存器管理 |

PS 侧流程（`board/fpga_worker.py`）：写入两个地址 → 启动 → 轮询完成 → `invalidate` 输出缓冲 → 读回。

### 批量核（`nihss_lowrank_batch8.bit`，C/RTL 与布局布线验证）

| 偏移 | 名称 | 说明 |
|---|---|---|
| `0x00` | CTRL | 启动 |
| `0x10` | ap_return | 返回码（0 成功，1 非法条数） |
| `0x18` | x | 输入缓冲（8 × 62 × float32 = 1984 B） |
| `0x20` | y | 输出缓冲（8 × float32 = 32 B） |
| `0x28` | count | 批大小，仅允许 1–8 |

`count` 非法（0 或 >8）时立即返回 1 且不修改输出缓冲。

## 四、实现结果

### 标量核（`hls/`）

| 资源 | 使用 | 可用 |
|---|---:|---:|
| Slice LUT | 11,367 | 53,200 |
| Slice FF | 8,108 | 106,400 |
| Block RAM Tile | 83.5 | 140 |
| DSP48 | 101 | 220 |
| 时序 100 MHz | WNS +0.866 ns，WHS +0.061 ns | 全部用户约束通过 |

原始报告：`hls/utilization.rpt`、`hls/timing_summary.rpt`。

### 批量核（`batch8_candidate/`）

| 资源 | 使用 |
|---|---:|
| Slice LUT | 11,443 |
| Slice FF | 8,226 |
| Block RAM Tile | 83.5 |
| DSP48 | 101 |
| 时序 100 MHz | WNS +1.044 ns，WHS +0.015 ns |

报告：`batch8_candidate/reports/verification.json`。

## 五、Block Design

- PS7 + `proc_sys_reset` + AXI Interconnect + HLS IP。
- `ps_from_working.tcl` 记录了与现有工程一致的 876 项 PS 配置，构建时逐项比对（`reports/ps_configuration_comparison.json`）。
- BD 的 Tcl 位于 `hls/board_build/.../hw_handoff/design_1_bd.tcl`（构建产物未入库，可用 `build_board.tcl` 重建）。

## 六、实现特点

- DNN 采用独立 Overlay，资源与时序报告对应 PS、AXI 互连和计算核。
- 权重常驻片上，按输出通道分块，以多路并行累加实现层内计算。
- 各层顺序执行，复用单核完成批量 1–8 条输入，降低主机启动与控制次数。
- 标量核提供独立上板计时，批量核提供 C/RTL 协同仿真和布局布线结果。
