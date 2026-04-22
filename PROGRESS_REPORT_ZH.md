# 深度图精修 PoC 阶段说明（截至 2026-04-22）

## 1. 到目前为止做了什么

本项目围绕论文题目“面向考古现场三维建模的深度图精修算法研究”，已完成一套可运行的 PoC 管线，包含以下模块：

1. 数据模块
- 合成数据生成（可控几何场景 + RGB 纹理）
- NYU Depth V2 数据加载（HDF5 .mat）
- NYU 维度兼容适配（支持多种常见排列）

2. 退化模拟模块
- 高斯噪声
- 深度相关噪声
- 随机空洞
- 边缘空洞
- 混合退化流程

3. 深度修复方法
- input_filled（补洞基线）
- median_filter（中值滤波）
- bilateral_filter（双边滤波）
- guided_filter（引导滤波）
- fixed_fractional（固定阶分数阶）
- adaptive_fractional（自适应阶分数阶，核心创新方向）

4. 评估与可视化
- 深度指标：RMSE、MAE、AbsRel、PSNR、SSIM、Edge_RMSE
- 点云指标：Chamfer、OutlierRatio
- 自动输出：metrics.csv、metrics_mean.csv、summary.md、figures/ 对比图

5. 工程化修复
- 修复 Windows 编码写文件问题（UTF-8）
- 修复 NYU 读取维度与方向兼容问题
- 修复分数阶卷积的掩码归一化数值放大问题
- 将分数阶参数开放为命令行参数，支持系统调参实验

## 2. 各次关键实验结果

说明：以下重点展示 RMSE（越小越好），并结合 Edge_RMSE、Chamfer 做边界与几何参考。

### 实验 A：Synthetic 20 样本（基线阶段）
来源：results/full_poc/summary.md

- median_filter：RMSE 0.0509（最优）
- bilateral_filter：RMSE 0.0790
- guided_filter：RMSE 0.1555
- adaptive_fractional：RMSE 1.7025
- fixed_fractional：RMSE 1.8527

结论：
- 自适应分数阶优于固定分数阶（方向有效）
- 但分数阶整体明显落后于传统方法

### 实验 B：NYU 20 样本（真实数据初测）
来源：results/nyu_poc/summary.md

- median_filter：RMSE 0.0468（最优）
- bilateral_filter：RMSE 0.0651
- guided_filter：RMSE 0.1329
- adaptive_fractional：RMSE 5.4214
- fixed_fractional：RMSE 5.7692

结论：
- 真实数据上同样是 adaptive > fixed
- 但分数阶绝对误差异常偏大，怀疑实现层面存在数值问题

### 实验 C：NYU 300 样本（放大验证，修复前）
来源：results/nyu_large_300/summary.md

- 排名（RMSE）：median < bilateral ≈ input_filled < guided << adaptive < fixed
- adaptive_fractional：RMSE 5.6524
- fixed_fractional：RMSE 6.0153

结论：
- 结果趋势稳定，但分数阶绝对性能仍明显异常
- 进一步指向实现存在系统性问题

### 实验 D：NYU 1449 全量（修复前全量确认）
来源：results/nyu_full_1449/summary.md

- median_filter：RMSE 0.0444（最优）
- bilateral_filter：RMSE 0.0626
- guided_filter：RMSE 0.1205
- adaptive_fractional：RMSE 5.0710
- fixed_fractional：RMSE 5.4147

结论：
- 全量数据仍复现“adaptive > fixed，但远弱于传统法”
- 说明问题并非样本偶然，而是方法实现层面的稳定缺陷

### 实验 E：NYU 300 样本（改造后）
来源：results/nyu_tuned_300/summary.md
参数：
- fixed: alpha=0.25, radius=3, iterations=1
- adaptive: alpha_min=0.05, alpha_max=0.35, radius=3, iterations=1

结果：
- median_filter：RMSE 0.0492（最优）
- adaptive_fractional：RMSE 0.0613（第 2）
- fixed_fractional：RMSE 0.0615（第 3）
- bilateral_filter：RMSE 0.0675
- guided_filter：RMSE 0.1337

与修复前（实验 C）相比：
- adaptive RMSE 从 5.6524 降至 0.0613（约 -98.9%）
- fixed RMSE 从 6.0153 降至 0.0615（约 -99.0%）
- Edge_RMSE、Chamfer 同步大幅改善

结论：
- 先前分数阶性能异常的核心原因已定位并修复
- 修复后分数阶进入可竞争区间，已优于 bilateral 与 guided
- 当前仍未超过 median_filter（约落后 24.5%）

## 3. 目前可以下的结论

1. 研究方向层面
- 自适应分数阶策略在“分数阶家族内部”持续优于固定分数阶，方向成立。

2. 工程实现层面
- 修复掩码归一化后，分数阶性能从异常区间恢复到合理区间，证明此前主要是实现问题而非理论问题。

3. 与传统方法对比
- 改造后已超过 bilateral 与 guided。
- 目前最佳仍是 median_filter。
- 因此当前可表述为：分数阶方法已具备竞争力，但尚未取得全局最优。

## 4. 下一步修正方向（按优先级）

1. 自适应策略强化
- 优化 alpha_map 生成逻辑（更强的边界置信与纹理抑制）
- 尝试分段映射或非线性映射替代当前线性映射

2. 参数系统搜索
- 在 NYU 300 样本上做网格搜索（alpha_min、alpha_max、radius、iterations）
- 目标：在 RMSE 与 Edge_RMSE 双指标上逼近或超过 median

3. 稳定性与泛化
- 在 NYU 全量再次复验最优参数
- 增加不同退化强度下的稳健性对比曲线

4. 论文产出准备
- 固化实验协议与随机种子
- 形成可复现实验表格与图示
- 明确“方向有效、实现迭代后接近传统最优”的阶段性结论

## 5. 本阶段产出文件

- 代码改动
  - run_minimal_poc.py
  - src/data_loader.py
  - src/fractional.py
- 新增脚本与说明
  - download_nyu.py
  - NYU_DOWNLOAD_GUIDE.md
  - view_results.html
  - PROGRESS_REPORT_ZH.md
- 代表性结果目录
  - results/full_poc
  - results/nyu_poc
  - results/nyu_large_300
  - results/nyu_full_1449
  - results/nyu_tuned_300

以上内容可作为当前阶段汇报与后续论文实验章节的基础材料。
