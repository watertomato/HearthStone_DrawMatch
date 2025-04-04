import json
import os
import random
from collections import defaultdict
from config import (RARITY_PROBABILITIES, GUARANTEE_RARE_OR_HIGHER, 
                    LEGENDARY_PITY_TIMER, DATA_PATH)
import config
from typing import Dict, List, Any, Optional

class CardDataManager:
    """卡牌数据管理类"""
    def __init__(self):
        self.data_path = DATA_PATH
        self.cards_by_set = {}
        self.cards_by_set_rarity = {}
        self.pity_counter = {}  # 每个系列的保底计数器
        self.opened_legendaries = defaultdict(set)  # 记录已抽到的传说卡
        
    def load_card_data(self):
        """加载所有可收藏卡牌数据"""
        try:
            # 读取统计信息以获取所有扩展包
            stats_path = os.path.join(self.data_path, "stats.json")
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            # 遍历所有扩展包
            for set_key in stats['sets']:
                # 确保set_key是扩展包的英文ID，不再使用旧的"英文ID_中文名"格式
                set_id = set_key
                
                # 构建扩展包数据路径
                set_path = os.path.join(self.data_path, set_key, "all_cards.json")
                if os.path.exists(set_path):
                    with open(set_path, 'r', encoding='utf-8') as f:
                        cards = json.load(f)
                    
                    # 只保留可收藏的卡牌
                    collectible_cards = [card for card in cards if card.get('collectible', False)]
                    
                    if collectible_cards:
                        # 保存扩展包的所有卡牌，name字段将暂时保存英文ID
                        # 稍后会使用HearthstoneDisplayManager进行本地化处理
                        self.cards_by_set[set_id] = {
                            'name': set_id,  # 使用ID作为name，便于后续使用display_manager处理
                            'cards': collectible_cards
                        }
                        
                        # 按稀有度分类卡牌
                        cards_by_rarity = defaultdict(list)
                        for card in collectible_cards:
                            rarity = card.get('rarity', 'COMMON')
                            cards_by_rarity[rarity].append(card)
                        
                        self.cards_by_set_rarity[set_id] = cards_by_rarity
                        
                        # 初始化保底计数器
                        self.pity_counter[set_id] = 0
            
            print(f"已加载 {len(self.cards_by_set)} 个扩展包的卡牌数据")
            return len(self.cards_by_set)
            
        except Exception as e:
            print(f"加载卡牌数据时出错: {e}")
            raise e
    
    def get_cards_by_set(self, set_id):
        """获取指定扩展包的所有卡牌
        
        Args:
            set_id: 扩展包ID
            
        Returns:
            list: 该扩展包的所有卡牌列表
        """
        set_data = self.cards_by_set.get(set_id)
        if set_data and 'cards' in set_data:
            return set_data['cards']
        return []


