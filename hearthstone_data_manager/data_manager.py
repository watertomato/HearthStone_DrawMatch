import requests
import json
import os
from collections import defaultdict
import sys # Import sys

class HearthstoneDataManager:
    """炉石传说卡牌数据管理器，支持获取和组织卡牌数据"""
    
    def __init__(self):
        # --- 判断运行环境并确定基准路径 ---
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe 文件运行
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是直接作为 .py 文件运行
            # 修改为使用项目根目录
            application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # ------------------------------------
    
        # 使用 application_path 来构建输出目录
        self.json_data_dir = os.path.join(application_path, "hsJSON卡牌数据")
        self.organized_dir = os.path.join(application_path, "炉石卡牌分类")
        
        # 职业名称中英文映射（便于目录命名）
        self.class_name_map = {
            'DEATHKNIGHT': '死亡骑士',
            'DEMONHUNTER': '恶魔猎手',
            'DRUID': '德鲁伊',
            'HUNTER': '猎人',
            'MAGE': '法师',
            'PALADIN': '圣骑士',
            'PRIEST': '牧师',
            'ROGUE': '潜行者',
            'SHAMAN': '萨满',
            'WARLOCK': '术士',
            'WARRIOR': '战士',
            'NEUTRAL': '中立'
        }
        
        # 稀有度中英文映射
        self.rarity_name_map = {
            'COMMON': '普通',
            'RARE': '稀有',
            'EPIC': '史诗',
            'LEGENDARY': '传说',
            'FREE': '基本'
        }
        
        # 确保目录存在
        os.makedirs(self.json_data_dir, exist_ok=True)
        os.makedirs(self.organized_dir, exist_ok=True)
    
    def fetch_from_hearthstonejson(self):
        """
        从HearthstoneJSON获取完整的卡牌数据
        HearthstoneJSON是一个知名的提供炉石卡牌数据的公共API
        """
        print("开始从HearthstoneJSON获取炉石传说卡牌数据...")
        
        # HearthstoneJSON API URL
        api_url = "https://api.hearthstonejson.com/v1/latest/zhCN/cards.json"
        # 注意：将zhCN改为enUS可以获取英文版卡牌
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        
        try:
            print(f"正在请求API: {api_url}")
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                # 解析JSON数据
                cards_data = response.json()
                
                # 保存完整数据
                with open(os.path.join(self.json_data_dir, "cards_complete.json"), 'w', encoding='utf-8') as f:
                    json.dump(cards_data, f, ensure_ascii=False, indent=2)
                print(f"已保存完整卡牌数据")
                
                # 提取卡牌名称和其他基本信息
                card_names = []
                card_infos = []
                
                for card in cards_data:
                    # 检查卡牌是否有中文名称
                    if 'name' in card:
                        card_names.append(card['name'])
                        
                        # 提取一些基本信息
                        card_info = {
                            'name': card.get('name', ''),
                            'id': card.get('id', ''),
                            'dbfId': card.get('dbfId', ''),
                            'type': card.get('type', ''),
                            'set': card.get('set', ''),
                            'rarity': card.get('rarity', ''),
                            'cost': card.get('cost', ''),
                            'attack': card.get('attack', ''),
                            'health': card.get('health', ''),
                            'text': card.get('text', ''),
                            'flavor': card.get('flavor', ''),
                            'artist': card.get('artist', ''),
                            'collectible': card.get('collectible', False)
                        }
                        
                        card_infos.append(card_info)
                
                # 保存卡牌名称
                with open(os.path.join(self.json_data_dir, "card_names.json"), 'w', encoding='utf-8') as f:
                    json.dump(card_names, f, ensure_ascii=False, indent=2)
                print(f"已保存 {len(card_names)} 个卡牌名称")
                
                # 保存基本信息
                with open(os.path.join(self.json_data_dir, "card_infos.json"), 'w', encoding='utf-8') as f:
                    json.dump(card_infos, f, ensure_ascii=False, indent=2)
                print(f"已保存 {len(card_infos)} 张卡牌基本信息")
                
                # 立即开始组织卡牌数据
                print("数据获取完成，准备开始组织卡牌数据")
                return True
            else:
                print(f"API请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"获取卡牌数据时出错: {e}")
            return False
    
    def organize_hearthstone_cards(self):
        """
        将炉石传说卡牌按照扩展包(set)、职业(cardClass)和稀有度(rarity)分类整理
        每个文件夹下都保存一个包含完整信息的json文件，只包含可收藏(collectible)的卡牌
        """
        print("开始按照扩展包、职业和稀有度整理炉石传说卡牌数据...")
        
        # 检查源数据文件是否存在
        complete_cards_path = os.path.join(self.json_data_dir, "cards_complete.json")
        if not os.path.exists(complete_cards_path):
            print(f"源数据文件不存在，请先运行fetch_from_hearthstonejson()")
            return False
            
        try:
            # 读取所有卡牌数据
            print(f"正在读取完整卡牌数据")
            with open(complete_cards_path, 'r', encoding='utf-8') as f:
                all_cards = json.load(f)
            
            print(f"共读取 {len(all_cards)} 张卡牌")
            
            # 只保留可收藏的卡牌
            collectible_cards = [card for card in all_cards if card.get('collectible', False)]
            print(f"其中可收藏卡牌 {len(collectible_cards)} 张")
            
            # 创建扩展包列表和统计信息
            sets_info = defaultdict(int)
            for card in collectible_cards:
                if 'set' in card and card['set']:
                    sets_info[card['set']] += 1
            
            # 输出扩展包信息
            print(f"\n找到 {len(sets_info)} 个扩展包:")
            for set_name, count in sorted(sets_info.items(), key=lambda x: x[1], reverse=True):
                print(f"- {set_name}: {count}张可收藏卡牌")
            
            # 开始组织文件结构
            print("\n开始组织文件结构...")
            
            # 创建用于存储每个层级卡牌的字典
            set_cards = defaultdict(list)  # 每个扩展包的所有卡牌
            class_cards = defaultdict(list)  # 每个扩展包下每个职业的所有卡牌
            rarity_cards = defaultdict(list)  # 每个扩展包下每个职业的每个稀有度的所有卡牌
            
            # 首先，按照扩展包、职业和稀有度组织卡牌到最底层目录
            for card in collectible_cards:
                # 获取卡牌的扩展包、职业和稀有度
                card_set = card.get('set', 'UNKNOWN')
                card_class = card.get('cardClass', 'NEUTRAL')
                card_rarity = card.get('rarity', 'UNKNOWN')
                
                # 构建目录路径（保持原始英文ID）
                set_dir = os.path.join(self.organized_dir, card_set)
                class_dir = os.path.join(set_dir, card_class)
                rarity_dir = os.path.join(class_dir, card_rarity)
                
                # 创建目录
                os.makedirs(rarity_dir, exist_ok=True)
                
                # 保存卡牌到相应的字典
                set_key = card_set
                class_key = f"{set_key}/{card_class}"
                rarity_key = f"{class_key}/{card_rarity}"
                
                # 添加到对应的集合中
                set_cards[set_key].append(card)
                class_cards[class_key].append(card)
                rarity_cards[rarity_key].append(card)
            
            # 保存每个层级的卡牌数据到对应目录
            print("正在为每个层级保存卡牌数据...")
            
            # 1. 保存最底层（稀有度）的卡牌
            for rarity_path, cards in rarity_cards.items():
                json_file = os.path.join(self.organized_dir, rarity_path, "cards.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(cards, f, ensure_ascii=False, indent=2)
            
            # 2. 保存中间层（职业）的卡牌
            for class_path, cards in class_cards.items():
                json_file = os.path.join(self.organized_dir, class_path, "all_cards.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(cards, f, ensure_ascii=False, indent=2)
            
            # 3. 保存顶层（扩展包）的卡牌
            for set_path, cards in set_cards.items():
                json_file = os.path.join(self.organized_dir, set_path, "all_cards.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(cards, f, ensure_ascii=False, indent=2)
            
            # 4. 保存根目录所有可收藏卡牌
            with open(os.path.join(self.organized_dir, "all_collectible_cards.json"), 'w', encoding='utf-8') as f:
                json.dump(collectible_cards, f, ensure_ascii=False, indent=2)
            
            # 创建统计信息
            print("\n创建统计信息文件...")
            
            # 统计各扩展包的卡牌数量
            set_stats = {}
            for card_set, count in sets_info.items():
                set_stats[card_set] = count
            
            # 保存统计信息
            with open(os.path.join(self.organized_dir, "stats.json"), 'w', encoding='utf-8') as f:
                json.dump({
                    "total_cards": len(all_cards),
                    "collectible_cards": len(collectible_cards),
                    "sets": set_stats
                }, f, ensure_ascii=False, indent=2)
            
            print(f"统计信息已保存")
            
            # 创建README文件
            with open(os.path.join(self.organized_dir, "README.txt"), 'w', encoding='utf-8') as f:
                f.write("# 炉石传说卡牌分类目录\n\n")
                f.write("## 目录结构\n")
                f.write("- 扩展包(set)：第一级目录，包含all_cards.json文件（该扩展包的所有卡牌）\n")
                f.write("- 职业(cardClass)：第二级目录，包含all_cards.json文件（该职业的所有卡牌）\n")
                f.write("- 稀有度(rarity)：第三级目录，包含cards.json文件（该稀有度的所有卡牌）\n\n")
                f.write("每个目录都有一个JSON文件，包含该层级的所有可收藏卡牌的完整信息。\n\n")
                f.write("## 统计信息\n")
                f.write(f"- 总卡牌数量：{len(all_cards)}张\n")
                f.write(f"- 可收藏卡牌数量：{len(collectible_cards)}张\n")
                f.write(f"- 扩展包数量：{len(sets_info)}个\n\n")
                
                f.write("## 扩展包列表\n")
                for set_name, count in sorted(sets_info.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {set_name}: {count}张可收藏卡牌\n")
            
            print(f"README文件已创建")
            
            print("\n卡牌分类整理完成！")
            return True
            
        except Exception as e:
            print(f"处理过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all(self):
        """运行所有数据处理步骤"""
        print("开始炉石传说卡牌数据处理流程...\n")
        
        # 1. 从HearthstoneJSON获取数据
        print("=== 步骤1: 从HearthstoneJSON获取数据 ===")
        json_success = self.fetch_from_hearthstonejson()
        
        if not json_success:
            print("从HearthstoneJSON获取数据失败，无法继续")
            return False
        
        # 2. 整理卡牌数据
        print("\n=== 步骤2: 整理炉石传说卡牌数据 ===")
        organize_success = self.organize_hearthstone_cards()
        
        if not organize_success:
            print("整理炉石传说卡牌数据失败")
            return False
        
        print("\n所有数据处理步骤完成！")
        return True

# 如果直接运行此脚本，则执行全部流程
if __name__ == "__main__":
    manager = HearthstoneDataManager()
    manager.run_all()