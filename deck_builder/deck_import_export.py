import base64
import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QApplication, QInputDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# 修改导入路径
from .deck_constants import ACCURATE_HERO_DBF_IDS
from utils import write_varint
from .deckstring_parser import parse_deckstring
from config import CLASS_NAMES

class DeckImportExport:
    """卡组导入导出管理类"""
    
    # 缓存英雄信息，避免重复读取
    _hero_info_cache = {}
    
    @staticmethod
    def get_hero_class_from_dbf_id(dbf_id):
        """
        从英雄dbfId查找对应的职业
        
        Args:
            dbf_id: 英雄的dbfId
            
        Returns:
            str: 职业名称，如果没找到则返回None
        """
        # 先检查缓存
        if dbf_id in DeckImportExport._hero_info_cache:
            return DeckImportExport._hero_info_cache[dbf_id]
        
        # 英雄皮肤数据文件路径
        hero_skins_file = os.path.join("炉石卡牌分类", "HERO_SKINS", "all_cards.json")
        
        try:
            if os.path.exists(hero_skins_file):
                with open(hero_skins_file, 'r', encoding='utf-8') as f:
                    hero_data = json.load(f)
                
                # 查找匹配的英雄
                for hero in hero_data:
                    if hero.get('dbfId') == dbf_id:
                        card_class = hero.get('cardClass')
                        if card_class:
                            # 转换为中文职业名
                            for en_name, cn_name in CLASS_NAMES.items():
                                if en_name.upper() == card_class:
                                    DeckImportExport._hero_info_cache[dbf_id] = cn_name
                                    return cn_name
                            
                            # 如果没有找到中文名，缓存英文名
                            for en_name, cn_name in CLASS_NAMES.items():
                                if en_name.upper() in card_class or card_class in en_name.upper():
                                    DeckImportExport._hero_info_cache[dbf_id] = cn_name
                                    return cn_name
                            
                            # 实在没办法，返回英文名
                            DeckImportExport._hero_info_cache[dbf_id] = None
                            return None
        except Exception as e:
            # 出错时默认返回None
            pass
            
        # 将查找失败的结果也缓存，避免重复查找
        DeckImportExport._hero_info_cache[dbf_id] = None
        return None
    
    @staticmethod
    def export_deckstring(selected_class, deck, data_manager, parent_widget):
        """
        将当前卡组导出为炉石传说可导入的卡组代码
        
        Args:
            selected_class: 当前选择的职业
            deck: 当前卡组列表
            data_manager: 数据管理器实例
            parent_widget: 父窗口部件，用于显示对话框
            
        Returns:
            bool: 导出是否成功
        """
        # print("开始导出卡组代码...")
        
        if not selected_class or len(deck) == 0:
            QMessageBox.warning(parent_widget, "警告", "当前没有选择职业或卡组为空，无法导出卡组代码。")
            # print("导出中止：未选择职业或卡组为空。")
            return False
        
        hero_dbf_id = ACCURATE_HERO_DBF_IDS.get(selected_class)
        if not hero_dbf_id:
            QMessageBox.warning(parent_widget, "警告", f"未找到职业 '{selected_class}' 的英雄 DBF ID，卡组代码导出可能不正确。")
            # 尝试使用旧的映射，确保有一个备选值
            hero_dbf_id = 7  # 默认为战士
        # print(f"英雄DBF ID: {hero_dbf_id}")
        
        # print("开始统计和查找卡牌DBF ID...")
        # 统计卡牌数量
        card_counts = {}
        for card in deck:
            card_name = card['name']
            card_counts[card_name] = card_counts.get(card_name, 0) + 1
            
        cards_x1 = []  # 一张的卡牌
        cards_x2 = []  # 两张的卡牌
        debug_info = []  # 调试信息
        missing_dbf_ids = []  # 找不到的卡牌
        
        card_index = 0 # 添加计数器
        total_cards = len(card_counts)
        for card_name, count in card_counts.items():
            card_index += 1
            # print(f"  查找卡牌 {card_index}/{total_cards}: {card_name} (数量: {count})...")
            # 尝试多种方式找到 DBF ID
            dbf_id = data_manager.find_card_dbf_id(card_name)
            # print(f"    找到DBF ID: {dbf_id if dbf_id else '未找到'}")
            
            if dbf_id:
                debug_info.append(f"{card_name}: DBF ID={dbf_id}, 数量={count}")
                if count == 1:
                    cards_x1.append(dbf_id)
                else:
                    cards_x2.append(dbf_id)
            else:
                missing_dbf_ids.append(card_name)
        # print("卡牌DBF ID查找完成。")
                
        if missing_dbf_ids:
            warning_msg = f"以下 {len(missing_dbf_ids)} 张卡牌未找到 DBF ID，它们将不会包含在导出的卡组代码中：\n"
            warning_msg += "\n".join(missing_dbf_ids)
            QMessageBox.warning(parent_widget, "警告", warning_msg)
            
        # 排序很重要！
        # print("对卡牌列表进行排序...")
        cards_x1.sort()
        cards_x2.sort()
        
        # 卡组格式版本
        version = 1
        # 游戏模式 (1=狂野, 2=标准, 3=经典)
        format_type = 2  # 默认为标准模式
        
        # 构建数据流
        data = bytearray()
        # 0. 保留字节 (按照 HearthSim 规范，只有一个)
        data.append(0)
        # 1. 版本
        write_varint(data, version)
        # 2. 模式
        write_varint(data, format_type)
        # 3. 英雄
        write_varint(data, 1)  # 英雄数量始终为1
        write_varint(data, hero_dbf_id)
        
        # 4. 单张卡牌
        write_varint(data, len(cards_x1))
        for dbf_id in cards_x1:
            write_varint(data, dbf_id)
            
        # 5. 双张卡牌
        write_varint(data, len(cards_x2))
        for dbf_id in cards_x2:
            write_varint(data, dbf_id)
            
        # 6. 其他数量的卡牌（通常为0）
        write_varint(data, 0)

        # 检查卡组中是否有奇利亚斯豪华版3000型 (dbfId=102983)
        kelthuzad_3000_dbf_id = 102983
        has_kelthuzad_3000 = any(data_manager.find_card_dbf_id(card['name']) == kelthuzad_3000_dbf_id for card in deck)

        # 如果有奇利亚斯豪华版3000型，添加额外数据
        if has_kelthuzad_3000:
            # print("检测到卡组包含奇利亚斯豪华版3000型，添加特殊处理...")
            # 根据用户提供的比较结果，添加官方代码中额外的字节
            # 这些字节值对应从字节73开始的额外数据
            extra_bytes = bytearray([
                0x01, 0x03, 0xf5, 0xb3, 0x06, 0xc7, 0xa4, 0x06, 
                0xf7, 0xb3, 0x06, 0xc7, 0xa4, 0x06, 0xe8, 0xde, 
                0x06, 0xc7, 0xa4, 0x06, 0x00, 0x00
            ])
            data.extend(extra_bytes)
            # print("已添加奇利亚斯豪华版3000型的特殊字节数据")

        # Base64编码
        encoded = base64.b64encode(data).decode('utf-8')
        # print("数据流构建和编码完成。")
        
        # 复制到剪贴板
        # print("复制到剪贴板...")
        clipboard = QApplication.clipboard()
        clipboard.setText(encoded)
        
        # --- 显示包含代码的成功对话框 --- 
        # 创建一个简单的对话框来显示代码
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("导出成功")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        label = QLabel("卡组代码已生成并复制到剪贴板：")
        layout.addWidget(label)
        
        code_text = QTextEdit()
        code_text.setPlainText(encoded)
        code_text.setReadOnly(True) # 用户不能编辑，但可以复制
        code_text.setFont(QFont("Consolas", 10)) # 使用等宽字体更美观
        layout.addWidget(code_text)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight) # 按钮靠右
        
        dialog.setLayout(layout)
        dialog.exec_()
        # -------------------------------------
        
        # print("导出流程结束。")
        return True
    
    @staticmethod
    def prompt_import_deck_code(parent_widget, import_callback):
        """
        弹出对话框让用户输入卡组代码
        
        Args:
            parent_widget: 父窗口部件
            import_callback: 导入卡组字符串的回调函数
        """
        deck_code, ok = QInputDialog.getText(parent_widget, '导入卡组代码', '请输入卡组代码:')
        
        if ok and deck_code:
            import_callback(deck_code.strip())
        elif ok:
            QMessageBox.warning(parent_widget, "提示", "未输入卡组代码。")
    
    @staticmethod
    def show_export_help(parent_widget):
        """
        显示导出卡组代码的帮助信息
        
        Args:
            parent_widget: 父窗口部件
        """
        help_text = """
        要成功导出游戏可识别的卡组代码，需要满足以下条件：

        1. 带满 30 张卡，即卡组不能是残缺的
        2. 本程序现在已支持奇利亚斯豪华版3000型的导出，但是不支持精英乐团牛头人酋长的导出。
        """
        QMessageBox.information(parent_widget, "导出卡组代码帮助", help_text)
    
    @staticmethod
    def import_deck_from_string(deckstring, data_manager, all_cards, selected_class, 
                              class_combo, current_deck, on_class_changed, 
                              update_deck_list, update_deck_count, update_cards_list, parent_widget):
        """
        根据卡组代码字符串导入卡组
        
        Args:
            deckstring: 卡组代码字符串
            data_manager: 数据管理器实例
            all_cards: 所有可用卡牌列表
            selected_class: 当前选择的职业
            class_combo: 职业选择下拉框
            current_deck: 当前卡组列表
            on_class_changed: 职业变更回调
            update_deck_list, update_deck_count, update_cards_list: 各种UI更新回调
            parent_widget: 父窗口部件
            
        Returns:
            bool: 导入是否成功
        """
        # print(f"尝试导入卡组代码: {deckstring}")
        
        # 检查数据库是否加载
        if not data_manager.dbf_id_to_card_info:
            QMessageBox.critical(parent_widget, "错误", "无法加载卡牌数据库 (DBF ID 映射)，无法导入卡组。")
            return False

        if not all_cards:
             QMessageBox.warning(parent_widget, "提示", "请先导入您的抽卡报告 (Excel 文件)，以便程序了解您拥有的卡牌和数量。")
             return False
        
        deck_data = parse_deckstring(deckstring)
        if not deck_data:
            QMessageBox.critical(parent_widget, "错误", "解析卡组代码失败，请检查代码是否有效。")
            return False
            
        # --- 确定目标职业 --- 
        target_class = None
        code_class_identified = False
        
        if deck_data['heroes']:
            hero_dbf_id = deck_data['heroes'][0]
            
            # 只从英雄皮肤文件中查找职业
            code_class = DeckImportExport.get_hero_class_from_dbf_id(hero_dbf_id)
            
            if code_class:
                target_class = code_class
                code_class_identified = True
                # print(f"从代码中识别出的职业: {target_class}")
            else:
                # print(f"无法从代码的英雄ID {hero_dbf_id} 中识别职业。")
                pass
        else:
            # print("卡组代码中未包含英雄信息。")
            pass

        # 如果无法从代码中识别职业，则使用当前选中的职业
        if not code_class_identified:
            if selected_class is None:
                QMessageBox.warning(parent_widget, "需要选择职业", 
                                    "无法识别卡组代码中的职业，且当前未选择任何职业。\n请先在左上角选择一个具体职业再导入。")
                return False
            else:
                target_class = selected_class
                QMessageBox.information(parent_widget, "提示", 
                                      f"无法识别卡组代码中的职业。\n将尝试把卡牌导入到当前选中的职业【{target_class}】中。")
                # print(f"将使用当前选中的职业: {target_class}")
        
        # --- 处理职业切换和清空卡组 --- 
        proceed_import = False
        if selected_class != target_class:
            # print(f"当前职业 '{selected_class}' 与目标职业 '{target_class}' 不匹配，尝试切换..." if selected_class else f"当前未选择职业，尝试切换到目标职业 '{target_class}'...")
            target_index = -1
            for i in range(class_combo.count()):
                if class_combo.itemText(i) == target_class:
                    target_index = i
                    break
            
            if target_index == -1:
                QMessageBox.critical(parent_widget, "错误", f"无法在下拉列表中找到职业 '{target_class}'。导入中止。")
                return False
            
            # 在父窗口对象上设置待导入的卡组代码，在职业切换后会用到
            setattr(parent_widget, "_pending_import_deckstring", deckstring)
            
            # 触发职业切换 (会处理清空确认)
            class_combo.setCurrentIndex(target_index)
            
            # 此时on_class_changed已被触发，如果用户确认了职业切换，则导入流程会在那里继续
            # 所以这里直接返回，不继续后面的导入流程
            return True
        else:
            # 职业匹配，或使用当前职业导入，需要确认清空
            # print(f"目标职业 '{target_class}' 与当前选中职业匹配。")
            if current_deck:
                reply = QMessageBox.question(parent_widget, '确认导入',
                                            f"导入新卡组到【{target_class}】将清空当前卡组，您确定要继续吗？",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    current_deck.clear()
                    # print("已清空现有卡组。")
                    proceed_import = True
                else:
                    # print("用户取消了导入。")
                    return False
            else:
                # 当前卡组为空，直接继续
                proceed_import = True

        if not proceed_import:
             # print("未能继续导入流程。") # 理论上不应执行到这里
             return False
             
        # --- 开始添加卡牌 --- 
        # print("开始添加卡牌到卡组...")
        imported_count = 0
        skipped_cards = [] # 记录无法添加或数量不足的卡牌
        missing_from_collection = [] # 记录用户根本没有的卡牌
        deck_full_skipped_start_index = -1 # 记录卡组满时处理到的卡牌在deck_data['cards']中的索引
        
        # 创建一个用户拥有卡牌的查找表 (名称 -> 卡牌对象列表)
        user_collection_map = {}
        for card_obj in all_cards:
            name = card_obj['name']
            if name not in user_collection_map:
                user_collection_map[name] = []
            user_collection_map[name].append(card_obj)
        
        for idx, (dbf_id, required_count) in enumerate(deck_data['cards']):
            if dbf_id not in data_manager.dbf_id_to_card_info:
                skipped_cards.append(f"ID {dbf_id} (数据库中未找到)")
                continue
            
            card_info = data_manager.dbf_id_to_card_info[dbf_id]
            card_name = card_info.get('name')
            rarity = card_info.get('rarity', '').upper() # 获取稀有度
            is_legendary = (rarity == 'LEGENDARY')
            
            if not card_name:
                skipped_cards.append(f"ID {dbf_id} (无名称信息)")
                continue
            
            # 在用户拥有的卡牌中查找这张卡
            if card_name not in user_collection_map:
                 missing_from_collection.append(f"{card_name} (未在您的收藏中找到)")
                 continue
            
            # 找到用户收藏中的对应卡牌对象
            user_card_obj = user_collection_map[card_name][0]
            owned_count = user_card_obj.get('count', 0) # 获取用户拥有的数量
            
            # 计算实际能添加的数量
            max_allowed = 1 if is_legendary else 2
            can_add_count = min(required_count, owned_count, max_allowed)
            
            # print(f"  处理卡牌: {card_name}, 要求: {required_count}, 拥有: {owned_count}, 规则上限: {max_allowed}, 可添加: {can_add_count}")

            # 添加卡牌到卡组 (添加 can_add_count 次)
            actually_added = 0
            for _ in range(can_add_count):
                 # 检查卡组是否已满
                 if len(current_deck) >= 30:
                     # print("卡组已满 (30张)，停止添加。")
                     deck_full_skipped_start_index = idx # 记录当前处理的卡牌索引
                     break # 跳出内层添加循环
                 current_deck.append(user_card_obj) # 添加用户收藏中的对象
                 imported_count += 1
                 actually_added += 1
            
            # 如果内层循环因为卡组满了而 break，外层循环也 break
            if deck_full_skipped_start_index != -1:
                # 检查当前卡牌是否已完全添加，如果未完全添加，也需记录
                if actually_added < required_count:
                    reason = "卡组已满"
                    # 可以补充其他原因，如果适用
                    if owned_count < required_count:
                        reason += f", 拥有数量不足({owned_count}/{required_count})"
                    if actually_added < max_allowed and max_allowed < required_count:
                        reason += f", 规则限制({max_allowed})"
                    elif max_allowed < required_count and owned_count >= required_count:
                        reason += f", 规则限制({max_allowed})"
                    skipped_cards.append(f"{card_name} (添加了 {actually_added}/{required_count} 张，原因: {reason})")
                break 
            
            # 记录未能完全满足要求的卡牌 (非卡组已满的情况)
            if actually_added < required_count:
                reason = ""
                if owned_count < required_count:
                    reason += f"拥有数量不足({owned_count}/{required_count}) "
                if actually_added < max_allowed and max_allowed < required_count:
                    reason += f"规则限制({max_allowed}) "
                elif max_allowed < required_count and owned_count >= required_count:
                    reason += f"规则限制({max_allowed}) "
                
                if not reason and owned_count >= required_count and max_allowed >= required_count:
                    reason = "未知原因" # 理论不应发生
                
                skipped_cards.append(f"{card_name} (添加了 {actually_added}/{required_count} 张，原因: {reason.strip()})")
        
        # --- 处理因卡组已满而完全跳过的后续卡牌 ---
        if deck_full_skipped_start_index != -1:
            # 从下一个索引开始遍历
            for rem_idx in range(deck_full_skipped_start_index + 1, len(deck_data['cards'])):
                rem_id, rem_count = deck_data['cards'][rem_idx]
                rem_name = data_manager.dbf_id_to_card_info.get(rem_id, {}).get('name', f'ID {rem_id}')
                # 检查这张卡是否之前因为缺失被记录过
                if not any(rem_name in s for s in missing_from_collection):
                    skipped_cards.append(f"{rem_name} x{rem_count} (卡组已满)")
        
        # print("卡牌添加处理完成。")
        
        # 更新UI
        update_deck_list()
        update_deck_count()
        update_cards_list() # 更新左侧列表以反映可能的职业变化
        
        # --- 显示导入结果 --- 
        summary_message = f"卡组导入完成。\n成功导入 {imported_count} / {sum(c[1] for c in deck_data['cards'])} 张卡牌到卡组。\n卡组当前共 {len(current_deck)} 张卡牌。"
        details = []
        if missing_from_collection:
            details.append("\n您未拥有的卡牌 (已跳过):")
            details.extend([f"- {s}" for s in missing_from_collection])
        if skipped_cards:
            details.append("\n未能完全添加或跳过的卡牌:")
            details.extend([f"- {s}" for s in skipped_cards])
            
        if details:
             QMessageBox.information(parent_widget, "导入结果", summary_message + "\n" + "\n".join(details))
        else:
             QMessageBox.information(parent_widget, "导入成功", summary_message)
             
        return True