class PackSimulator:
    """卡包模拟器核心"""
    def __init__(self, card_data_manager, rarity_probabilities=None):
        self.card_manager = card_data_manager
        self.rarity_probabilities = rarity_probabilities or RARITY_PROBABILITIES
        self.guarantee_rare_or_higher = GUARANTEE_RARE_OR_HIGHER
        self.legendary_pity_timer = LEGENDARY_PITY_TIMER
        # 记录每个扩展包是否已经抽到第一张传说
        self.first_legendary_obtained = {}
        # 记录每个扩展包已抽取的包数（用于前10包保底）
        self.packs_opened = {}
        
    def simulate_pack_opening(self, set_id):
        """模拟单个卡包的抽卡过程"""
        try:
            if set_id not in self.card_manager.cards_by_set_rarity:
                print(f"警告: 扩展包 {set_id} 的按稀有度分类数据不存在")
                # 返回备选方案
                if set_id in self.card_manager.cards_by_set and self.card_manager.cards_by_set[set_id]['cards']:
                    all_cards = self.card_manager.cards_by_set[set_id]['cards']
                    return random.sample(all_cards, min(5, len(all_cards)))
                else:
                    raise ValueError(f"扩展包 {set_id} 没有可用卡牌数据")
            
            # 初始化当前扩展包的状态记录
            if set_id not in self.first_legendary_obtained:
                self.first_legendary_obtained[set_id] = False
            if set_id not in self.packs_opened:
                self.packs_opened[set_id] = 0
                
            # 增加已开包计数
            self.packs_opened[set_id] += 1
            
            cards_by_rarity = self.card_manager.cards_by_set_rarity[set_id]
            
            # 检查是否有足够的卡牌数据
            has_enough_cards = True
            missing_rarities = []
            for rarity in self.rarity_probabilities:
                if rarity not in cards_by_rarity or len(cards_by_rarity[rarity]) == 0:
                    has_enough_cards = False
                    missing_rarities.append(rarity)
            
            if not has_enough_cards:
                print(f"警告: 扩展包 {set_id} 缺少以下稀有度的卡牌: {', '.join(missing_rarities)}")
                # 如果某个稀有度没有卡牌，则随机从所有卡牌中抽取
                all_cards = self.card_manager.cards_by_set[set_id]['cards']
                if not all_cards:
                    raise ValueError(f"扩展包 {set_id} 没有可用卡牌数据")
                return random.sample(all_cards, min(5, len(all_cards)))
            
            # 保底机制处理
            guaranteed_legendary = False
            
            # 前10包保底逻辑：如果未抽到传说且当前是第10包，强制出传说
            if not self.first_legendary_obtained[set_id] and self.packs_opened[set_id] == 10:
                guaranteed_legendary = True
                print(f"扩展包 {set_id} 第10包保底触发，必出传说")
            # 每40包保底逻辑：仅在已经抽到第一张传说后生效
            elif self.first_legendary_obtained[set_id]:
                self.card_manager.pity_counter[set_id] += 1
                if self.card_manager.pity_counter[set_id] >= self.legendary_pity_timer:
                    guaranteed_legendary = True
                    self.card_manager.pity_counter[set_id] = 0
                    print(f"扩展包 {set_id} 40包保底触发，必出传说")
            
            # 抽取5张卡片
            cards = []
            rarities = self.determine_pack_rarities(guaranteed_legendary)
            
            for rarity in rarities:
                try:
                    card = self.draw_card_of_rarity(set_id, rarity)
                    if card:
                        cards.append(card)
                        
                        # 如果抽到了传说卡
                        if card.get('rarity') == 'LEGENDARY':
                            # 记录已获得第一张传说
                            if not self.first_legendary_obtained[set_id]:
                                self.first_legendary_obtained[set_id] = True
                                print(f"扩展包 {set_id} 已抽到第一张传说，开始应用40包保底规则")
                                # 重置保底计数器
                                self.card_manager.pity_counter[set_id] = 0
                            # 已经抽到过传说，正常重置40包保底计数
                            else:
                                self.card_manager.pity_counter[set_id] = 0
                except Exception as e:
                    print(f"抽取{rarity}稀有度卡牌时出错: {e}")
                    # 继续尝试抽取其他卡牌
            
            # 确保返回5张卡片
            while len(cards) < 5:
                # 如果卡片不足5张，从所有卡牌中随机补充
                all_cards = self.card_manager.cards_by_set[set_id]['cards']
                if not all_cards:
                    raise ValueError(f"扩展包 {set_id} 没有可用卡牌数据")
                cards.append(random.choice(all_cards))
            
            return cards
            
        except Exception as e:
            print(f"模拟卡包抽取过程中出错: {e}")
            # 尝试使用备选方案
            try:
                if set_id in self.card_manager.cards_by_set and self.card_manager.cards_by_set[set_id]['cards']:
                    all_cards = self.card_manager.cards_by_set[set_id]['cards']
                    return random.sample(all_cards, min(5, len(all_cards)))
            except:
                pass
            # 如果备选方案也失败，重新抛出异常
            raise
    
    def draw_card_of_rarity(self, set_id, rarity):
        """抽取指定稀有度的卡牌，对传说卡进行特殊处理"""
        try:
            if set_id not in self.card_manager.cards_by_set_rarity:
                return None
                
            cards_by_rarity = self.card_manager.cards_by_set_rarity[set_id]
            available_cards = cards_by_rarity.get(rarity, [])
            
            # 如果没有该稀有度的卡牌，尝试使用更高稀有度
            if not available_cards and rarity != 'LEGENDARY':
                for higher_rarity in ['LEGENDARY', 'EPIC', 'RARE']:
                    if higher_rarity in cards_by_rarity and cards_by_rarity[higher_rarity]:
                        available_cards = cards_by_rarity[higher_rarity]
                        break
            
            if not available_cards:
                print(f"扩展包 {set_id} 没有可用的 {rarity} 稀有度卡牌")
                return None
                
            # 对传说卡进行特殊处理
            if rarity == 'LEGENDARY':
                # 获取该扩展包中所有传说卡
                all_legendaries = cards_by_rarity.get('LEGENDARY', [])
                if not all_legendaries:
                    print(f"扩展包 {set_id} 没有传说卡")
                    return None
                    
                # 已抽到的传说卡ID集合
                opened_legendary_ids = self.card_manager.opened_legendaries[set_id]
                
                # 检查是否已抽到所有传说卡
                if len(opened_legendary_ids) >= len(all_legendaries):
                    print(f"扩展包 {set_id} 所有传说卡都已抽到，随机抽取一张")
                    # 如果已抽到所有传说，随机抽取一张
                    return random.choice(all_legendaries)
                else:
                    # 否则只能抽还没抽到过的传说
                    unopened_legendaries = [card for card in all_legendaries 
                                          if card.get('id', '') not in opened_legendary_ids]
                    if unopened_legendaries:
                        return random.choice(unopened_legendaries)
                    else:
                        # 理论上不应该到这里，但以防万一
                        print(f"扩展包 {set_id} 未抽到的传说卡计算错误，随机抽取一张")
                        return random.choice(all_legendaries)
            else:
                # 非传说卡正常抽取
                return random.choice(available_cards)
                
        except Exception as e:
            print(f"抽取卡牌时出错: {e}, set_id={set_id}, rarity={rarity}")
            # 如果出错，返回None让调用者处理
            return None
    
    def determine_pack_rarities(self, guaranteed_legendary=False):
        """确定一个卡包中5张卡的稀有度"""
        rarities = []
        
        # 如果保证传说，直接添加一张传说
        if guaranteed_legendary:
            rarities.append('LEGENDARY')
            remaining_cards = 4
        else:
            remaining_cards = 5
        
        # 确保至少有一张稀有或更高
        if self.guarantee_rare_or_higher and 'LEGENDARY' not in rarities:
            # 按照概率抽取一张稀有+的卡牌
            higher_rarities = ['LEGENDARY', 'EPIC', 'RARE']
            weights = [self.rarity_probabilities.get(r, 0) for r in higher_rarities]
            
            # 归一化权重
            total_weight = sum(weights)
            if total_weight > 0:
                normalized_weights = [w/total_weight for w in weights]
                selected_rarity = random.choices(higher_rarities, weights=normalized_weights, k=1)[0]
                rarities.append(selected_rarity)
                remaining_cards -= 1
        
        # 抽取剩余卡片
        for _ in range(remaining_cards):
            rarity_items = list(self.rarity_probabilities.items())
            rarities_list = [r[0] for r in rarity_items]
            weights = [r[1] for r in rarity_items]
            
            selected_rarity = random.choices(rarities_list, weights=weights, k=1)[0]
            rarities.append(selected_rarity)
        
        return rarities
        
    def add_legendary_record(self, set_id, card_id):
        """添加已抽到的传说卡记录"""
        try:
            if set_id and card_id:
                self.card_manager.opened_legendaries[set_id].add(card_id)
        except Exception as e:
            print(f"添加传说卡记录时出错: {e}")
            # 但不会抛出异常中断流程
    
    def reset_legendary_records(self):
        """重置传说卡记录和保底计数器"""
        try:
            # 清空已抽到传说的记录
            self.card_manager.opened_legendaries = defaultdict(set)
            # 重置保底计数器
            for set_id in self.card_manager.pity_counter:
                self.card_manager.pity_counter[set_id] = 0
            # 重置首次传说记录
            self.first_legendary_obtained = {}
            # 重置已开包数记录
            self.packs_opened = {}
        except Exception as e:
            print(f"重置传说卡记录时出错: {e}")
            raise e
    
    def set_rarity_probabilities(self, probabilities):
        """设置各稀有度的概率"""
        # 验证概率总和是否接近1
        total = sum(probabilities.values())
        # 允许更小范围的浮点误差，以适应四位小数精度
        if 0.9999 <= total <= 1.0001:
            self.rarity_probabilities = probabilities
            print(f"概率设置成功，总和为: {total}")
            return True
        else:
            print(f"概率总和 {total} 不接近1，无法设置")
            return False

