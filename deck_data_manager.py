import os
import json
from PyQt5.QtWidgets import QMessageBox
from utils import normalize_card_name

class DeckDataManager:
    """卡组数据管理类"""
    
    def __init__(self):
        """初始化卡组数据管理器"""
        self.card_name_to_dbf_id = {}  # 卡牌名称到DBF ID的映射
        self.normalized_name_to_dbf_id = {}  # 规范化名称到DBF ID的映射
        self.dbf_id_to_card_info = {}  # DBF ID到卡牌信息的映射
    
    def load_card_data(self, parent_widget=None):
        """
        加载 card_infos.json 并构建映射，严格优先选择 CORE 系列卡牌。
        
        Args:
            parent_widget: 父窗口部件，用于显示错误消息框
            
        Returns:
            bool: 加载是否成功
        """
        json_path = "hsJSON卡牌数据/card_infos.json"
        if not os.path.exists(json_path):
            if parent_widget:
                QMessageBox.critical(parent_widget, "错误", f"找不到卡牌数据文件：{json_path}\n无法实现卡组导出/导入功能。")
            return False
            
        try:
            print(f"Loading card data from {json_path}...")
            with open(json_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            self.card_name_to_dbf_id = {}
            normalized_name_to_dbf_id = {}
            self.dbf_id_to_card_info = {}
            
            print("正在构建卡牌名称到DBF ID的映射 (优先CORE系列)...")

            for card_data in all_data:
                dbf_id = card_data.get('dbfId')
                card_name = card_data.get('name')
                card_set = card_data.get('set')
                is_collectible = card_data.get('collectible', False)
                
                # 建立 DBF ID 到信息的完整映射
                if dbf_id:
                    self.dbf_id_to_card_info[dbf_id] = card_data
                
                # 处理可收集卡牌的名称->DBF ID 映射
                if is_collectible and card_name and dbf_id and card_set:
                    is_current_core = (card_set == "CORE")
                    normalized_name = normalize_card_name(card_name)
                    
                    # --- 处理原始名称映射 --- 
                    if card_name not in self.card_name_to_dbf_id:
                        # 如果名称不存在，直接添加
                        self.card_name_to_dbf_id[card_name] = dbf_id
                    else:
                        # 如果名称已存在，检查是否需要用CORE版本覆盖
                        existing_dbf_id = self.card_name_to_dbf_id[card_name]
                        existing_card_info = self.dbf_id_to_card_info.get(existing_dbf_id, {})
                        existing_set = existing_card_info.get('set')
                        is_existing_core = (existing_set == "CORE")
                        
                        # 仅当: 当前是CORE 且 已存在不是CORE 时，才覆盖
                        if is_current_core and not is_existing_core:
                            self.card_name_to_dbf_id[card_name] = dbf_id
                        # 在其他情况下 (包括两者都是CORE, 两者都不是CORE, 当前不是CORE但已存在是CORE), 保持不变
                        
                    # --- 处理规范化名称映射 --- 
                    if normalized_name not in normalized_name_to_dbf_id:
                        # 如果规范化名称不存在，直接添加
                        normalized_name_to_dbf_id[normalized_name] = dbf_id
                    else:
                        # 如果规范化名称已存在，检查是否需要用CORE版本覆盖
                        existing_dbf_id = normalized_name_to_dbf_id[normalized_name]
                        existing_card_info = self.dbf_id_to_card_info.get(existing_dbf_id, {})
                        existing_set = existing_card_info.get('set')
                        is_existing_core = (existing_set == "CORE")
                        
                        # 仅当: 当前是CORE 且 已存在不是CORE 时，才覆盖
                        if is_current_core and not is_existing_core:
                            normalized_name_to_dbf_id[normalized_name] = dbf_id
                        # 其他情况保持不变
            
            self.normalized_name_to_dbf_id = normalized_name_to_dbf_id
            
            print(f"Loaded {len(self.card_name_to_dbf_id)} collectible cards with CORE preference.")
            print(f"Created DBF ID map with {len(self.dbf_id_to_card_info)} entries.")
            return True
            
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            if parent_widget:
                QMessageBox.critical(parent_widget, "错误", f"加载卡牌数据 {json_path} 时出错：{str(e)}\n\n{traceback_str}")
            self.card_name_to_dbf_id = {} 
            self.normalized_name_to_dbf_id = {}
            self.dbf_id_to_card_info = {}
            return False
    
    def find_card_dbf_id(self, card_name):
        """
        尝试使用精确匹配找到卡牌的 DBF ID
        
        Args:
            card_name: 卡牌名称
            
        Returns:
            int 或 None: 找到的DBF ID，如果未找到则返回None
        """
        # 1. 直接使用卡牌名称查找
        if card_name in self.card_name_to_dbf_id:
            print(f"    找到DBF ID (直接匹配): {self.card_name_to_dbf_id[card_name]}")
            return self.card_name_to_dbf_id[card_name]
            
        # 2. 尝试使用规范化名称查找
        normalized_name = normalize_card_name(card_name)
        if normalized_name in self.normalized_name_to_dbf_id:
            print(f"    找到DBF ID (规范化匹配): {self.normalized_name_to_dbf_id[normalized_name]}")
            return self.normalized_name_to_dbf_id[normalized_name]
                
        print(f"    警告：未能通过精确匹配找到卡牌 '{card_name}' 的 DBF ID。")        
        return None 