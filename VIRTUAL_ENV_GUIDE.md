# Virtual Environment Guide

## 为什么使用虚拟环境？

### 问题：全局安装依赖的风险

当你运行 `pip install numpy` 时（不在虚拟环境中），包会被安装到系统Python中：

```
C:\Python39\
├── Lib\site-packages\
│   ├── numpy\          ← 全局安装，所有项目共享
│   ├── cv2\
│   └── ...
```

**潜在问题：**
- 项目A需要 numpy 1.20，项目B需要 numpy 1.25 → 冲突
- 升级一个库可能破坏其他项目
- 依赖难以追踪和复现
- 卸载库时可能误删其他项目依赖

### 解决方案：虚拟环境

虚拟环境为每个项目创建**隔离的Python环境**：

```
minimal_depth_refine_poc/
├── venv/
│   ├── Lib\site-packages\
│   │   ├── numpy\      ← 项目专用
│   │   ├── cv2\
│   │   └── ...
│   └── ...
├── src/
├── run_minimal_poc.py
└── ...

another_project/
├── venv/
│   ├── Lib\site-packages\
│   │   ├── numpy\      ← 不同版本，互不影响
│   │   └── ...
│   └── ...
└── ...
```

## 清理全局安装

如果已经用 `pip install numpy` 在系统中安装了，可以卸载：

```bash
# 卸载全局numpy
pip uninstall numpy

# 卸载其他已全局安装的包
pip uninstall opencv-python scipy scikit-image open3d matplotlib pandas tqdm h5py

# 列出所有全局安装的包
pip list

# 生成当前环境的requirements
pip freeze > old_requirements.txt  # 备份
```

## 推荐工作流

### 项目隔离最佳实践

```bash
# 新项目时
cd my_project
python -m venv venv          # 创建虚拟环境
source venv/bin/activate     # 激活
pip install -r requirements.txt  # 安装项目依赖

# 开发、测试
python script.py

# 完成后
deactivate                   # 停用虚拟环境

# 下次使用
source venv/bin/activate     # 重新激活
# ... 开发 ...
deactivate
```

### 与Git协作

虚拟环境**不要**提交到版本控制：

```bash
# .gitignore 文件中：
venv/
env/
ENV/

# 但需要提交 requirements.txt：
# 这样其他人可以快速复现环境
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
```

**同事想使用你的项目：**
```bash
git clone your_repo
cd your_repo
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # 快速复现环境
```

## 本项目的虚拟环境

### 快速设置

```bash
# Windows
.\setup_venv.bat

# Linux/macOS
chmod +x setup_venv.sh
./setup_venv.sh
```

### 手动设置

```bash
# 1. 创建
python -m venv venv

# 2. 激活
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# Linux/macOS:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证
python -c "import numpy, cv2, scipy; print('OK')"

# 5. 使用
python run_minimal_poc.py ...

# 6. 完成后停用
deactivate
```

## 常见问题

### Q: 为什么虚拟环境后需要重新激活？

A: 每次打开新的终端/PowerShell窗口时，虚拟环境都会被停用（回到系统Python）。需要在终端中重新运行激活命令。

### Q: 虚拟环境占用多少空间？

A: 通常 200-500MB（取决于依赖）。venv/ 目录应该加入 .gitignore，不提交到仓库。

### Q: 能删除虚拟环境吗？

A: 可以。直接删除 venv/ 目录即可：
```bash
rm -rf venv          # Linux/macOS
rmdir /s venv        # Windows
```
然后可以重新创建。

### Q: 虚拟环境和系统Python的区别？

A: 虚拟环境中的 `pip install` 只影响该环境的 site-packages，不影响系统。但需要先激活虚拟环境。

### Q: 如何知道虚拟环境是否激活？

A: 看命令行提示符：
- 激活后：`(venv) C:\path\project>`
- 未激活：`C:\path\project>`

### Q: 能在虚拟环境中升级pip吗？

A: 可以，推荐在安装前升级：
```bash
python -m pip install --upgrade pip
```

## 高级用法

### 使用 requirements-dev.txt 分离开发依赖

```
# requirements.txt - 生产依赖
numpy>=1.21.0
opencv-python>=4.5.0
scipy>=1.7.0
...

# requirements-dev.txt - 开发工具
-r requirements.txt
pytest
black
flake8
```

安装：
```bash
pip install -r requirements-dev.txt
```

### 冻结特定版本

```bash
pip freeze > requirements-pinned.txt
```

这会记录下所有包的具体版本，保证完全复现。

### 多项目使用不同Python版本

```bash
# 项目A（Python 3.8）
python3.8 -m venv venv

# 项目B（Python 3.10）
python3.10 -m venv venv
```

## 参考资源

- [Python venv 官方文档](https://docs.python.org/3/library/venv.html)
- [pip 用户指南](https://pip.pypa.io/en/latest/user_guide/)
- [Virtualenv（更高级的虚拟环境工具）](https://virtualenv.pypa.io/)

---

**总结**：使用虚拟环境是Python开发的标准做法。本项目提供了快速设置脚本，强烈推荐使用虚拟环境来隔离项目依赖。
