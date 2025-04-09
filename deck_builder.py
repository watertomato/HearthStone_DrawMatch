import os
import sys
import pandas as pd

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 导入自定义模块
from config import CLASS_NAMES, RARITY_NAMES, SET_NAMES, CARD_TYPE_NAMES
from deck_constants import ACCURATE_HERO_DBF_IDS
from deck_data_manager import DeckDataManager
from deck_ui_components import DeckBuilderUI
from deck_import_export import DeckImportExport

class DeckBuilder(QMainWindow):
    def __init__(self):
        """初始化卡组构建器"""
        super().__init__()
        
        # 初始化数据
        self.all_cards = []  # 所有卡牌
        self.deck = []  # 当前卡组中的卡牌
        self.selected_class = None  # 当前选择的职业
        self.search_text = ""  # 搜索文本
        self.sort_column = -1  # 当前排序的列
        self.sort_order = Qt.AscendingOrder  # 当前排序顺序
        self.previous_class_index = 0 # 记录上一次选择的职业索引，默认为"全部职业"
        
        # 初始化数据管理器
        self.data_manager = DeckDataManager()
        
        # 字体设置
        self.base_font_size = 10 # 使用pt作为单位
        self.current_font = QFont() # 创建字体对象
        self.current_font.setPointSize(self.base_font_size)
        
        # 定义各列的目标宽度比例 (总和应接近1.0)
        self.column_proportions = [0.06, 0.14, 0.06, 0.10, 0.06, 0.08, 0.06, 0.08, 0.30, 0.06]
        
        # 初始化UI组件管理器
        self.ui = DeckBuilderUI(self)
        
        # 创建UI
        self.init_ui()
        
        # 加载卡牌数据
        self.data_manager.load_card_data(self)
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建UI组件
        self.ui.create_ui()
        
        # 创建菜单栏
        self.ui.create_menu_bar(self.set_font_size)

    def set_font_size(self, size):
        """设置表格和列表的字体大小"""
        self.current_font.setPointSize(size)
        # 应用到表格和列表
        self.ui.cards_table.setFont(self.current_font)
        self.ui.deck_list.setFont(self.current_font)
        
        # 调整行高以适应新字体
        self.ui.cards_table.resizeRowsToContents()

    def on_search_changed(self, text):
        """搜索文本改变时的处理"""
        self.search_text = text.lower()
        self.update_cards_list()
    
    def on_header_clicked(self, logical_index):
        """表头点击时的处理"""
        if self.sort_column == logical_index:
            # 如果点击的是当前排序列，则切换排序顺序
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # 如果点击的是新列，则设置为升序
            self.sort_column = logical_index
            self.sort_order = Qt.AscendingOrder
        
        # 应用排序
        self.ui.cards_table.sortItems(logical_index, self.sort_order)
    
    def import_report(self):
        """导入抽卡报告"""
        try:
            # 打开文件选择对话框
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择抽卡报告",
                os.path.join("抽卡报告"),
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # 读取Excel文件
            df = pd.read_excel(file_path, sheet_name='抽卡结果')

            # --- 容错：检查必需列是否存在 ---
            required_column = '卡牌名称'
            if required_column not in df.columns:
                QMessageBox.critical(self, "错误", f"导入失败：Excel文件中缺少必需的列 '{required_column}'。")
                return
            # ------------------------------
            
            # 清空现有数据
            self.all_cards = []
            self.deck = []
            self.ui.cards_table.setRowCount(0)
            self.ui.deck_list.clear()
            
            skipped_rows = 0
            # 处理每一行数据
            for index, row in df.iterrows(): 
                # --- 容错：检查必需列的值是否为空 ---
                card_name = str(row[required_column]).strip() if required_column in row and pd.notna(row[required_column]) else ""
                if not card_name:
                    skipped_rows += 1
                    print(f"Skipping row {index+2} because '{required_column}' is empty.")
                    continue 
                # -------------------------------------
                
                # --- 容错：读取可选列，不存在则使用默认值 ---
                # 读取拥有数量，默认为1
                owned_count = int(float(row['数量'])) if '数量' in df.columns and pd.notna(row['数量']) and row['数量'] > 0 else 1 
                card_class = str(row['职业']).strip() if '职业' in df.columns and pd.notna(row['职业']) else "中立"
                card_set = str(row['扩展包']) if '扩展包' in df.columns and pd.notna(row['扩展包']) else "未知"
                card_rarity = str(row['稀有度']) if '稀有度' in df.columns and pd.notna(row['稀有度']) else "普通"
                card_cost = int(float(row['法力值'])) if '法力值' in df.columns and pd.notna(row['法力值']) else 0
                card_type = str(row['卡牌类型']) if '卡牌类型' in df.columns and pd.notna(row['卡牌类型']) else "未知"
                card_description = str(row['卡牌描述']) if '卡牌描述' in df.columns and pd.notna(row['卡牌描述']) else ""
                
                # 读取攻击力/生命值，默认为空字符串
                attack_health = str(row['攻击力/生命值']) if '攻击力/生命值' in df.columns and pd.notna(row['攻击力/生命值']) else ""
                
                # 读取种族/类型，默认为空字符串
                race_type = str(row['种族/类型']) if '种族/类型' in df.columns and pd.notna(row['种族/类型']) else ""
                # -------------------------------------------
                
                card = {
                    'name': card_name,
                    'count': owned_count, # 存储拥有数量
                    'class': card_class, 
                    'set': card_set,
                    'rarity': card_rarity,
                    'cost': card_cost,
                    'type': card_type,
                    'description': card_description,
                    'attack_health': attack_health,
                    'race_type': race_type
                }
                self.all_cards.append(card)
            
            # 更新显示
            self.update_cards_list()
            self.update_deck_count()
            
            # 成功消息
            success_message = "抽卡报告导入成功！"
            if skipped_rows > 0:
                success_message += f" (已跳过 {skipped_rows} 行缺少卡牌名称的数据)"
            QMessageBox.information(self, "成功", success_message)
            
        except Exception as e:
            # 提供更具体的错误信息
            import traceback
            traceback_str = traceback.format_exc()
            QMessageBox.critical(self, "错误", f"导入报告时出错：{str(e)}\n\n{traceback_str}")
    
    def on_class_changed(self, index):
        """职业选择改变时的处理"""
        # 如果选择未改变，则不执行任何操作
        if index == self.previous_class_index:
            return

        new_class_text = self.ui.class_combo.currentText()

        # 检查卡组是否为空，如果不为空则提示
        if self.deck: # 如果卡组不为空
            reply = QMessageBox.question(self, '确认切换职业',
                                         "切换职业将清空当前卡组，您确定要继续吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                # 用户取消，恢复下拉框到上一个选项
                # 暂时阻塞信号，避免再次触发 on_class_changed
                self.ui.class_combo.blockSignals(True)
                self.ui.class_combo.setCurrentIndex(self.previous_class_index)
                self.ui.class_combo.blockSignals(False)
                return # 退出，不执行后续操作
            else:
                # 用户确认，清空卡组
                self.deck.clear()
                self.update_deck_list()
                self.update_deck_count()
        
        # --- 执行职业切换逻辑 --- 
        # (卡组为空或用户已确认清空)
        if new_class_text == "全部职业":
            self.selected_class = None
        else:
            self.selected_class = new_class_text
            
        self.update_cards_list() # 更新左侧卡牌列表
        
        # 更新上一次选择的索引
        self.previous_class_index = index
    
    def update_cards_list(self):
        """更新左侧卡牌列表"""
        # 过滤卡牌
        filtered_cards = []
        for card in self.all_cards:
            # 检查卡牌是否有完整信息 (name and class are essential)
            if not card['name'] or not card['class']:
                continue
                
            # 准备职业名称进行比较 (去除空白)
            card_class_name = card['class'].strip()
            selected_class_name = self.selected_class.strip() if self.selected_class else None
            
            # 职业过滤
            if selected_class_name is not None:
                # 如果选择了特定职业，显示该职业和中立卡牌
                if not (card_class_name == selected_class_name or card_class_name == '中立'):
                    continue
            
            # 搜索过滤
            if self.search_text:
                searchable_text = f"{card['name']} {card['description']} {card['type']} {card_class_name} {card['set']} {card['rarity']}".lower()
                if self.search_text not in searchable_text:
                    continue
            
            filtered_cards.append(card)
        
        # 更新UI
        self.ui.update_cards_list(filtered_cards, self.sort_column, self.sort_order)
    
    def add_card_to_deck(self, item):
        """添加卡牌到卡组"""
        # --- 检查是否选择了具体职业 ---
        if self.selected_class is None:
            QMessageBox.warning(self, "提示", "请先选择一个职业再编辑卡组。")
            return
        # -----------------------------

        if len(self.deck) >= 30:
            QMessageBox.warning(self, "警告", "卡组已达到30张卡牌上限！")
            return
        
        # 获取选中的行
        row = item.row()
        
        # --- 从表格中获取卡牌数据 (包括拥有数量) ---
        card_name = self.ui.cards_table.item(row, 1).text()
        try:
            owned_count = int(self.ui.cards_table.item(row, 9).text())
        except (ValueError, TypeError):
            owned_count = 1 # Fallback if count is invalid
            print(f"Warning: Could not parse owned count for {card_name}, defaulting to 1.")
        
        card = {
            'name': card_name,
            'count': owned_count, # Store owned count here too for consistency
            'class': self.ui.cards_table.item(row, 2).text(),
            'set': self.ui.cards_table.item(row, 3).text(),
            'rarity': self.ui.cards_table.item(row, 4).text(),
            'cost': int(self.ui.cards_table.item(row, 0).text()),
            'type': self.ui.cards_table.item(row, 5).text(),
            'race_type': self.ui.cards_table.item(row, 7).text(),
            'description': self.ui.cards_table.item(row, 8).text(),
            'attack_health': self.ui.cards_table.item(row, 6).text()
        }
        
        # --- 检查添加的卡是否符合当前职业 --- (双重保险)
        if card['class'] != self.selected_class and card['class'] != '中立':
             QMessageBox.warning(self, "错误", f"无法将【{card['class']}】职业卡牌添加到【{self.selected_class}】卡组中。")
             return
        # -------------------------------------
        
        # --- 检查拥有数量 --- 
        current_deck_count = sum(1 for deck_card in self.deck if deck_card['name'] == card['name'])
        if current_deck_count >= owned_count:
            QMessageBox.warning(self, "数量不足", f"您只有 {owned_count} 张【{card['name']}】，无法再添加。")
            return
        # -------------------

        # 检查传说卡限制 (现在也受拥有数量限制)
        if card['rarity'] == '传说':
            # (拥有数量检查已保证 current_deck_count < owned_count <= 1)
            if current_deck_count >= 1:
                 QMessageBox.warning(self, "规则限制", "传说卡最多只能带1张！") # Should be caught by owned_count check, but good practice
                 return 
        # 检查非传说卡限制 (现在也受拥有数量限制)
        else:
            # (拥有数量检查已保证 current_deck_count < owned_count)
            if current_deck_count >= 2:
                QMessageBox.warning(self, "规则限制", "非传说卡最多只能带2张！") # Should be caught by owned_count check, but good practice
                return

        # --- 检查符文限制 ---
        # 计算添加这张卡后的符文总数
        new_max_runes = {'红': 0, '蓝': 0, '绿': 0}
        
        # 先计算当前卡组中的最大符文数
        for deck_card in self.deck:
            if 'description' in deck_card and '符文：' in deck_card['description']:
                rune_text = deck_card['description'].split('符文：')[1].split('。')[0]
                if '红' in rune_text:
                    count = int(rune_text.split('红')[0].strip())
                    new_max_runes['红'] = max(new_max_runes['红'], count)
                if '蓝' in rune_text:
                    count = int(rune_text.split('蓝')[0].strip().split(',')[-1].strip())
                    new_max_runes['蓝'] = max(new_max_runes['蓝'], count)
                if '绿' in rune_text:
                    count = int(rune_text.split('绿')[0].strip().split(',')[-1].strip())
                    new_max_runes['绿'] = max(new_max_runes['绿'], count)
        
        # 检查新卡牌的符文数
        if 'description' in card and '符文：' in card['description']:
            rune_text = card['description'].split('符文：')[1].split('。')[0]
            if '红' in rune_text:
                count = int(rune_text.split('红')[0].strip())
                new_max_runes['红'] = max(new_max_runes['红'], count)
            if '蓝' in rune_text:
                count = int(rune_text.split('蓝')[0].strip().split(',')[-1].strip())
                new_max_runes['蓝'] = max(new_max_runes['蓝'], count)
            if '绿' in rune_text:
                count = int(rune_text.split('绿')[0].strip().split(',')[-1].strip())
                new_max_runes['绿'] = max(new_max_runes['绿'], count)
        
        # 检查是否超过符文限制
        total_runes = sum(new_max_runes.values())
        if total_runes > 3:
            current_runes = []
            if new_max_runes['红'] > 0:
                current_runes.append(f"{new_max_runes['红']}红")
            if new_max_runes['蓝'] > 0:
                current_runes.append(f"{new_max_runes['蓝']}蓝")
            if new_max_runes['绿'] > 0:
                current_runes.append(f"{new_max_runes['绿']}绿")
            QMessageBox.warning(self, "符文冲突", 
                f"添加【{card['name']}】后，卡组符文总数将达到 {' '.join(current_runes)}，超过了3点符文上限！")
            return
        # ----------------------
        
        # 添加卡牌到卡组
        self.deck.append(card)
        
        # 更新显示
        self.update_deck_list()
        self.update_deck_count()
    
    def remove_card_from_deck(self, item):
        """从卡组中移除卡牌"""
        # 获取与点击项关联的卡牌数据
        card_to_remove = item.data(Qt.UserRole)
        
        if card_to_remove in self.deck:
            # 从内部列表中移除这个特定的卡牌对象
            # 对于同名非传说卡，这会移除列表中的第一个匹配项
            self.deck.remove(card_to_remove)
            
            # 更新显示
            self.update_deck_list()
            self.update_deck_count()
        # 如果卡牌不在列表中（理论上不应发生），则不执行任何操作
    
    def confirm_clear_deck(self):
        """显示确认对话框并清空卡组"""
        reply = QMessageBox.question(self, '确认清空',
                                     "您确定要清空当前卡组吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 清空内部卡组数据
            self.deck.clear()
            # 更新右侧列表显示
            self.update_deck_list()
            # 更新卡组数量显示
            self.update_deck_count()
    
    def update_deck_list(self):
        """更新右侧卡组列表"""
        self.ui.update_deck_list(self.deck)
    
    def update_deck_count(self):
        """更新卡组数量显示"""
        self.ui.update_deck_count(len(self.deck))
        
    # 窗口大小改变事件
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 在窗口大小改变后，按比例调整列宽
        self.ui.resize_table_columns()

    # === 导入导出功能 ===
    def export_deckstring(self):
        """将当前卡组导出为炉石传说可导入的卡组代码"""
        DeckImportExport.export_deckstring(self.selected_class, self.deck, self.data_manager, self)

    def prompt_import_deck_code(self):
        """弹出对话框让用户输入卡组代码"""
        DeckImportExport.prompt_import_deck_code(self, self.import_deck_from_string)
    
    def import_deck_from_string(self, deckstring):
        """根据卡组代码字符串导入卡组"""
        DeckImportExport.import_deck_from_string(
            deckstring=deckstring,
            data_manager=self.data_manager,
            all_cards=self.all_cards,
            selected_class=self.selected_class,
            class_combo=self.ui.class_combo,
            current_deck=self.deck,
            on_class_changed=self.on_class_changed,
            update_deck_list=self.update_deck_list,
            update_deck_count=self.update_deck_count,
            update_cards_list=self.update_cards_list,
            parent_widget=self
        )

    def show_export_help(self):
        """显示导出卡组代码的帮助信息"""
        DeckImportExport.show_export_help(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 实例化并显示
    deck_builder = DeckBuilder()
    
    sys.exit(app.exec_())