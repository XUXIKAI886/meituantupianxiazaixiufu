#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体管理器
统一管理应用中的字体设置
"""

import os
from pathlib import Path
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QApplication

class FontManager:
    """字体管理器类"""

    def __init__(self):
        self.font_database = None
        self.custom_font_path = Path("MapleMono-NF-CN-Bold.ttf")
        self.custom_font_family = None
        self.default_font_size = 10
        self._font_loaded = False

        # 延迟加载字体，等待QApplication创建后再加载
    
    def _ensure_font_database(self):
        """确保字体数据库已初始化"""
        if self.font_database is None:
            # 检查是否有QApplication实例
            app = QApplication.instance()
            if app is None:
                print("⚠️ 需要先创建QApplication才能使用字体管理器")
                return False
            self.font_database = QFontDatabase()
        return True

    def load_custom_font(self):
        """加载自定义字体文件"""
        if self._font_loaded:
            return True

        if not self._ensure_font_database():
            return False

        if self.custom_font_path.exists():
            try:
                # 添加字体到字体数据库
                font_id = self.font_database.addApplicationFont(str(self.custom_font_path))

                if font_id != -1:
                    # 获取字体家族名称
                    font_families = self.font_database.applicationFontFamilies(font_id)
                    if font_families:
                        self.custom_font_family = font_families[0]
                        self._font_loaded = True
                        print(f"✅ 自定义字体加载成功: {self.custom_font_family}")
                        print(f"📁 字体文件路径: {self.custom_font_path.absolute()}")
                        return True
                    else:
                        print("⚠️ 无法获取字体家族名称")
                else:
                    print("⚠️ 字体文件加载失败")
            except Exception as e:
                print(f"❌ 字体加载异常: {e}")
        else:
            print(f"⚠️ 字体文件不存在: {self.custom_font_path.absolute()}")

        return False
    
    def get_font(self, size=None, weight=QFont.Normal, italic=False):
        """获取字体对象

        Args:
            size: 字体大小，None使用默认大小
            weight: 字体粗细 (QFont.Normal, QFont.Bold等)
            italic: 是否斜体

        Returns:
            QFont对象
        """
        # 确保字体已加载
        if not self._font_loaded:
            self.load_custom_font()

        if size is None:
            size = self.default_font_size

        if self.custom_font_family:
            font = QFont(self.custom_font_family, size, weight, italic)
        else:
            # 回退到系统默认字体
            font = QFont("Microsoft YaHei", size, weight, italic)

        return font
    
    def get_title_font(self, size=16):
        """获取标题字体"""
        return self.get_font(size, QFont.Bold)
    
    def get_subtitle_font(self, size=14):
        """获取副标题字体"""
        return self.get_font(size, QFont.DemiBold)
    
    def get_body_font(self, size=10):
        """获取正文字体"""
        return self.get_font(size, QFont.Normal)
    
    def get_caption_font(self, size=9):
        """获取说明文字字体"""
        return self.get_font(size, QFont.Normal)
    
    def get_code_font(self, size=9):
        """获取代码字体（等宽）"""
        if self.custom_font_family:
            # MapleMono是等宽字体，适合代码显示
            return self.get_font(size, QFont.Normal)
        else:
            # 回退到系统等宽字体
            font = QFont("Consolas", size, QFont.Normal)
            if not font.exactMatch():
                font = QFont("Courier New", size, QFont.Normal)
            return font
    
    def apply_to_application(self):
        """将字体应用到整个应用程序"""
        # 确保字体已加载
        if not self._font_loaded:
            self.load_custom_font()

        app = QApplication.instance()
        if app:
            default_font = self.get_body_font()
            app.setFont(default_font)
            if self.custom_font_family:
                print(f"✅ 应用程序字体设置为: {self.custom_font_family}")
            else:
                print("✅ 应用程序字体设置为系统默认字体")
            return True
        return False
    
    def get_font_info(self):
        """获取字体信息"""
        info = {
            'custom_font_loaded': self.custom_font_family is not None,
            'custom_font_family': self.custom_font_family,
            'font_file_path': str(self.custom_font_path.absolute()),
            'font_file_exists': self.custom_font_path.exists(),
            'default_font_size': self.default_font_size
        }
        return info
    
    def list_available_fonts(self):
        """列出所有可用字体"""
        families = self.font_database.families()
        return sorted(families)
    
    def set_default_font_size(self, size):
        """设置默认字体大小"""
        self.default_font_size = size
        print(f"✅ 默认字体大小设置为: {size}pt")

# 全局字体管理器实例
font_manager = FontManager()

def get_font(size=None, weight=QFont.Normal, italic=False):
    """便捷函数：获取字体"""
    return font_manager.get_font(size, weight, italic)

def get_title_font(size=16):
    """便捷函数：获取标题字体"""
    return font_manager.get_title_font(size)

def get_subtitle_font(size=14):
    """便捷函数：获取副标题字体"""
    return font_manager.get_subtitle_font(size)

def get_body_font(size=10):
    """便捷函数：获取正文字体"""
    return font_manager.get_body_font(size)

def get_caption_font(size=9):
    """便捷函数：获取说明文字字体"""
    return font_manager.get_caption_font(size)

def get_code_font(size=9):
    """便捷函数：获取代码字体"""
    return font_manager.get_code_font(size)

def apply_font_to_application():
    """便捷函数：应用字体到整个应用"""
    return font_manager.apply_to_application()

def get_font_info():
    """便捷函数：获取字体信息"""
    return font_manager.get_font_info()

if __name__ == "__main__":
    # 测试字体管理器
    print("🔤 字体管理器测试")
    print("=" * 40)
    
    # 显示字体信息
    info = font_manager.get_font_info()
    print("📋 字体信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # 测试各种字体
    print("\n🎨 字体样式测试:")
    fonts = {
        '标题字体': font_manager.get_title_font(),
        '副标题字体': font_manager.get_subtitle_font(),
        '正文字体': font_manager.get_body_font(),
        '说明字体': font_manager.get_caption_font(),
        '代码字体': font_manager.get_code_font()
    }
    
    for name, font in fonts.items():
        print(f"  {name}: {font.family()}, {font.pointSize()}pt, 粗细:{font.weight()}")
    
    print("\n✅ 字体管理器测试完成")
