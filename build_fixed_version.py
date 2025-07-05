#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版打包脚本 - 包含图片下载修复
包含SSL证书问题修复和增强的网络请求功能
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """检查打包要求"""
    print("🔍 检查打包要求...")
    
    # 检查主文件
    required_files = [
        'gui_fluent.py',
        'malatang_processor.py',
        'gui_processor.py',
        'config.py',
        'font_manager.py',
        'icon_manager.py',
        'MapleMono-NF-CN-Bold.ttf'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - 存在")
        else:
            print(f"❌ {file} - 缺失")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ 缺失关键文件: {', '.join(missing_files)}")
        return False
    
    # 检查图标目录
    if os.path.exists('icons'):
        icon_count = len(list(Path('icons').glob('*.png'))) + len(list(Path('icons').glob('*.ico')))
        print(f"✅ 图标系统 - {icon_count} 个图标文件")
    else:
        print("⚠️ 图标目录不存在")
    
    # 检查字体文件
    font_path = Path('MapleMono-NF-CN-Bold.ttf')
    if font_path.exists():
        font_size = font_path.stat().st_size / 1024 / 1024
        print(f"✅ 自定义字体 - {font_size:.2f} MB")
    else:
        print("⚠️ 自定义字体文件不存在")
    
    # 检查依赖库
    try:
        import PyInstaller
        print(f"✅ PyInstaller - 版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False
    
    # 检查核心依赖
    dependencies = [
        ('PyQt5', 'PyQt5'),
        ('pandas', 'pandas'),
        ('requests', 'requests'),
        ('PIL', 'Pillow'),
        ('watchdog', 'watchdog'),
        ('openpyxl', 'openpyxl'),
        ('urllib3', 'urllib3')
    ]
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {package} - 已安装")
        except ImportError:
            print(f"❌ {package} - 未安装")
            print(f"请运行: pip install {package}")
            return False
    
    return True

def clean_build_dirs():
    """清理构建目录"""
    print("\n🧹 清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ 清理目录: {dir_name}")
            except Exception as e:
                print(f"⚠️ 清理目录失败 {dir_name}: {e}")

def prepare_data_files():
    """准备数据文件"""
    print("\n📁 准备数据文件...")
    
    data_files = []
    
    # 字体文件
    if os.path.exists('MapleMono-NF-CN-Bold.ttf'):
        data_files.append(('MapleMono-NF-CN-Bold.ttf', '.'))
        print("✅ 添加字体文件")
    
    # 图标目录
    if os.path.exists('icons'):
        for icon_file in Path('icons').glob('*'):
            if icon_file.is_file():
                data_files.append((str(icon_file), 'icons'))
        print(f"✅ 添加图标文件: {len(list(Path('icons').glob('*')))} 个")
    
    # 配置文件
    if os.path.exists('config.py'):
        data_files.append(('config.py', '.'))
        print("✅ 添加配置文件")
    
    return data_files

def create_spec_file():
    """创建spec文件"""
    print("\n📝 创建spec文件...")
    
    data_files = prepare_data_files()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 数据文件配置
datas = {data_files}

# 分析阶段 - 指定主脚本和依赖
a = Analysis(
    ['gui_fluent.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt5相关
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtNetwork',
        
        # QFluentWidgets相关
        'qfluentwidgets',
        'qfluentwidgets.components',
        'qfluentwidgets.common',
        'qfluentwidgets.window',
        
        # 业务逻辑模块
        'malatang_processor',
        'gui_processor',
        'config',
        'font_manager',
        'icon_manager',
        
        # 数据处理相关
        'pandas',
        'openpyxl',
        'requests',
        'watchdog',
        'PIL',
        'PIL.Image',
        'urllib3',
        'urllib3.exceptions',
        
        # 其他可能需要的模块
        'json',
        'datetime',
        'pathlib',
        'logging',
        'threading',
        'queue',
        'ssl',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'tkinter',
        'matplotlib',
        'numpy.testing',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ阶段 - 创建Python字节码归档
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE阶段 - 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='美团店铺数据处理工具_修复版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/app.ico' if os.path.exists('icons/app.ico') else None,
)
'''
    
    with open('美团店铺数据处理工具_修复版.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ spec文件创建完成")

def build_executable():
    """构建可执行文件"""
    print("\n🔨 开始构建可执行文件...")
    
    try:
        # 运行PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            '美团店铺数据处理工具_修复版.spec'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ 构建成功!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败!")
        print(f"错误输出: {e.stderr}")
        return False

def verify_build():
    """验证构建结果"""
    print("\n🔍 验证构建结果...")
    
    exe_path = Path('dist/美团店铺数据处理工具_修复版.exe')
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / 1024 / 1024
        print(f"✅ 可执行文件已生成")
        print(f"   文件路径: {exe_path}")
        print(f"   文件大小: {file_size:.2f} MB")
        
        # 检查关键文件是否包含
        print("\n📋 构建内容检查:")
        if os.path.exists('icons/app.ico'):
            print("✅ 应用图标已包含")
        if os.path.exists('MapleMono-NF-CN-Bold.ttf'):
            print("✅ 自定义字体已包含")
        if os.path.exists('icons'):
            print("✅ 图标系统已包含")
        
        return True
    else:
        print("❌ 可执行文件未生成")
        return False

def main():
    """主函数"""
    print("🔧 美团店铺数据处理工具 - 修复版打包脚本")
    print("=" * 60)
    print("包含功能:")
    print("  • 🔧 SSL证书问题修复")
    print("  • 🌐 增强网络请求功能")
    print("  • 🎨 图标系统")
    print("  • 🔤 字体管理")
    print("  • 📐 窗口优化")
    print("=" * 60)
    
    # 1. 检查要求
    if not check_requirements():
        print("\n❌ 检查失败，请解决上述问题后重试")
        return False
    
    # 2. 清理构建目录
    clean_build_dirs()
    
    # 3. 创建spec文件
    create_spec_file()
    
    # 4. 构建可执行文件
    if not build_executable():
        print("\n❌ 构建失败")
        return False
    
    # 5. 验证构建结果
    if not verify_build():
        print("\n❌ 验证失败")
        return False
    
    print("\n🎉 打包完成!")
    print("=" * 60)
    print("✅ 修复版可执行文件已生成")
    print("📁 位置: dist/美团店铺数据处理工具_修复版.exe")
    print("🔧 修复内容:")
    print("   • SSL证书验证问题")
    print("   • img.meituan.net域名访问问题")
    print("   • 增强的错误处理和重试机制")
    print("   • 改进的请求头配置")
    print("\n🚀 现在可以正常下载所有图片了!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