class HearthstoneDisplayManager:
    """炉石传说卡牌显示管理器，负责转换卡牌信息的显示格式"""
    
    def __init__(self):
        """初始化显示管理器，加载所有配置"""
        self.class_name_map = config.CLASS_NAMES
        self.rarity_name_map = config.RARITY_NAMES
        self.set_name_map = config.SET_NAMES
        
    def get_localized_class_name(self, class_key: str) -> str:
        """获取本地化的职业名称"""
        return self.class_name_map.get(class_key, class_key)
        
    def get_localized_rarity_name(self, rarity_key: str) -> str:
        """获取本地化的稀有度名称"""
        return self.rarity_name_map.get(rarity_key, rarity_key)
        
    def get_localized_set_name(self, set_key: str) -> str:
        """获取本地化的扩展包名称"""
        return self.set_name_map.get(set_key, set_key)
    
    def localize_card_data(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """将卡牌数据中的关键字段本地化（不修改原始数据）"""
        localized_card = card.copy()
        
        # 添加本地化字段
        if 'set' in card:
            localized_card['localizedSet'] = self.get_localized_set_name(card['set'])
            
        if 'cardClass' in card:
            localized_card['localizedClass'] = self.get_localized_class_name(card['cardClass'])
            
        if 'rarity' in card:
            localized_card['localizedRarity'] = self.get_localized_rarity_name(card['rarity'])
            
        return localized_card
    
    def localize_card_list(self, cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将卡牌列表中的所有卡牌数据本地化"""
        return [self.localize_card_data(card) for card in cards]
    
    def get_display_path(self, card_set: str, card_class: Optional[str] = None, 
                         card_rarity: Optional[str] = None) -> str:
        """获取显示路径（只使用本地化名称）"""
        path_parts = []
        
        # 添加扩展包（必须）
        set_display = self.get_localized_set_name(card_set)
        path_parts.append(f"{set_display}")
        
        # 添加职业（可选）
        if card_class:
            class_display = self.get_localized_class_name(card_class)
            path_parts.append(f"{class_display}")
        
        # 添加稀有度（可选）
        if card_rarity:
            rarity_display = self.get_localized_rarity_name(card_rarity)
            path_parts.append(f"{rarity_display}")
        
        return "/".join(path_parts)
    
    def display_card_info(self, card: Dict[str, Any]) -> None:
        """显示一张卡牌的关键信息（只使用本地化显示）"""
        localized = self.localize_card_data(card)
        
        print(f"卡牌: {localized.get('name', 'Unknown')}")
        print(f"ID: {localized.get('id', 'Unknown')}")
        print(f"扩展包: {localized.get('localizedSet', 'Unknown')}")
        print(f"职业: {localized.get('localizedClass', 'Unknown')}")
        print(f"稀有度: {localized.get('localizedRarity', 'Unknown')}")
        print(f"费用: {localized.get('cost', 'Unknown')}")
        
        if 'attack' in card and 'health' in card:
            print(f"攻击/生命: {localized.get('attack', '?')}/{localized.get('health', '?')}")
            
        if 'text' in card and card['text']:
            print(f"卡牌文本: {localized.get('text', '')}")
            
        print("---")
    
    def display_statistics(self, stats_file: str) -> None:
        """显示统计信息（只使用本地化名称）"""
        if not os.path.exists(stats_file):
            print(f"统计文件不存在: {stats_file}")
            return
        
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            print("炉石传说卡牌统计信息:")
            print(f"总卡牌数量: {stats.get('total_cards', 0)}")
            print(f"可收藏卡牌数量: {stats.get('collectible_cards', 0)}")
            
            if 'sets' in stats:
                print("\n扩展包统计:")
                for set_name, count in sorted(stats['sets'].items(), key=lambda x: x[1], reverse=True):
                    localized_name = self.get_localized_set_name(set_name)
                    print(f"- {localized_name}: {count}张卡牌")
        except Exception as e:
            print(f"读取统计信息时出错: {e}")

# 示例用法
if __name__ == "__main__":
    display_manager = HearthstoneDisplayManager()
    
    # 显示一些扩展包名称的本地化示例
    print("扩展包名称本地化示例:")
    test_sets = ['EMERALD_DREAM', 'SPACE', 'TITANS', 'BATTLE_OF_THE_BANDS', 'CORE']
    for set_name in test_sets:
        localized = display_manager.get_localized_set_name(set_name)
        print(f"- {set_name} -> {localized}")
    
    # 演示如何使用本地化路径
    print("\n显示路径示例:")
    path1 = display_manager.get_display_path('EMERALD_DREAM', 'MAGE', 'LEGENDARY')
    path2 = display_manager.get_display_path('TITANS', 'WARLOCK')
    print(f"路径1: {path1}")
    print(f"路径2: {path2}")
    
    # 模拟读取卡牌数据并显示
    print("\n模拟卡牌数据显示:")
    sample_card = {
        "id": "EDR_001",
        "name": "翡翠守护者",
        "set": "EMERALD_DREAM",
        "cardClass": "DRUID",
        "rarity": "LEGENDARY",
        "cost": 7,
        "attack": 5,
        "health": 5,
        "text": "<b>嘲讽</b>，<b>战吼：</b>获得+1/+1，在本局对战中每有一个友方生物死亡，重复一次。",
        "collectible": True
    }
    
    display_manager.display_card_info(sample_card) 