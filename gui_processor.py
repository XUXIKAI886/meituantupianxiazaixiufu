#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI专用的数据处理器
提供更好的进度反馈和日志输出
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
import requests
from PIL import Image

from malatang_processor import DataExtractor, ExcelManager, ImageDownloader, Config


class GUIProcessor:
    """GUI专用处理器"""
    
    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.data_extractor = DataExtractor(self.logger)
        self.excel_manager = ExcelManager(self.logger)
        self.image_downloader = ImageDownloader(self.logger)
        
        self.total_steps = 0
        self.current_step = 0
    
    def log(self, message, level="INFO"):
        """发送日志消息"""
        self.logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)
    
    def update_progress(self, step_name=""):
        """更新进度"""
        if self.total_steps > 0:
            progress = int((self.current_step / self.total_steps) * 100)
            if self.progress_callback:
                self.progress_callback(progress)
            
            if step_name:
                self.log(f"进度 {progress}%: {step_name}")
    
    def process_file(self, input_file, output_excel, images_dir):
        """处理文件"""
        try:
            self.total_steps = 6  # 总步骤数
            self.current_step = 0
            
            # 步骤1: 解析JSON文件
            self.log("🔍 开始解析JSON文件...")
            self.current_step += 1
            self.update_progress("解析JSON文件")
            
            data = self.data_extractor.parse_json_file(input_file)
            if not data:
                raise Exception("JSON文件解析失败")
            
            # 步骤2: 提取商品信息
            self.log("📦 提取商品信息...")
            self.current_step += 1
            self.update_progress("提取商品信息")
            
            products = self.data_extractor.extract_products(data)
            if not products:
                raise Exception("没有提取到商品信息")
            
            self.log(f"✅ 成功提取 {len(products)} 个商品信息")
            
            # 步骤3: 检查现有Excel数据
            self.log("📊 检查现有Excel数据...")
            self.current_step += 1
            self.update_progress("检查Excel数据")
            
            existing_df = self.excel_manager.load_existing_data(output_excel)
            existing_names = set(existing_df['商品名称'].tolist()) if not existing_df.empty else set()
            
            # 过滤新商品
            new_products = [p for p in products if p['name'] not in existing_names]
            self.log(f"📋 发现 {len(new_products)} 个新商品需要处理")
            
            # 步骤4: 保存到Excel
            self.log("💾 保存数据到Excel...")
            self.current_step += 1
            self.update_progress("保存Excel数据")
            
            self.excel_manager.save_products_to_excel(products, output_excel)
            
            # 步骤5: 创建图片目录
            self.log("📁 创建图片目录...")
            self.current_step += 1
            self.update_progress("创建图片目录")
            
            os.makedirs(images_dir, exist_ok=True)
            
            # 步骤6: 下载图片
            self.log("🖼️ 开始下载图片...")
            self.current_step += 1
            self.update_progress("下载图片")
            
            download_results = self.download_images_with_progress(products, images_dir)
            
            # 完成
            self.current_step = self.total_steps
            self.update_progress("处理完成")
            
            # 返回结果统计
            results = {
                'total_products': len(products),
                'new_products': len(new_products),
                'downloaded_images': download_results['downloaded'],
                'skipped_images': download_results['skipped'],
                'failed_images': download_results['failed'],
                'excel_file': output_excel,
                'images_dir': images_dir
            }
            
            self.log("🎉 所有处理完成！")
            self.log(f"📊 统计: 商品{results['total_products']}个, 新增{results['new_products']}个")
            self.log(f"🖼️ 图片: 下载{results['downloaded_images']}张, 跳过{results['skipped_images']}张, 失败{results['failed_images']}张")
            
            return results
            
        except Exception as e:
            self.log(f"❌ 处理失败: {str(e)}", "ERROR")
            raise
    
    def download_images_with_progress(self, products, images_dir):
        """带进度的图片下载"""
        downloaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        total_images = len([p for p in products if p['image_url']])
        
        for i, product in enumerate(products):
            if not product['image_url'] or not product['image_filename']:
                continue
                
            file_path = os.path.join(images_dir, product['image_filename'])
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                skipped_count += 1
                self.log(f"⏭️ 跳过已存在的图片: {product['image_filename']}")
                continue
            
            # 下载图片
            self.log(f"⬇️ 下载图片 ({i+1}/{total_images}): {product['name']}")
            
            if self._download_single_image_gui(product['image_url'], file_path, product['name']):
                downloaded_count += 1
                self.log(f"✅ 下载成功: {product['image_filename']}")
            else:
                failed_count += 1
                self.log(f"❌ 下载失败: {product['image_filename']}", "WARNING")
        
        return {
            'downloaded': downloaded_count,
            'skipped': skipped_count,
            'failed': failed_count
        }
    
    def _download_single_image_gui(self, url, file_path, product_name):
        """GUI版本的单个图片下载"""
        try:
            # 使用现有的图片下载器
            return self.image_downloader._download_single_image(url, file_path)
        except Exception as e:
            self.log(f"下载图片时出错 {product_name}: {e}", "WARNING")
            return False


class GUIImageConverter:
    """GUI专用图片转换器"""
    
    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.quality = 95
        self.supported_formats = {'.webp', '.png', '.bmp', '.tiff', '.tif'}
    
    def log(self, message, level="INFO"):
        """发送日志消息"""
        if self.log_callback:
            self.log_callback(message, level)
    
    def convert_all_images(self, images_dir):
        """转换所有图片"""
        if not os.path.exists(images_dir):
            self.log(f"❌ 图片目录不存在: {images_dir}", "ERROR")
            return False
        
        # 扫描需要转换的文件
        files_to_convert = []
        for filename in os.listdir(images_dir):
            file_path = os.path.join(images_dir, filename)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename.lower())
                if ext in self.supported_formats:
                    # 检查是否有对应的JPG文件
                    base_name = os.path.splitext(file_path)[0]
                    jpg_path = f"{base_name}.jpg"
                    if not os.path.exists(jpg_path):
                        files_to_convert.append(file_path)
        
        if not files_to_convert:
            self.log("✅ 没有需要转换的图片文件")
            return True
        
        self.log(f"🔄 开始转换 {len(files_to_convert)} 个图片文件...")
        
        converted_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(files_to_convert):
            filename = os.path.basename(file_path)
            self.log(f"🖼️ 转换图片 ({i+1}/{len(files_to_convert)}): {filename}")
            
            if self._convert_single_image(file_path):
                converted_count += 1
                self.log(f"✅ 转换成功: {filename}")
            else:
                failed_count += 1
                self.log(f"❌ 转换失败: {filename}", "WARNING")
            
            # 更新进度
            if self.progress_callback:
                progress = int(((i + 1) / len(files_to_convert)) * 100)
                self.progress_callback(progress)
        
        self.log(f"🎉 图片转换完成! 成功: {converted_count}, 失败: {failed_count}")
        return True
    
    def _convert_single_image(self, input_path):
        """转换单个图片"""
        try:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}.jpg"
            
            with Image.open(input_path) as img:
                # 处理透明通道
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存为JPG
                img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
            
            return True
            
        except Exception as e:
            return False
