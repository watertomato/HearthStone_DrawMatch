#!/usr/bin/env python
# -*- coding: utf-8 -*-

from config import SET_NAMES, RARITY_NAMES, CLASS_NAMES

class TextDisplayManager:
    """
    负责文本显示的管理器，处理卡牌名称、稀有度、职业等的本地化显示
    """
    
    def __init__(self):
        """初始化显示管理器"""
        # 加载本地化映射
        self.set_names = SET_NAMES
        self.rarity_names = RARITY_NAMES
        self.class_names = CLASS_NAMES
        
        # 卡牌名称缓存
        self.card_name_cache = {}
    
    def get_localized_set_name(self, set_id):
        """获取扩展包的本地化名称"""
        if not set_id:
            return "未知扩展"
        
        # 返回配置中的中文名称，如果不存在则返回原始ID
        return self.set_names.get(set_id, set_id)
    
    def get_localized_rarity_name(self, rarity_id):
        """获取稀有度的本地化名称"""
        if not rarity_id:
            return "未知稀有度"
        
        # 返回配置中的中文名称，如果不存在则返回原始ID
        return self.rarity_names.get(rarity_id, rarity_id)
    
    def get_localized_class_name(self, class_id):
        """获取职业的本地化名称"""
        if not class_id:
            return "未知职业"
        
        # 返回配置中的中文名称，如果不存在则返回原始ID
        return self.class_names.get(class_id, class_id)
    
    def get_localized_card_name(self, card_name):
        """
        获取卡牌的本地化名称
        未来可以实现卡牌名称的本地化查询和缓存
        """
        # 当前版本直接返回原名，未来可扩展为从本地化文件或数据库中查询
        return card_name
    
    def format_localized_name(self, name, original_id=None):
        """
        格式化本地化名称，仅返回中文名称而不包含英文ID和括号
        """
        return name 