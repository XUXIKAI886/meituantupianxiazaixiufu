#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
用户可以根据需要修改这些配置项
"""

# 文件路径配置
INPUT_FILE = "D:/ailun/liansuoshuju.txt"       # 输入的JSON数据文件（默认）
OUTPUT_EXCEL = "malatang_products.xlsx"        # 输出的Excel文件
IMAGES_DIR = "images"                          # 图片保存目录
LOG_FILE = "malatang_processor.log"            # 日志文件

# 预设数据文件路径配置
PRESET_FILES = {
    "获取连锁图片": "D:/ailun/liansuoshuju.txt",
    "获取小叮当图片": "D:/ailun/xiaodingdangshuju.txt"
}

# 默认选择的预设选项
DEFAULT_PRESET = "获取连锁图片"

# 网络请求配置
REQUEST_TIMEOUT = 30                           # 请求超时时间（秒）
MAX_RETRIES = 3                                # 最大重试次数
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 文件处理配置
PRESERVE_ORIGINAL_NAME = True                  # 保持文件名与商品名称完全一致
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']  # 支持的图片格式

# 监控配置
MONITOR_DELAY = 2                              # 文件监控延迟（秒），防止重复触发
FILE_WRITE_DELAY = 1                           # 文件写入完成等待时间（秒）

# Excel配置
EXCEL_COLUMNS = [
    '商品名称', 
    '原价', 
    '折扣价', 
    '月售数量', 
    '图片链接', 
    '图片文件名', 
    '更新时间'
]

# 日志配置
LOG_LEVEL = "INFO"                             # 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# 数据处理配置
ENABLE_DEDUPLICATION = True                    # 是否启用去重功能
SKIP_EXISTING_IMAGES = True                    # 是否跳过已存在的图片
CLEAN_PRODUCT_NAMES = True                     # 是否清理商品名称中的特殊字符

# 图片转换配置
CONVERT_TO_JPG = True                          # 是否将所有图片转换为JPG格式
JPG_QUALITY = 95                               # JPG图片质量 (1-100，95为高质量)
JPG_BACKGROUND_COLOR = (255, 255, 255)        # 透明背景替换颜色 (白色)
