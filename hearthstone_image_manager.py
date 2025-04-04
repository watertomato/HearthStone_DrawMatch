import requests
import json
import os
import sys
import time
import concurrent.futures
from tqdm import tqdm  # 用于显示进度条
import importlib.util  # 用于动态导入模块

class HearthstoneImageManager:
    """炉石传说卡牌图像管理器，支持批量下载不同类型的卡牌图片"""
    
    def __init__(self):
        # --- 判断运行环境并确定基准路径 ---
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe 文件运行
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是直接作为 .py 文件运行
            application_path = os.path.dirname(os.path.abspath(__file__))
        # ------------------------------------

        # 使用 application_path 来构建目录
        self.json_data_dir = os.path.join(application_path, "hsJSON卡牌数据")
        self.images_dir = os.path.join(application_path, "炉石卡牌图片")
        
        # 创建不同类型图片的子目录
        self.orig_dir = os.path.join(self.images_dir, "原始图")
        self.art_256x_dir = os.path.join(self.images_dir, "256x")
        self.art_512x_dir = os.path.join(self.images_dir, "512x")
        self.tiles_dir = os.path.join(self.images_dir, "缩略图")
        self.render_dir = os.path.join(self.images_dir, "渲染图")
        
        # API基础URL
        self.base_urls = {
            'orig': 'https://art.hearthstonejson.com/v1/orig/',
            '256x': 'https://art.hearthstonejson.com/v1/256x/',
            '512x': 'https://art.hearthstonejson.com/v1/512x/',
            'tiles': 'https://art.hearthstonejson.com/v1/tiles/',
            'render': 'https://art.hearthstonejson.com/v1/render/latest/'
        }
        
        # 支持的语言
        self.locales = ['zhCN', 'enUS', 'frFR', 'deDE', 'itIT', 'jaJP', 'koKR', 'plPL', 'ptBR', 'ruRU', 'esES', 'esMX', 'thTH']
        
        # 确保所有目录存在
        self._ensure_directories()
        
        # 加载扩展包信息
        self.set_names = self.load_set_names()
    
    def _ensure_directories(self):
        """确保所有需要的目录存在"""
        os.makedirs(self.json_data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.orig_dir, exist_ok=True)
        os.makedirs(self.art_256x_dir, exist_ok=True)
        os.makedirs(self.art_512x_dir, exist_ok=True)
        os.makedirs(self.tiles_dir, exist_ok=True)
        os.makedirs(self.render_dir, exist_ok=True)
        
        # 为渲染图创建语言子目录
        for locale in self.locales:
            locale_dir = os.path.join(self.render_dir, locale)
            os.makedirs(locale_dir, exist_ok=True)
            # 为每种分辨率创建子目录
            os.makedirs(os.path.join(locale_dir, '256x'), exist_ok=True)
            os.makedirs(os.path.join(locale_dir, '512x'), exist_ok=True)
    
    def load_set_names(self):
        """加载config.py中的SET_NAMES字典"""
        try:
            # 动态导入config模块
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
            if not os.path.exists(config_path):
                print(f"找不到配置文件: {config_path}")
                return {}
                
            spec = importlib.util.spec_from_file_location("config", config_path)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            # 获取SET_NAMES字典
            if hasattr(config, 'SET_NAMES'):
                return config.SET_NAMES
            else:
                print("config.py中未找到SET_NAMES字典")
                return {}
        except Exception as e:
            print(f"加载扩展包名称时出错: {e}")
            return {}
    
    def get_latest_sets(self, count=7):
        """获取最新的N个扩展包"""
        if not self.set_names:
            print("未能加载扩展包信息")
            return []
            
        # 返回字典的前N个键
        return list(self.set_names.keys())[:count]
    
    def load_card_ids(self):
        """
        从卡牌数据中加载所有卡牌ID
        返回一个包含所有卡牌ID的列表
        """
        card_infos_path = os.path.join(self.json_data_dir, "card_infos.json")
        if not os.path.exists(card_infos_path):
            print(f"找不到卡牌数据文件: {card_infos_path}")
            print("请先运行 HearthstoneDataManager 获取卡牌数据")
            return []
        
        try:
            with open(card_infos_path, 'r', encoding='utf-8') as f:
                card_infos = json.load(f)
            
            # 提取所有卡牌ID
            card_ids = [card['id'] for card in card_infos if 'id' in card]
            return card_ids
        except Exception as e:
            print(f"加载卡牌ID时出错: {e}")
            return []
    
    def download_image(self, url, save_path, timeout=10):
        """
        下载单个图片并保存到指定路径
        
        Args:
            url: 图片的URL
            save_path: 保存图片的路径
            timeout: 请求超时时间（秒）
        
        Returns:
            bool: 下载是否成功
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        
        # 如果文件已存在，则跳过
        if os.path.exists(save_path):
            return True
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return False
        except Exception:
            return False
    
    def download_orig_art(self, card_id):
        """下载原始尺寸的卡牌艺术图片（PNG格式）"""
        url = f"{self.base_urls['orig']}{card_id}.png"
        save_path = os.path.join(self.orig_dir, f"{card_id}.png")
        return self.download_image(url, save_path)
    
    def download_art_256x(self, card_id, format='jpg'):
        """下载256x256尺寸的卡牌艺术图片"""
        format = format.lower()
        if format not in ['jpg', 'webp']:
            format = 'jpg'
        
        url = f"{self.base_urls['256x']}{card_id}.{format}"
        save_path = os.path.join(self.art_256x_dir, f"{card_id}.{format}")
        return self.download_image(url, save_path)
    
    def download_art_512x(self, card_id, format='jpg'):
        """下载512x512尺寸的卡牌艺术图片"""
        format = format.lower()
        if format not in ['jpg', 'webp']:
            format = 'jpg'
        
        url = f"{self.base_urls['512x']}{card_id}.{format}"
        save_path = os.path.join(self.art_512x_dir, f"{card_id}.{format}")
        return self.download_image(url, save_path)
    
    def download_tile(self, card_id, format='png'):
        """下载卡牌缩略图（用于卡组显示）"""
        format = format.lower()
        if format not in ['png', 'jpg', 'webp']:
            format = 'png'
        
        url = f"{self.base_urls['tiles']}{card_id}.{format}"
        save_path = os.path.join(self.tiles_dir, f"{card_id}.{format}")
        return self.download_image(url, save_path)
    
    def download_render(self, card_id, locale='zhCN', resolution='512x'):
        """下载完整渲染的卡牌图片"""
        if locale not in self.locales:
            locale = 'zhCN'
        
        if resolution not in ['256x', '512x']:
            resolution = '512x'
        
        url = f"{self.base_urls['render']}{locale}/{resolution}/{card_id}.png"
        locale_res_dir = os.path.join(self.render_dir, locale, resolution)
        os.makedirs(locale_res_dir, exist_ok=True)
        
        save_path = os.path.join(locale_res_dir, f"{card_id}.png")
        return self.download_image(url, save_path)
    
    def batch_download_images(self, image_type, card_ids, format='jpg', locale='zhCN', resolution='512x', max_workers=5):
        """
        批量下载指定类型的卡牌图片
        
        Args:
            image_type: 图片类型，可选 'orig', '256x', '512x', 'tiles', 'render'
            card_ids: 卡牌ID列表
            format: 图片格式，取决于image_type
            locale: 语言，仅用于渲染图
            resolution: 分辨率，仅用于渲染图
            max_workers: 最大并发下载线程数
        
        Returns:
            (success_count, failed_count): 成功和失败的下载数量
        """
        success_count = 0
        failed_count = 0
        failed_ids = []
        
        print(f"开始下载 {image_type} 类型的卡牌图片...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # 根据不同类型的图片，创建不同的下载任务
            if image_type == 'orig':
                for card_id in card_ids:
                    futures.append(executor.submit(self.download_orig_art, card_id))
            elif image_type == '256x':
                for card_id in card_ids:
                    futures.append(executor.submit(self.download_art_256x, card_id, format))
            elif image_type == '512x':
                for card_id in card_ids:
                    futures.append(executor.submit(self.download_art_512x, card_id, format))
            elif image_type == 'tiles':
                for card_id in card_ids:
                    futures.append(executor.submit(self.download_tile, card_id, format))
            elif image_type == 'render':
                for card_id in card_ids:
                    futures.append(executor.submit(self.download_render, card_id, locale, resolution))
            else:
                print(f"未知的图片类型: {image_type}")
                return 0, 0
            
            # 使用tqdm显示进度
            for i, future in enumerate(tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc=f"下载{image_type}")):
                try:
                    if future.result():
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(card_ids[i] if i < len(card_ids) else "未知卡牌")
                except Exception as e:
                    print(f"处理下载任务时出错: {e}")
                    failed_count += 1
        
        print(f"{image_type} 类型卡牌图片下载完成！成功: {success_count}, 失败: {failed_count}")
        
        if failed_count > 0:
            print(f"失败的卡牌ID (前10个): {failed_ids[:10]}")
            # 将失败的卡牌ID保存到文件
            failed_file = os.path.join(self.images_dir, f"failed_{image_type}.txt")
            with open(failed_file, 'w', encoding='utf-8') as f:
                for card_id in failed_ids:
                    f.write(f"{card_id}\n")
            print(f"所有失败的卡牌ID已保存到: {failed_file}")
        
        return success_count, failed_count
    
    def download_all_image_types(self, card_ids=None, locale='zhCN'):
        """
        下载所有类型的卡牌图片
        
        Args:
            card_ids: 卡牌ID列表，如果为None则加载所有卡牌
            locale: 渲染图的语言
        """
        if card_ids is None:
            card_ids = self.load_card_ids()
            if not card_ids:
                print("未找到卡牌ID，无法下载图片")
                return
        
        print(f"准备下载 {len(card_ids)} 张卡牌的所有类型图片...")
        
        # 下载原始图
        self.batch_download_images('orig', card_ids)
        
        # 下载艺术图 (256x)
        self.batch_download_images('256x', card_ids, format='jpg')
        
        # 下载艺术图 (512x)
        self.batch_download_images('512x', card_ids, format='jpg')
        
        # 下载缩略图
        self.batch_download_images('tiles', card_ids, format='png')
        
        # 下载渲染图 (512x)
        self.batch_download_images('render', card_ids, locale=locale, resolution='512x')
        
        print("所有类型的卡牌图片下载完成！")
    
    def download_collectible_card_images(self, locale='zhCN'):
        """仅下载可收藏卡牌的图片"""
        card_infos_path = os.path.join(self.json_data_dir, "card_infos.json")
        if not os.path.exists(card_infos_path):
            print(f"找不到卡牌数据文件: {card_infos_path}")
            return
        
        try:
            with open(card_infos_path, 'r', encoding='utf-8') as f:
                card_infos = json.load(f)
            
            # 筛选可收藏的卡牌
            collectible_cards = [card for card in card_infos if card.get('collectible', False)]
            collectible_ids = [card['id'] for card in collectible_cards if 'id' in card]
            
            print(f"找到 {len(collectible_ids)} 张可收藏卡牌")
            self.download_all_image_types(collectible_ids, locale)
            
        except Exception as e:
            print(f"处理可收藏卡牌时出错: {e}")
    
    def download_collectible_tiles_only(self, format='png'):
        """只下载可收藏卡牌的缩略图"""
        card_infos_path = os.path.join(self.json_data_dir, "card_infos.json")
        if not os.path.exists(card_infos_path):
            print(f"找不到卡牌数据文件: {card_infos_path}")
            print("请先运行 HearthstoneDataManager 获取卡牌数据")
            return False
        
        try:
            with open(card_infos_path, 'r', encoding='utf-8') as f:
                card_infos = json.load(f)
            
            # 筛选可收藏的卡牌
            collectible_cards = [card for card in card_infos if card.get('collectible', False)]
            collectible_ids = [card['id'] for card in collectible_cards if 'id' in card]
            
            print(f"找到 {len(collectible_ids)} 张可收藏卡牌")
            
            # 只下载缩略图
            self.batch_download_images('tiles', collectible_ids, format=format)
            
            print("缩略图下载完成！")
            return True
            
        except Exception as e:
            print(f"处理可收藏卡牌时出错: {e}")
            return False
    
    def download_latest_sets_tiles(self, format='png', set_count=7):
        """只下载最新的N个扩展包中的可收藏卡牌的缩略图"""
        card_infos_path = os.path.join(self.json_data_dir, "card_infos.json")
        if not os.path.exists(card_infos_path):
            print(f"找不到卡牌数据文件: {card_infos_path}")
            print("请先运行 HearthstoneDataManager 获取卡牌数据")
            return False
        
        # 获取最新的N个扩展包
        latest_sets = self.get_latest_sets(set_count)
        if not latest_sets:
            print(f"无法获取最新的{set_count}个扩展包信息")
            return False
            
        print(f"获取到最新的{len(latest_sets)}个扩展包: {', '.join(latest_sets)}")
        
        try:
            with open(card_infos_path, 'r', encoding='utf-8') as f:
                card_infos = json.load(f)
            
            # 筛选可收藏的卡牌且属于最新扩展包的卡牌
            latest_collectible_cards = [
                card for card in card_infos 
                if card.get('collectible', False) and card.get('set', '') in latest_sets
            ]
            
            if not latest_collectible_cards:
                print(f"未找到属于最新{set_count}个扩展包的可收藏卡牌")
                return False
                
            latest_collectible_ids = [card['id'] for card in latest_collectible_cards if 'id' in card]
            
            print(f"找到 {len(latest_collectible_ids)} 张属于最新扩展包的可收藏卡牌")
            
            # 只下载缩略图
            self.batch_download_images('tiles', latest_collectible_ids, format=format)
            
            print("最新扩展包卡牌缩略图下载完成！")
            return True
            
        except Exception as e:
            print(f"处理最新扩展包卡牌时出错: {e}")
            return False
    
    def download_collectible_render_and_512x(self, format='jpg', locale='zhCN', resolution='512x'):
        """下载可收藏卡牌的渲染图和512x分辨率图片"""
        card_infos_path = os.path.join(self.json_data_dir, "card_infos.json")
        if not os.path.exists(card_infos_path):
            print(f"找不到卡牌数据文件: {card_infos_path}")
            print("请先运行 HearthstoneDataManager 获取卡牌数据")
            return False
        
        try:
            with open(card_infos_path, 'r', encoding='utf-8') as f:
                card_infos = json.load(f)
            
            # 筛选可收藏的卡牌
            collectible_cards = [card for card in card_infos if card.get('collectible', False)]
            collectible_ids = [card['id'] for card in collectible_cards if 'id' in card]
            
            print(f"找到 {len(collectible_ids)} 张可收藏卡牌")
            
            # 下载512x图片
            print("开始下载512x图片...")
            self.batch_download_images('512x', collectible_ids, format=format)
            
            # 下载渲染图
            print("开始下载渲染图...")
            self.batch_download_images('render', collectible_ids, locale=locale, resolution=resolution)
            
            print("高质量图片下载完成！")
            return True
            
        except Exception as e:
            print(f"处理可收藏卡牌时出错: {e}")
            return False
    
    def download_latest_sets_render_and_512x(self, format='jpg', locale='zhCN', resolution='512x', set_count=7):
        """只下载最新的N个扩展包中的可收藏卡牌的渲染图和512x图片"""
        card_infos_path = os.path.join(self.json_data_dir, "card_infos.json")
        if not os.path.exists(card_infos_path):
            print(f"找不到卡牌数据文件: {card_infos_path}")
            print("请先运行 HearthstoneDataManager 获取卡牌数据")
            return False
        
        # 获取最新的N个扩展包
        latest_sets = self.get_latest_sets(set_count)
        if not latest_sets:
            print(f"无法获取最新的{set_count}个扩展包信息")
            return False
            
        print(f"获取到最新的{len(latest_sets)}个扩展包: {', '.join(latest_sets)}")
        
        try:
            with open(card_infos_path, 'r', encoding='utf-8') as f:
                card_infos = json.load(f)
            
            # 筛选可收藏的卡牌且属于最新扩展包的卡牌
            latest_collectible_cards = [
                card for card in card_infos 
                if card.get('collectible', False) and card.get('set', '') in latest_sets
            ]
            
            if not latest_collectible_cards:
                print(f"未找到属于最新{set_count}个扩展包的可收藏卡牌")
                return False
                
            latest_collectible_ids = [card['id'] for card in latest_collectible_cards if 'id' in card]
            
            print(f"找到 {len(latest_collectible_ids)} 张属于最新扩展包的可收藏卡牌")
            
            # 下载512x图片
            print("开始下载最新扩展包的512x图片...")
            self.batch_download_images('512x', latest_collectible_ids, format=format)
            
            # 下载渲染图
            print("开始下载最新扩展包的渲染图...")
            self.batch_download_images('render', latest_collectible_ids, locale=locale, resolution=resolution)
            
            print("最新扩展包高质量图片下载完成！")
            return True
            
        except Exception as e:
            print(f"处理最新扩展包卡牌时出错: {e}")
            return False
    
    def run_all(self, download_latest_only=False):
        """运行下载流程 - 下载中文可收藏卡牌的渲染图和512x图片"""
        if download_latest_only:
            print("开始下载最新7个扩展包的可收藏卡牌渲染图和512x图片...\n")
            return self.download_latest_sets_render_and_512x(locale='zhCN', resolution='512x', set_count=7)
        else:
            print("开始下载所有可收藏卡牌渲染图和512x图片...\n")
            return self.download_collectible_render_and_512x(locale='zhCN', resolution='512x')

# 如果直接运行此脚本，则执行流程
if __name__ == "__main__":
    manager = HearthstoneImageManager()
    try:
        download_latest_input = input("是否只下载最新的7个扩展包卡牌？(y/n，默认n): ").strip().lower()
        download_latest_only = download_latest_input == 'y'
        
        manager.run_all(download_latest_only=download_latest_only)
    except KeyboardInterrupt:
        print("\n\n下载过程被用户中断")
        print("可以稍后重新运行，已下载的图片不会重复下载") 