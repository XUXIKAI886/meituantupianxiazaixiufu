#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标管理器
统一管理应用中的所有图标资源
"""

import os
from pathlib import Path
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

class IconManager:
    """图标管理器类"""
    
    def __init__(self):
        self.icons_dir = Path("icons")
        self._icon_cache = {}
        
        # 确保图标目录存在
        if not self.icons_dir.exists():
            print("⚠️ 图标目录不存在，正在创建...")
            self.icons_dir.mkdir(exist_ok=True)
    
    def get_icon(self, icon_name, size=None):
        """获取图标
        
        Args:
            icon_name: 图标名称 (如 'app', 'status_completed', 'button_play')
            size: 图标尺寸 (如 24, 32, 48)，None表示使用默认尺寸
            
        Returns:
            QIcon对象
        """
        # 构建缓存键
        cache_key = f"{icon_name}_{size}" if size else icon_name
        
        # 检查缓存
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        # 查找图标文件
        icon_path = self._find_icon_file(icon_name, size)
        
        if icon_path and icon_path.exists():
            icon = QIcon(str(icon_path))
            self._icon_cache[cache_key] = icon
            return icon
        else:
            # 返回默认图标或空图标
            print(f"⚠️ 图标文件未找到: {icon_name} (size: {size})")
            return QIcon()
    
    def get_pixmap(self, icon_name, size=None, target_size=None):
        """获取图标的Pixmap
        
        Args:
            icon_name: 图标名称
            size: 原始图标尺寸
            target_size: 目标显示尺寸 (width, height)
            
        Returns:
            QPixmap对象
        """
        icon_path = self._find_icon_file(icon_name, size)
        
        if icon_path and icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            
            if target_size:
                width, height = target_size
                pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            return pixmap
        else:
            print(f"⚠️ 图标文件未找到: {icon_name} (size: {size})")
            return QPixmap()
    
    def _find_icon_file(self, icon_name, size=None):
        """查找图标文件路径"""
        # 如果指定了尺寸，优先查找对应尺寸的文件
        if size:
            size_specific_path = self.icons_dir / f"{icon_name}_{size}x{size}.png"
            if size_specific_path.exists():
                return size_specific_path
        
        # 查找通用文件
        generic_path = self.icons_dir / f"{icon_name}.png"
        if generic_path.exists():
            return generic_path
        
        # 查找ICO文件（主要用于应用图标）
        ico_path = self.icons_dir / f"{icon_name}.ico"
        if ico_path.exists():
            return ico_path
        
        # 尝试查找最大尺寸的PNG文件
        for test_size in [256, 128, 64, 48, 32, 24, 16]:
            test_path = self.icons_dir / f"{icon_name}_{test_size}x{test_size}.png"
            if test_path.exists():
                return test_path
        
        return None
    
    def get_app_icon(self):
        """获取应用主图标"""
        return self.get_icon("app")
    
    def get_status_icon(self, status_type, size=24):
        """获取状态图标
        
        Args:
            status_type: 状态类型 ('completed', 'download', 'success_rate')
            size: 图标尺寸
        """
        return self.get_icon(f"status_{status_type}", size)
    
    def get_button_icon(self, button_type, size=24):
        """获取按钮图标
        
        Args:
            button_type: 按钮类型 ('play', 'stop', 'folder', 'delete')
            size: 图标尺寸
        """
        return self.get_icon(f"button_{button_type}", size)
    
    def list_available_icons(self):
        """列出所有可用的图标"""
        icons = {}
        
        for icon_file in self.icons_dir.glob("*.png"):
            name = icon_file.stem
            if name not in icons:
                icons[name] = []
            icons[name].append(icon_file.name)
        
        for icon_file in self.icons_dir.glob("*.ico"):
            name = icon_file.stem
            if name not in icons:
                icons[name] = []
            icons[name].append(icon_file.name)
        
        return icons
    
    def verify_icons(self):
        """验证图标文件完整性"""
        print("🔍 验证图标文件...")
        
        required_icons = {
            'app': ['ico', 'png'],
            'status_completed': ['24x24', '32x32', '48x48'],
            'status_download': ['24x24', '32x32', '48x48'],
            'status_success_rate': ['24x24', '32x32', '48x48'],
            'button_play': ['16x16', '24x24', '32x32'],
            'button_stop': ['16x16', '24x24', '32x32'],
            'button_folder': ['16x16', '24x24', '32x32'],
            'button_delete': ['16x16', '24x24', '32x32'],
        }
        
        missing_icons = []
        
        for icon_name, required_sizes in required_icons.items():
            for size_info in required_sizes:
                if size_info in ['ico', 'png']:
                    icon_path = self.icons_dir / f"{icon_name}.{size_info}"
                else:
                    icon_path = self.icons_dir / f"{icon_name}_{size_info}.png"
                
                if not icon_path.exists():
                    missing_icons.append(str(icon_path))
                else:
                    print(f"  ✅ {icon_path.name}")
        
        if missing_icons:
            print("❌ 缺失的图标文件:")
            for missing in missing_icons:
                print(f"  - {missing}")
            return False
        else:
            print("✅ 所有图标文件完整!")
            return True

# 全局图标管理器实例
icon_manager = IconManager()

def get_icon(icon_name, size=None):
    """便捷函数：获取图标"""
    return icon_manager.get_icon(icon_name, size)

def get_pixmap(icon_name, size=None, target_size=None):
    """便捷函数：获取Pixmap"""
    return icon_manager.get_pixmap(icon_name, size, target_size)

def get_app_icon():
    """便捷函数：获取应用图标"""
    return icon_manager.get_app_icon()

def get_status_icon(status_type, size=24):
    """便捷函数：获取状态图标"""
    return icon_manager.get_status_icon(status_type, size)

def get_button_icon(button_type, size=24):
    """便捷函数：获取按钮图标"""
    return icon_manager.get_button_icon(button_type, size)

if __name__ == "__main__":
    # 测试图标管理器
    print("🎯 图标管理器测试")
    print("=" * 40)
    
    manager = IconManager()
    
    # 验证图标
    manager.verify_icons()
    
    # 列出可用图标
    print("\n📁 可用图标:")
    icons = manager.list_available_icons()
    for name, files in icons.items():
        print(f"  {name}: {', '.join(files)}")
    
    print("\n✅ 图标管理器测试完成")
