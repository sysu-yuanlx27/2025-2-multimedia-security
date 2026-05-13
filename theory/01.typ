#import "@local/sysu-exercise:0.1.0": *
#import "@preview/fletcher:0.5.8": diagram, node, edge

#show: exercise.with(
  title: "作业一",
  subtitle: "多媒体安全技术（理论）",
  student: (name: "元朗曦", id: "23336294"),
  lang: "zh",
)

#problem[
  设载体 $x = 1001101001101010$，嵌入信息

  $
    m = 10110111, quad hat(H)_(2 times 2) = mat(1, 0; 1, 1),
  $

  用修改次数作为代价，采用 STC 将 $m$ 嵌入 $x$，给出全部 STC 参数配置以及嵌入过程（画出格图），给出最后得到的 LSB 输出 $y$．
][
  全部 STC 参数配置如下：

  - 载体长度：$n = 16$ 比特，

  - 嵌入信息长度：$k = 8$ 比特，

  - 校验矩阵：$hat(H)_(2 times 2) = mat(1, 0; 1, 1)$，

  - 块长：$m = 2$（对应校验矩阵列数），

  - 代价度量：汉明距离（修改比特数），

  格图如下（部分边略）：

  #figure(
    diagram(
      node-inset: 2pt,
      spacing: 1.5em,

      node((-1, 1), "00"),
      node((-1, 2), "01"),
      node((-1, 3), "10"),
      node((-1, 4), "11"),

      node((0, 0), $p_0$),
      node((1, 0), $1$),
      node((2, 0), $2$),
      node((0, 1), $0$, name: <1>, stroke: 1pt),
      node((1, 1), $1$, name: <2>, stroke: 1pt),
      node((1, 4), $0$, name: <3>, stroke: 1pt),
      node((2, 1), $1$, name: <4>, stroke: 1pt),
      node((2, 2), $1$, name: <5>, stroke: 1pt),
      node((2, 3), $2$, name: <6>, stroke: 1pt),
      node((2, 4), $0$, name: <7>, stroke: 1pt),
      edge(<1>, <2>),
      edge(<1>, <3>, stroke: 2pt),
      edge(<2>, <4>),
      edge(<2>, <6>),
      edge(<3>, <5>),
      edge(<3>, <7>, stroke: 2pt),
      edge(<5>, <8>),
      edge(<7>, <9>, stroke: 2pt),

      node((3, 0), $p_1$),
      node((4, 0), $3$),
      node((5, 0), $4$),
      node((3, 1), $1$, name: <8>, stroke: 1pt),
      node((3, 2), $0$, name: <9>, stroke: 1pt),
      node((4, 1), $1$, name: <10>, stroke: 1pt),
      node((4, 2), $0$, name: <11>, stroke: 1pt),
      node((4, 3), $1$, name: <12>, stroke: 1pt),
      node((4, 4), $2$, name: <13>, stroke: 1pt),
      node((5, 1), $1$, name: <14>, stroke: 1pt),
      node((5, 2), $1$, name: <15>, stroke: 1pt),
      node((5, 3), $1$, name: <16>, stroke: 1pt),
      node((5, 4), $0$, name: <17>, stroke: 1pt),
      edge(<8>, <10>),
      edge(<8>, <13>),
      edge(<9>, <11>),
      edge(<9>, <12>, stroke: 2pt),
      edge(<10>, <14>, "--"),
      edge(<10>, <16>),
      edge(<11>, <15>),
      edge(<11>, <17>),
      edge(<12>, <14>, stroke: 2pt),
      edge(<12>, <16>, "--"),
      edge(<13>, <15>, "--"),
      edge(<13>, <17>, "--"),
      edge(<14>, <18>, stroke: 2pt),

      node((6, 0), $p_2$),
      node((7, 0), $5$),
      node((8, 0), $6$),
      node((6, 1), $1$, name: <18>, stroke: 1pt),
      node((6, 2), $1$, name: <19>, stroke: 1pt),
      node((7, 1), $2$, name: <20>, stroke: 1pt),
      node((7, 2), $2$, name: <21>, stroke: 1pt),
      node((7, 3), $1$, name: <22>, stroke: 1pt),
      node((7, 4), $1$, name: <23>, stroke: 1pt),
      node((8, 1), $2$, name: <24>, stroke: 1pt),
      node((8, 2), $2$, name: <25>, stroke: 1pt),
      node((8, 3), $1$, name: <26>, stroke: 1pt),
      node((8, 4), $1$, name: <27>, stroke: 1pt),
      edge(<18>, <23>, stroke: 2pt),
      edge(<23>, <27>, stroke: 2pt),
      edge(<27>, <29>, stroke: 2pt),

      node((9, 0), $p_3$),
      node((10, 0), $7$),
      node((11, 0), $8$),
      node((9, 1), $2$, name: <28>, stroke: 1pt),
      node((9, 2), $1$, name: <29>, stroke: 1pt),
      node((10, 1), $3$, name: <30>, stroke: 1pt),
      node((10, 2), $2$, name: <31>, stroke: 1pt),
      node((10, 3), $1$, name: <32>, stroke: 1pt),
      node((10, 4), $2$, name: <33>, stroke: 1pt),
      node((11, 1), $2$, name: <34>, stroke: 1pt),
      node((11, 2), $2$, name: <35>, stroke: 1pt),
      node((11, 3), $1$, name: <36>, stroke: 1pt),
      node((11, 4), $2$, name: <37>, stroke: 1pt),
      edge(<29>, <31>, stroke: 2pt),
      edge(<31>, <35>, stroke: 2pt),
      edge(<35>, <38>, stroke: 2pt),

      node((12, 0), $p_4$),
      node((12, 1), $2$, name: <38>, stroke: 1pt),
      node((12, 2), $2$, name: <39>, stroke: 1pt),

      node((-1, 6), "00"),
      node((-1, 7), "01"),
      node((-1, 8), "10"),
      node((-1, 9), "11"),

      node((0, 5), $p_4$),
      node((1, 5), $9$),
      node((2, 5), $10$),
      node((0, 6), $2$, name: <40>, stroke: 1pt),
      node((0, 7), $2$, name: <41>, stroke: 1pt),
      node((1, 6), $2$, name: <42>, stroke: 1pt),
      node((1, 7), $2$, name: <43>, stroke: 1pt),
      node((1, 8), $3$, name: <44>, stroke: 1pt),
      node((1, 9), $3$, name: <45>, stroke: 1pt),
      node((2, 6), $3$, name: <46>, stroke: 1pt),
      node((2, 7), $3$, name: <47>, stroke: 1pt),
      node((2, 8), $2$, name: <48>, stroke: 1pt),
      node((2, 9), $2$, name: <49>, stroke: 1pt),
      edge(<40>, <42>, stroke: 2pt),
      edge(<42>, <48>, stroke: 2pt),
      edge(<48>, <51>, stroke: 2pt),

      node((3, 5), $p_5$),
      node((4, 5), $11$),
      node((5, 5), $12$),
      node((3, 6), $3$, name: <50>, stroke: 1pt),
      node((3, 7), $2$, name: <51>, stroke: 1pt),
      node((4, 6), $4$, name: <52>, stroke: 1pt),
      node((4, 7), $3$, name: <53>, stroke: 1pt),
      node((4, 8), $2$, name: <54>, stroke: 1pt),
      node((4, 9), $3$, name: <55>, stroke: 1pt),
      node((5, 6), $3$, name: <56>, stroke: 1pt),
      node((5, 7), $3$, name: <57>, stroke: 1pt),
      node((5, 8), $2$, name: <58>, stroke: 1pt),
      node((5, 9), $3$, name: <59>, stroke: 1pt),
      edge(<51>, <53>, stroke: 2pt),
      edge(<53>, <57>, stroke: 2pt),
      edge(<57>, <60>, stroke: 2pt),

      node((6, 5), $p_6$),
      node((7, 5), $13$),
      node((8, 5), $14$),
      node((6, 6), $3$, name: <60>, stroke: 1pt),
      node((6, 7), $3$, name: <61>, stroke: 1pt),
      node((7, 6), $4$, name: <62>, stroke: 1pt),
      node((7, 7), $4$, name: <63>, stroke: 1pt),
      node((7, 8), $3$, name: <64>, stroke: 1pt),
      node((7, 9), $3$, name: <65>, stroke: 1pt),
      node((8, 6), $4$, name: <66>, stroke: 1pt),
      node((8, 7), $4$, name: <67>, stroke: 1pt),
      node((8, 8), $3$, name: <68>, stroke: 1pt),
      node((8, 9), $3$, name: <69>, stroke: 1pt),
      edge(<60>, <65>, stroke: 2pt),
      edge(<65>, <69>, stroke: 2pt),
      edge(<69>, <71>, stroke: 2pt),

      node((9, 5), $p_7$),
      node((10, 5), $15$),
      node((11, 5), $16$),
      node((9, 6), $4$, name: <70>, stroke: 1pt),
      node((9, 7), $3$, name: <71>, stroke: 1pt),
      node((10, 6), $3$, name: <72>, stroke: 1pt),
      node((10, 7), $4$, name: <73>, stroke: 1pt),
      node((11, 6), $3$, name: <74>, stroke: 1pt),
      node((11, 7), $4$, name: <75>, stroke: 1pt),
      edge(<71>, <73>, stroke: 2pt),
      edge(<73>, <75>, stroke: 2pt),
      edge(<75>, <76>, stroke: 2pt),

      node((12, 5), $p_8$),
      node((12, 6), $4$, name: <76>, stroke: 1pt),
    ),
  )

  得 $y = 1011100001001000$，代价为 $4$．
]