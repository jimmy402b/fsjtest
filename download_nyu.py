#!/usr/bin/env python
"""
NYU Depth V2 数据集下载和验证脚本
自动下载、验证和设置 NYU 数据
"""

import os
import sys
import h5py
from pathlib import Path

try:
    import requests
except ImportError:
    print("⚠️  需要 requests 库。运行：pip install requests")
    sys.exit(1)


def setup_data_directory():
    """创建 data 目录"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def check_file_exists(file_path):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        size_gb = os.path.getsize(file_path) / (1024**3)
        return True, size_gb
    return False, 0


def verify_mat_file(file_path):
    """验证 MAT 文件的完整性和格式"""
    try:
        with h5py.File(file_path, 'r') as f:
            required_keys = ['images', 'depths']
            has_required = all(key in f.keys() for key in required_keys)
            
            if not has_required:
                return False, "缺少必要数据集"
            
            images_shape = f['images'].shape
            depths_shape = f['depths'].shape
            
            # 验证形状
            if images_shape[0] != 3:  # RGB 通道
                return False, f"RGB 通道数错误: {images_shape[0]}"
            
            if images_shape[1] != 480 or images_shape[2] != 640:
                return False, f"图像分辨率错误: {images_shape[1]}x{images_shape[2]}"
            
            if depths_shape[0] != 480 or depths_shape[1] != 640:
                return False, f"深度分辨率错误: {depths_shape[0]}x{depths_shape[1]}"
            
            num_samples = images_shape[3]
            
            return True, f"✓ 数据有效 ({num_samples} 个样本)"
    
    except Exception as e:
        return False, str(e)


def download_file(url, output_path, chunk_size=8192):
    """下载文件，显示进度条"""
    print(f"\n📥 开始下载: {url}")
    print(f"   目标: {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=3600)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        if total_size == 0:
            print("⚠️  无法获取文件大小，继续下载...")
        
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024**2)
                        mb_total = total_size / (1024**2)
                        print(f"   进度: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='\r')
        
        print(f"\n✓ 下载完成: {output_path}")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"✗ 下载失败: {e}")
        return False


def main():
    """主函数"""
    print("="*70)
    print("  NYU Depth V2 数据集 - 下载和验证工具")
    print("="*70)
    
    # 设置目录
    data_dir = setup_data_directory()
    mat_path = data_dir / "nyu_depth_v2_labeled.mat"
    
    print(f"\n📁 数据目录: {data_dir.absolute()}")
    
    # 检查文件是否已存在
    exists, size_gb = check_file_exists(mat_path)
    
    if exists:
        print(f"\n✓ 文件已存在: {mat_path}")
        print(f"  大小: {size_gb:.2f} GB")
        
        # 验证文件
        print("\n🔍 验证文件完整性...")
        is_valid, msg = verify_mat_file(mat_path)
        
        if is_valid:
            print(f"✓ {msg}")
            print("\n✨ 数据已准备就绪！")
            return 0
        else:
            print(f"✗ 文件验证失败: {msg}")
            print("   建议重新下载...")
            response = input("\n是否删除并重新下载? (y/n): ")
            if response.lower() != 'y':
                return 1
            mat_path.unlink()
    
    # 下载文件
    print("\n📥 需要下载 NYU Depth V2 数据集")
    print("   大小: ~2.6 GB")
    print("   时间: 视网络速度而定（10-30 分钟）")
    
    response = input("\n是否继续下载? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return 1
    
    # 选择下载源
    print("\n下载源选择:")
    print("1. GitHub (推荐)")
    print("2. 官方 NYU 服务器")
    
    source = input("选择下载源 (1/2): ")
    
    if source == '2':
        url = "http://cs.nyu.edu/~silberman/datasets/nyu_depth_v2_labeled.zip"
        print("⚠️  下载的是 ZIP 文件，需要手动解压")
    else:
        url = "https://github.com/KendrickLamarJ/NYU_Depth_V2/raw/master/nyu_depth_v2_labeled.mat"
    
    # 下载
    if not download_file(url, str(mat_path)):
        print("❌ 下载失败，请稍后重试")
        return 1
    
    # 验证下载的文件
    print("\n🔍 验证下载的文件...")
    is_valid, msg = verify_mat_file(mat_path)
    
    if is_valid:
        print(f"✓ {msg}")
        print("\n✨ NYU 数据已准备就绪！")
        print(f"\n可以运行以下命令进行实验：")
        print(f"\npython run_minimal_poc.py \\")
        print(f"  --data nyu \\")
        print(f"  --nyu_mat {mat_path} \\")
        print(f"  --num_samples 50 \\")
        print(f"  --out_dir results/nyu_full")
        return 0
    else:
        print(f"✗ 文件验证失败: {msg}")
        print("❌ 下载或文件可能损坏，请重新尝试")
        return 1


if __name__ == '__main__':
    sys.exit(main())
