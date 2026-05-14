#import "@preview/zebraw:0.6.3": zebraw, zebraw-themes

#set document(title: "鲁棒 JPEG 图像隐写实验报告")
#set page(
  paper: "a4",
  margin: (x: 2.6cm, y: 2.5cm),
)
#set par(
  justify: true,
)
#set text(
  lang: "zh",
  font: "Noto Serif CJK SC",
)
#show raw.where(block: false): set text(
  font: "Menlo",
)
#show: zebraw.with(
  ..zebraw-themes.zebra,
  lang: true,
  numbering: true,
  numbering-separator: true,
  radius: 4pt,
  inset: (x: 7pt, y: 6pt),
  lang-font-args: (
    font: "Menlo",
    size: 8pt,
  ),
  numbering-font-args: (
    font: "Menlo",
    size: 7pt,
    fill: gray,
  ),
)

#align(center)[
  #text(size: 18pt, weight: "bold")[鲁棒 JPEG 图像隐写实验报告]
]

#v(1em)

= 实验目的

本实验围绕鲁棒 JPEG 图像隐写算法展开，目标是实现并比较 `J-UNIWARD` 与 `J-UNIWARD-P` 两种方法在 JPEG 重压缩信道下的表现。实验关注的问题是：当载密图像经过 JPEG 重压缩后，嵌入的秘密信息是否仍能被正确提取。

具体目标包括：

+ 建立一个可复现的 JPEG 域隐写实验流程，包括图像预处理、DCT 系数量化、信息嵌入、重压缩模拟、信息提取和指标统计。
+ 实现 `J-UNIWARD` 风格的代价引导嵌入方法，观察其在重压缩后的误码情况。
+ 实现 `J-UNIWARD-P` 的核心思想，即先在重压缩后的信道域中确定目标嵌入结果，再调整原始 JPEG 域系数，使其经过信道压缩后尽量保持目标系数。
+ 输出实验结果表格，为后续在 BOSSbase-1.01 和 UCID 数据集上的完整复现实验提供代码基础。

= 实验原理

JPEG 图像压缩通常以 $8 times 8$ 像素块为单位进行离散余弦变换（DCT），然后使用量化表对 DCT 系数进行量化。设某一 DCT 系数为 $c$，对应量化步长为 $q$，则量化后的 JPEG 域系数可以表示为：

$ C = op("round")(c / q) $

JPEG 域隐写通常不直接修改像素，而是在量化后的 DCT 系数上进行微小调整，例如将某些非零 AC 系数增加或减少 $1$，以改变其最低有效位并承载秘密消息。为了降低视觉失真和统计异常，算法需要为每个可修改系数计算嵌入代价。代价越小，表示在该位置修改系数越不容易被察觉。

`J-UNIWARD` 属于代价自适应隐写方法。其基本思想是：优先在纹理复杂、局部变化较强的区域嵌入信息，因为这些区域对细微修改更不敏感。本实验实现了一个简化的 `J-UNIWARD` 风格代价模型：先由反量化和 IDCT 得到图像块，再根据图像梯度、块内活动度和 DCT 基函数影响估计修改代价。随后使用代价引导的 LSB matching 方法完成嵌入。

普通 `J-UNIWARD` 的问题是：如果载密图像经过 JPEG 重压缩，原先修改过的 DCT 系数可能被重新量化，导致嵌入位发生翻转。重压缩过程可抽象为从源量化表 $Q_s$ 到信道量化表 $Q_c$ 的再量化：

$ C_c = op("round")((C_s Q_s) / Q_c) $

`J-UNIWARD-P` 针对这一问题进行改进。它先模拟信道重压缩，在信道域中选择嵌入位置并确定目标系数，然后反过来寻找源 JPEG 域中的系数 $C_s'$，使得其经过重压缩后满足目标信道系数：

