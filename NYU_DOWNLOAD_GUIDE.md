# NYU Depth V2 数据集使用指南

## 📥 下载步骤

### 方式 1：直接下载（推荐 - 最快）

```bash
# 进入项目的 data 文件夹
cd z:\FSJTry\minimal_depth_refine_poc\data

# 使用 Python 直接下载（推荐）
python -m urllib.request \\
  "https://github.com/KendrickLamarJ/NYU_Depth_V2/raw/master/nyu_depth_v2_labeled.mat" \\
  -O nyu_depth_v2_labeled.mat

# 或使用 curl
curl -L -o nyu_depth_v2_labeled.mat \\
  "https://github.com/KendrickLamarJ/NYU_Depth_V2/raw/master/nyu_depth_v2_labeled.mat"
```

### 方式 2：通过浏览器下载

1. **访问下载链接：**
   ```
   http://cs.nyu.edu/~silberman/datasets/nyu_depth_v2_labeled.zip
   ```

2. **下载 ZIP 文件** (~2.7 GB)

3. **解压：**
   ```bash
   # 使用 7-Zip、WinRAR 等工具
   # 或 PowerShell：
   Expand-Archive -Path nyu_depth_v2_labeled.zip -DestinationPath data/
   
   # 或 Python：
   import zipfile
   zipfile.ZipFile('nyu_depth_v2_labeled.zip').extractall('data/')
   ```

4. **确保文件在正确位置：**
   ```
   data/nyu_depth_v2_labeled.mat
   ```

### 方式 3：通过 Git LFS 克隆（适合开发者）

```bash
# 如果仓库使用了 Git LFS
git lfs install
git clone https://github.com/datasets/nyu-depth-v2.git data/
```

---

## ✅ 验证下载完成

### 检查文件大小

```bash
# PowerShell
(Get-Item data/nyu_depth_v2_labeled.mat).Length / 1GB

# 预期大小：~2.6 GB
```

### 验证文件完整性

```python
import h5py
import os

mat_path = 'data/nyu_depth_v2_labeled.mat'

# 检查文件是否存在
if os.path.exists(mat_path):
    print(f"✓ 文件存在")
    print(f"  大小: {os.path.getsize(mat_path) / 1e9:.2f} GB")
    
    # 检查内容
    try:
        with h5py.File(mat_path, 'r') as f:
            print(f"✓ 文件有效 (MATLAB格式)")
            print(f"  包含的数据：")
            for key in f.keys():
                shape = f[key].shape
                print(f"    - {key}: {shape}")
    except Exception as e:
        print(f"✗ 文件损坏或格式不正确: {e}")
else:
    print(f"✗ 文件不存在: {mat_path}")
```

---

## 🚀 使用 NYU 数据运行实验

### 运行命令

```bash
# 确保虚拟环境已激活
# (venv) PS> ...

# 使用 NYU 数据运行完整实验
python run_minimal_poc.py \
  --data nyu \
  --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 50 \
  --height 240 \
  --width 320 \
  --out_dir results/nyu_full \
  --seed 42
```

### 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--data` | `nyu` | 使用 NYU 数据 |
| `--nyu_mat` | 路径 | .mat 文件位置 |
| `--num_samples` | 50 | 处理 50 个样本（最多 1449） |
| `--height` | 240 | 缩放高度（NYU 原始 480） |
| `--width` | 320 | 缩放宽度（NYU 原始 640） |
| `--out_dir` | 路径 | 输出目录 |
| `--seed` | 42 | 随机种子（可复现） |

### 运行示例

```bash
# 快速测试（10个样本）
python run_minimal_poc.py --data nyu --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 10 --out_dir results/nyu_quick

# 完整实验（100个样本）
python run_minimal_poc.py --data nyu --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 100 --out_dir results/nyu_full

# 高分辨率（480×640，需要更多时间和内存）
python run_minimal_poc.py --data nyu --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 50 --height 480 --width 640 --out_dir results/nyu_hires
```

---

## 📊 NYU 数据特性

### 数据统计

| 特性 | 值 |
|------|-----|
| **总样本数** | 1449 |
| **图像尺寸** | 640 × 480 |
| **原始深度范围** | 0 - 10000 mm |
| **采集设备** | Kinect v1 |
| **场景类型** | 室内 |
| **场景数量** | 407 个独特场景 |

### 典型场景

```
卧室、浴室、厨房、办公室、书房、走廊、客厅等
```

### 深度值处理

代码会自动处理：
- 将深度从 mm 转为 m（除以 1000）
- 移除无效的 0 值（设为 nan）
- 自动调整相机内参

### 相机内参

```python
# NYU 使用的相机参数已内置：
fx = 518.8579
fy = 519.4696
cx = 325.5824
cy = 253.7362
```

---

## ⚠️ 注意事项

### 文件大小

