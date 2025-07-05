#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麻辣烫数据处理脚本
功能：解析malatang.txt文件，提取商品信息，生成Excel表格并下载图片
支持文件监控和自动更新
"""

import json
import os
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

import pandas as pd
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)


class Config:
    """配置类"""
    INPUT_FILE = "D:/ailun/liansuoshuju.txt"
    OUTPUT_EXCEL = "malatang_products.xlsx"
    IMAGES_DIR = "images"
    LOG_FILE = "malatang_processor.log"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    FILENAME_MAX_LENGTH = 100
    CONVERT_TO_JPG = True  # 是否将图片转换为JPG格式
    JPG_QUALITY = 95  # JPG图片质量 (1-100)


class Logger:
    """日志管理类"""
    
    @staticmethod
    def setup_logger():
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)


class DataExtractor:
    """数据提取类"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def parse_json_file(self, file_path: str) -> Optional[Dict]:
        """解析JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"成功解析JSON文件: {file_path}")
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return None
        except FileNotFoundError:
            self.logger.error(f"文件不存在: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"读取文件时发生错误: {e}")
            return None
    
    def extract_products(self, data: Dict) -> List[Dict]:
        """提取商品信息"""
        products = []
        
        try:
            spu_list = data.get('data', {}).get('spuListVos', [])
            self.logger.info(f"找到 {len(spu_list)} 个商品")
            
            for item in spu_list:
                try:
                    product = self._extract_single_product(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    self.logger.warning(f"提取商品信息时出错: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"提取商品列表时出错: {e}")
        
        self.logger.info(f"成功提取 {len(products)} 个商品信息")
        return products
    
    def _extract_single_product(self, item: Dict) -> Optional[Dict]:
        """提取单个商品信息"""
        try:
            name = item.get('name', '').strip()
            if not name:
                return None
            
            price = item.get('price', 0)
            discount_price = item.get('discountPrice', -1)
            month_sale = item.get('monthSale', 0)
            
            # 提取图片信息
            pic_info = self._extract_image_info(item)
            
            return {
                'name': name,
                'price': price,
                'discount_price': discount_price if discount_price > 0 else price,
                'month_sale': month_sale,
                'image_url': pic_info['url'],
                'image_filename': pic_info['filename']
            }
        except Exception as e:
            self.logger.warning(f"提取单个商品信息失败: {e}")
            return None
    
    def _extract_image_info(self, item: Dict) -> Dict[str, str]:
        """提取图片信息"""
        pic_vos = item.get('wmProductPicVos', [])
        if not pic_vos:
            return {'url': '', 'filename': ''}
        
        # 优先使用高清图片
        pic_url = pic_vos[0].get('picLargeUrl') or pic_vos[0].get('picUrl', '')
        
        if pic_url:
            # 生成文件名
            product_name = item.get('name', 'unknown')
            filename = self._clean_filename(product_name, pic_url)
            return {'url': pic_url, 'filename': filename}
        
        return {'url': '', 'filename': ''}
    
    def _clean_filename(self, product_name: str, url: str) -> str:
        """生成文件名（保持与商品名称完全一致）"""
        # 保持商品名称完全不变，只替换Windows文件系统不支持的字符
        clean_name = product_name

        # 只替换Windows文件系统绝对不支持的字符，用相似字符替换
        replacements = {
            '<': '＜',   # 全角小于号
            '>': '＞',   # 全角大于号
            ':': '：',   # 全角冒号
            '"': '"',   # 全角引号
            '/': '／',   # 全角斜杠
            '\\': '＼',  # 全角反斜杠
            '|': '｜',   # 全角竖线
            '?': '？',   # 全角问号
            '*': '＊'    # 全角星号
        }

        for old_char, new_char in replacements.items():
            clean_name = clean_name.replace(old_char, new_char)

        # 如果配置为转换为JPG，则使用.jpg扩展名
        if Config.CONVERT_TO_JPG:
            ext = '.jpg'
        else:
            # 获取原始文件扩展名
            parsed_url = urlparse(url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = '.jpg'  # 默认扩展名

        return f"{clean_name}{ext}"


class ExcelManager:
    """Excel管理类"""
    
    def __init__(self, logger):
        self.logger = logger
        self.columns = ['商品名称', '原价', '折扣价', '月售数量', '图片链接', '图片文件名', '更新时间']
    
    def load_existing_data(self, file_path: str) -> pd.DataFrame:
        """加载现有Excel数据"""
        try:
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                self.logger.info(f"加载现有Excel数据，共 {len(df)} 条记录")
                return df
            else:
                self.logger.info("Excel文件不存在，将创建新文件")
                return pd.DataFrame(columns=self.columns)
        except Exception as e:
            self.logger.error(f"加载Excel文件失败: {e}")
            return pd.DataFrame(columns=self.columns)
    
    def save_products_to_excel(self, products: List[Dict], file_path: str):
        """保存商品数据到Excel"""
        try:
            # 加载现有数据
            existing_df = self.load_existing_data(file_path)
            existing_names = set(existing_df['商品名称'].tolist()) if not existing_df.empty else set()
            
            # 准备新数据
            new_data = []
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for product in products:
                if product['name'] not in existing_names:
                    new_data.append({
                        '商品名称': product['name'],
                        '原价': product['price'],
                        '折扣价': product['discount_price'],
                        '月售数量': product['month_sale'],
                        '图片链接': product['image_url'],
                        '图片文件名': product['image_filename'],
                        '更新时间': current_time
                    })
            
            if new_data:
                new_df = pd.DataFrame(new_data)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_excel(file_path, index=False)
                self.logger.info(f"新增 {len(new_data)} 条商品数据到Excel文件")
            else:
                self.logger.info("没有新的商品数据需要添加")
                
        except Exception as e:
            self.logger.error(f"保存Excel文件失败: {e}")


class ImageDownloader:
    """图片下载类"""

    def __init__(self, logger):
        self.logger = logger
        self.session = requests.Session()

        # 设置更完整的请求头，模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

        # 禁用SSL验证以解决证书问题
        self.session.verify = False

        # 设置适配器以处理SSL问题
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def download_images(self, products: List[Dict], images_dir: str):
        """下载商品图片"""
        # 创建图片目录
        Path(images_dir).mkdir(exist_ok=True)
        
        downloaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        for product in products:
            if not product['image_url'] or not product['image_filename']:
                continue
                
            file_path = os.path.join(images_dir, product['image_filename'])
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                skipped_count += 1
                continue
            
            # 下载图片
            if self._download_single_image(product['image_url'], file_path):
                downloaded_count += 1
            else:
                failed_count += 1
        
        self.logger.info(f"图片下载完成 - 新下载: {downloaded_count}, 跳过: {skipped_count}, 失败: {failed_count}")
    
    def _download_single_image(self, url: str, file_path: str) -> bool:
        """下载单个图片"""
        for attempt in range(Config.MAX_RETRIES):
            try:
                # 根据域名设置不同的策略
                domain = urlparse(url).netloc

                if domain == 'img.meituan.net':
                    # 对于img.meituan.net，添加特殊的请求头
                    headers = {
                        'Referer': 'https://e.waimai.meituan.com/',
                        'Origin': 'https://e.waimai.meituan.com',
                        'Sec-Fetch-Site': 'same-site'
                    }
                    response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT, headers=headers)
                else:
                    # 对于其他域名使用默认设置
                    response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)

                response.raise_for_status()

                # 如果需要转换为JPG格式
                if Config.CONVERT_TO_JPG:
                    return self._download_and_convert_to_jpg(response.content, file_path)
                else:
                    # 直接保存原始格式
                    with open(file_path, 'wb') as f:
                        f.write(response.content)

                    # 验证文件大小
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024:  # 小于1KB可能是错误页面
                        self.logger.warning(f"文件太小 ({file_size} 字节)，可能下载失败: {file_path}")
                        os.remove(file_path)
                        return False

                    self.logger.debug(f"成功下载图片: {file_path} ({file_size} 字节)")
                    return True

            except requests.exceptions.SSLError as e:
                self.logger.warning(f"SSL错误 (尝试 {attempt + 1}/{Config.MAX_RETRIES}): {url} - {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2)
                    continue
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"连接错误 (尝试 {attempt + 1}/{Config.MAX_RETRIES}): {url} - {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2)
                    continue
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"超时 (尝试 {attempt + 1}/{Config.MAX_RETRIES}): {url} - {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                self.logger.warning(f"下载图片失败 (尝试 {attempt + 1}/{Config.MAX_RETRIES}): {url} - {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(1)

        return False

    def _download_and_convert_to_jpg(self, image_data: bytes, file_path: str) -> bool:
        """下载图片并转换为JPG格式"""
        try:
            # 创建临时文件保存原始图片
            temp_path = file_path + '.temp'
            with open(temp_path, 'wb') as f:
                f.write(image_data)

            # 使用PIL打开并转换图片
            with Image.open(temp_path) as img:
                # 如果图片有透明通道，转换为RGB模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # 保存为JPG格式
                img.save(file_path, 'JPEG', quality=Config.JPG_QUALITY, optimize=True)

            # 删除临时文件
            os.remove(temp_path)

            self.logger.debug(f"成功下载并转换图片为JPG: {file_path}")
            return True

        except Exception as e:
            self.logger.warning(f"图片转换失败: {e}")
            # 如果转换失败，尝试直接保存原始格式
            try:
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                self.logger.debug(f"转换失败，保存原始格式: {file_path}")
                return True
            except Exception as e2:
                self.logger.error(f"保存原始格式也失败: {e2}")
                return False
        finally:
            # 确保清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass


class FileMonitorHandler(FileSystemEventHandler):
    """文件监控处理器"""
    
    def __init__(self, processor):
        self.processor = processor
        self.last_modified = 0
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith(Config.INPUT_FILE):
            # 防止重复触发
            current_time = time.time()
            if current_time - self.last_modified < 2:
                return
            
            self.last_modified = current_time
            self.processor.logger.info("检测到文件变化，开始处理...")
            time.sleep(1)  # 等待文件写入完成
            self.processor.process_file()


class MalatangProcessor:
    """主处理类"""
    
    def __init__(self):
        self.logger = Logger.setup_logger()
        self.data_extractor = DataExtractor(self.logger)
        self.excel_manager = ExcelManager(self.logger)
        self.image_downloader = ImageDownloader(self.logger)
    
    def process_file(self):
        """处理文件"""
        self.logger.info("开始处理麻辣烫数据...")
        
        # 解析JSON数据
        data = self.data_extractor.parse_json_file(Config.INPUT_FILE)
        if not data:
            return
        
        # 提取商品信息
        products = self.data_extractor.extract_products(data)
        if not products:
            self.logger.warning("没有提取到商品信息")
            return
        
        # 保存到Excel
        self.excel_manager.save_products_to_excel(products, Config.OUTPUT_EXCEL)
        
        # 下载图片
        self.image_downloader.download_images(products, Config.IMAGES_DIR)
        
        self.logger.info("数据处理完成")
    
    def start_monitoring(self):
        """启动文件监控"""
        self.logger.info("启动文件监控...")
        
        event_handler = FileMonitorHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            self.logger.info("停止文件监控")
        
        observer.join()


def main():
    """主函数"""
    import sys

    processor = MalatangProcessor()

    # 首次处理
    processor.process_file()

    # 检查是否需要启动监控
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        # 启动监控
        print("按 Ctrl+C 停止监控")
        processor.start_monitoring()
    else:
        print("数据处理完成。如需启动文件监控，请使用: python malatang_processor.py --monitor")


if __name__ == "__main__":
    main()