$ op("round")((C_s' Q_s) / Q_c) = C_c' $

这样，实际发送的载密图像虽然仍处于源 JPEG 域，但经过社交平台或其他 JPEG 信道重压缩后，接收端看到的信道域系数仍能保留嵌入信息。因此，`J-UNIWARD-P` 预期比直接嵌入的 `J-UNIWARD` 具有更低的重压缩后误码率。

= 实验内容

实验代码位于项目的 `lab/` 目录中，主要结构如下：

```text
lab/
+-- configs/
|   +-- default.json
|   +-- table1.json
+-- scripts/
|   +-- make_demo_dataset.py
|   +-- prepare_dataset.py
|   +-- run_table1.py
|   +-- summarize_results.py
+-- src/robust_stego/
|   +-- jpeg.py
|   +-- costs.py
|   +-- embedding.py
|   +-- adjustment.py
|   +-- experiment.py
|   +-- metrics.py
+-- report/
    +-- report.tex
    +-- report.typ
```

各模块功能如下：

+ `jpeg.py`：实现 JPEG 质量因子到量化表的转换、$8 times 8$ DCT/IDCT、量化、反量化和重压缩模拟。
+ `costs.py`：计算 `J-UNIWARD` 风格的修改代价。
+ `embedding.py`：实现代价引导的 LSB matching 嵌入与提取。
+ `adjustment.py`：实现 `J-UNIWARD-P` 中的源域系数调整。
+ `experiment.py`：组织单张图像上的 `J-UNIWARD` 和 `J-UNIWARD-P` 对比实验。
+ `run_table1.py`：批量运行实验并输出 `results.csv` 和 `summary.csv`。

实验流程如下：

+ 将原始图像转换为灰度图，并统一裁剪或缩放到指定尺寸。
+ 按设定 JPEG 质量因子生成源 JPEG 域量化 DCT 系数。
+ 对 `J-UNIWARD`，直接在源 JPEG 域中根据代价选择非零 AC 系数嵌入消息。
+ 对 `J-UNIWARD-P`，先模拟信道重压缩，在信道域中嵌入消息，再调整源 JPEG 域系数。
+ 将载密系数经过 JPEG 信道重压缩，按嵌入位置提取消息。
+ 统计误码率（BER）、PSNR、修改系数数量和总代价。

默认配置采用源 JPEG 质量因子 $95$、信道 JPEG 质量因子 $75$，用于模拟高质量载密图像被较低质量 JPEG 信道重压缩的情况。可通过如下命令运行演示实验：

```bash
python3 scripts/make_demo_dataset.py --output-dir data/work/demo --count 4 --size 256
python3 scripts/run_table1.py \
  --input-dir data/work/demo \
  --output-dir results/demo \
  --max-images 2 \
  --payload 0.1 \
  --payload 0.2
```

在当前小规模演示数据上的验证结果如下。该结果用于检查实现流程是否正确，不代表 BOSSbase-1.01 或 UCID 上的正式实验结论。

#figure(
  table(
    columns: (1.4fr, 0.8fr, 1fr, 1fr),
    inset: 6pt,
    align: center,
    table.header([方法], [Payload], [平均 BER], [平均 PSNR / dB]),
    [`J-UNIWARD`], [0.1], [0.513749], [42.44],
    [`J-UNIWARD`], [0.2], [0.505396], [41.85],
    [`J-UNIWARD-P`], [0.1], [0.000000], [41.84],
    [`J-UNIWARD-P`], [0.2], [0.000000], [40.72],
  ),
  caption: [演示数据上的重压缩后误码率],
)

从该 smoke test 可以看出，直接嵌入的 `J-UNIWARD` 在重压缩后 BER 接近 $0.5$，说明嵌入位基本被信道扰乱；而 `J-UNIWARD-P` 通过信道域预嵌入和源域系数调整，在当前模拟信道下能够保持提取结果稳定。

= 实验总结

本实验完成了一个可运行的鲁棒 JPEG 图像隐写实验框架，实现了从图像预处理、JPEG 域系数生成、代价计算、消息嵌入、重压缩模拟到结果汇总的完整流程。实验结果表明，在 JPEG 重压缩场景下，直接在源 JPEG 域嵌入的 `J-UNIWARD` 容易受到再量化影响，导致较高的误码率；而 `J-UNIWARD-P` 将信道重压缩过程纳入嵌入设计，通过调整源域系数保证重压缩后目标系数不变，因此更适合鲁棒隐写场景。

当前实现主要用于课程实验和算法流程理解，仍有进一步改进空间。首先，本实验使用的是紧凑的 Python 复现版本，代价模型采用了简化的纹理活动度估计，并未完整复刻论文中的所有小波残差细节。其次，嵌入过程使用代价引导的 LSB matching 模拟器，而不是完整的 STC 编码。最后，当前报告中的数值来自小规模演示数据，正式结果还需要在 BOSSbase-1.01 和 UCID 数据集上批量运行后替换。

后续工作可以继续完善三个方向：一是加入更接近原始论文的 `J-UNIWARD` 代价计算和 STC 编码；二是使用真实数据集运行完整 payload 设置并生成正式对比表；三是扩展信道模型，测试不同 JPEG 质量因子、不同图像尺寸和不同重压缩强度下的鲁棒性。