```
nyu_depth_v2_labeled.mat: ~2.6 GB
解压后：仍然是 ~2.6 GB（MAT 格式不压缩）
```

### 下载时间

```
快速网络（100 Mbps）：约 200+ 秒
慢速网络（10 Mbps）：约 2000+ 秒
```

**建议：**
- 使用有线网络或 WiFi 5G
- 留足可用磁盘空间
- 如果下载中断，可重新尝试（有些下载工具支持断点续传）

### 内存需求

```
处理 100 个 480×640 样本需要：
- 系统内存：~8-16 GB
- 显存（如果用GPU）：可选
- 磁盘空间：~10 GB（输出结果）
```

### 如果文件无法直接下载

**替代方案 1：通过 Google Drive**
```
某些镜像可能存储在 Google Drive 或 Dropbox
搜索：NYU Depth V2 Labeled Google Drive
```

**替代方案 2：通过 Kaggle**
```
https://www.kaggle.com/datasets/soumikraychaudhuri/nyu-depth-v2
```

**替代方案 3：通过 AWS S3**
```
某些组织维护的公共 S3 桶中可能有镜像
```

---

## 🔍 文件格式验证

### 查看 MAT 文件内容

```python
import h5py

# 打开 MAT 文件
with h5py.File('data/nyu_depth_v2_labeled.mat', 'r') as f:
    # 查看所有键
    print("可用的数据集：")
    for key in f.keys():
        data = f[key]
        print(f"  {key}: {data.shape} {data.dtype}")
    
    # 查看图像
    images = f['images']  # (3, 480, 640, 1449)
    print(f"\n图像数据：{images.shape}")
    
    # 查看深度
    depths = f['depths']  # (480, 640, 1449)
    print(f"深度数据：{depths.shape}")
    
    # 读取一个样本
    sample_idx = 0
    img = images[:, :, :, sample_idx]  # (3, 480, 640)
    depth = depths[:, :, sample_idx]   # (480, 640)
    
    print(f"\n样本 {sample_idx}:")
    print(f"  RGB: {img.shape} {img.dtype}")
    print(f"  Depth: {depth.shape} {depth.dtype} 范围 [{depth.min()}, {depth.max()}]")
```

---

## 📋 故障排除

### 问题 1：下载失败 / 超时

```bash
# 使用 Python requests 库（支持代理和超时）
python
import requests

url = "https://github.com/KendrickLamarJ/NYU_Depth_V2/raw/master/nyu_depth_v2_labeled.mat"
response = requests.get(url, timeout=3600)  # 1小时超时

with open('data/nyu_depth_v2_labeled.mat', 'wb') as f:
    f.write(response.content)
    
print("下载完成")
```

### 问题 2：内存不足

```bash
# 使用较少的样本
python run_minimal_poc.py --data nyu --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 20 --height 120 --width 160 --out_dir results/nyu_low_res
```

### 问题 3：文件损坏

```bash
# 删除旧文件并重新下载
rm data/nyu_depth_v2_labeled.mat  # 或在 Windows 中手动删除

# 重新下载...
```

### 问题 4：代码找不到文件

```bash
# 确认文件路径
python -c "import os; print(os.path.exists('data/nyu_depth_v2_labeled.mat'))"

# 如果返回 False，检查：
# 1. 文件是否真的存在
# 2. 当前工作目录是否正确
# 3. 路径分隔符（Windows 用 \ 或 /）
```

---

## 🎯 完整工作流示例

```bash
# 1. 导航到项目目录
cd z:\FSJTry\minimal_depth_refine_poc

# 2. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 3. 确认文件存在（如果尚未下载）
python -c "import os; print('✓' if os.path.exists('data/nyu_depth_v2_labeled.mat') else '✗ 文件不存在')"

# 如果不存在，下载文件
# （见上面的下载步骤）

# 4. 运行实验
python run_minimal_poc.py \
  --data nyu \
  --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 50 \
  --out_dir results/nyu_experiment

# 5. 查看结果
# results/nyu_experiment/
#   ├── figures/
#   ├── metrics.csv
#   ├── metrics_mean.csv
#   └── summary.md
```

---

## 📚 参考文献

**NYU Depth V2 原始论文：**
```
@inproceedings{silberman2012indoor,
  title={Indoor segmentation and support inference from RGBD images},
  author={Silberman, Nathan and Hoiem, Derek and Kohli, Pushmeet and Fergus, Rob},
  booktitle={ECCV},
  year={2012}
}
```

**官方页面：**
```
http://cs.nyu.edu/~silberman/datasets/nyu_depth_v2_labeled.zip
https://github.com/cvlab-nyu/depthlab
```

---

有任何问题，可以：
1. 检查 `data/` 文件夹中的 `README.md`
2. 查看 `src/data_loader.py` 中的 `load_nyu_depth_v2()` 函数
3. 运行验证脚本（见上面的代码示例）
