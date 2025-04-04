import os
import sys
import json
import base64

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                          QHBoxLayout, QLabel, QPushButton, QListWidget, 
                          QListWidgetItem, QAbstractItemView, QComboBox,
                          QFileDialog, QMessageBox, QSplitter,
                          QTableWidget, QTableWidgetItem, QHeaderView,
                          QLineEdit, QTextEdit, QDialog,QAction, QActionGroup,QInputDialog, 
                          QToolButton) # Add QToolButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# 导入自定义模块
from config import CLASS_NAMES, RARITY_NAMES, SET_NAMES, CARD_TYPE_NAMES
# 导入卡组代码解析器功能
from deckstring_parser import parse_deckstring, HERO_ID_TO_CLASS

# --- Varint Encoding Function ---
def write_varint(data, value):
    """
    将整数编码为 varint 并添加到字节数组中
    
    Args:
        data: 目标字节数组，使用 bytearray 或支持 extend 方法的类似对象
        value: 要编码的整数值
        
    Returns:
        None，直接修改传入的 data 对象
    """
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        data.append(byte)
        if not value:
            break
# ------------------------------

# --- Default Hero DBF IDs (Updated based on actual game data) ---
DEFAULT_HERO_DBF_IDS = {
    "死亡骑士": 78065,  # 阿尔萨斯·米奈希尔
    "恶魔猎手": 56550,  # 伊利丹·怒风
    "德鲁伊": 274,     # 玛法里奥·怒风
    "猎人": 31,       # 雷克萨
    "法师": 637,      # 吉安娜·普罗德摩尔
    "圣骑士": 671,     # 乌瑟尔·光明使者
    "牧师": 813,      # 安度因·乌瑞恩
    "潜行者": 930,     # 瓦莉拉·萨古纳尔
    "萨满祭司": 1066,    # 萨尔
    "术士": 893,      # 古尔丹
    "战士": 7,        # 加尔鲁什·地狱咆哮
}

# 更准确的英雄 DBF ID，基于实际游戏数据
ACCURATE_HERO_DBF_IDS = {
    "死亡骑士": 78065,
    "恶魔猎手": 56550, 
    "德鲁伊": 274,
    "猎人": 31,
    "法师": 637,
    "圣骑士": 671,
    "牧师": 813,
    "潜行者": 930,
    "萨满祭司": 1066,
    "术士": 893,
    "战士": 7,
}

# 自定义 TableWidgetItem 用于数字排序
class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            # 尝试将文本转换为浮点数进行比较
            return float(self.text()) < float(other.text())
        except ValueError:
            # 如果转换失败（例如文本不是数字），则按字符串比较
            return super().__lt__(other)

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
        self.card_name_to_dbf_id = {} # 新增：用于存储名称到DBF ID的映射
        
        # 字体设置
        self.base_font_size = 10 # 使用pt作为单位，默认大小为9
        self.current_font = QFont() # 创建字体对象
        self.current_font.setPointSize(self.base_font_size)
        
        # 定义各列的目标宽度比例 (总和应接近1.0)
        self.column_proportions = [0.06, 0.14, 0.08, 0.12, 0.06, 0.08, 0.08, 0.30, 0.08]
        
        # 创建UI
        self.init_ui()
        # 加载卡牌数据
        self.load_card_data()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("炉石传说卡组构建器")
        self.setMinimumSize(1600, 800)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        
        # ===== 左侧面板 =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # 职业选择
        class_layout = QHBoxLayout()
        class_label = QLabel("选择职业:")
        class_label.setFont(QFont("Sans Serif", 10))
        self.class_combo = QComboBox()
        self.class_combo.addItem("全部职业", None)
        for class_id, class_name in CLASS_NAMES.items():
            # 跳过添加 "中立" 选项
            if class_name != '中立':
                self.class_combo.addItem(class_name, class_id)
        self.class_combo.currentIndexChanged.connect(self.on_class_changed)
        class_layout.addWidget(class_label)
        class_layout.addWidget(self.class_combo)
        left_layout.addLayout(class_layout)
        
        # 导入报告按钮
        import_btn = QPushButton("导入抽卡报告")
        import_btn.clicked.connect(self.import_report)
        left_layout.addWidget(import_btn)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        search_label.setFont(QFont("Sans Serif", 10))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入卡牌名称、描述等进行搜索...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        left_layout.addLayout(search_layout)
        
        # 卡牌列表标题
        cards_title = QLabel("可选卡牌")
        cards_title.setFont(QFont("Sans Serif", 12, QFont.Bold))
        left_layout.addWidget(cards_title)
        
        # 卡牌表格
        self.cards_table = QTableWidget()
        self.cards_table.setColumnCount(9)  # 增加到9列，添加攻击力/生命值列
        self.cards_table.setHorizontalHeaderLabels([
            "法力值", "卡牌名称", "职业", "扩展包", "稀有度", "卡牌类型", "攻击/生命", "卡牌描述", "拥有数量"
        ])
        # 设置列宽调整模式为 Interactive (允许用户调整，并由我们代码控制)
        self.cards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 取消最后列拉伸
        self.cards_table.horizontalHeader().setStretchLastSection(False)
        # 移除特定列拉伸，因为我们将手动按比例设置
        # self.cards_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        
        self.cards_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cards_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cards_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cards_table.itemDoubleClicked.connect(self.add_card_to_deck)
        # 启用排序
        self.cards_table.setSortingEnabled(True)
        self.cards_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        left_layout.addWidget(self.cards_table)
        
        # ===== 右侧面板 =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 卡组标题
        deck_title = QLabel("当前卡组")
        deck_title.setFont(QFont("Sans Serif", 12, QFont.Bold))
        right_layout.addWidget(deck_title)
        
        # 卡牌数量显示
        self.deck_count_label = QLabel("卡牌数量: 0/30")
        self.deck_count_label.setFont(QFont("Sans Serif", 10))
        right_layout.addWidget(self.deck_count_label)
        
        # 卡组列表
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.deck_list.itemDoubleClicked.connect(self.remove_card_from_deck)
        right_layout.addWidget(self.deck_list)
        
        # --- 添加按钮布局 --- 
        button_layout = QHBoxLayout()
        # 清空卡组按钮
        clear_deck_btn = QPushButton("清空卡组")
        clear_deck_btn.clicked.connect(self.confirm_clear_deck)
        button_layout.addWidget(clear_deck_btn)

        # 导入代码按钮
        import_code_btn = QPushButton("导入代码")
        import_code_btn.clicked.connect(self.prompt_import_deck_code)
        button_layout.addWidget(import_code_btn)
        
        # 导出卡组按钮
        export_deck_btn = QPushButton("导出卡组代码")
        export_deck_btn.clicked.connect(self.export_deckstring)
        button_layout.addWidget(export_deck_btn)

        # 新增：导出帮助按钮
        export_help_btn = QToolButton()
        export_help_btn.setText("?")
        export_help_btn.setFixedSize(24, 24) # 设置固定大小使其像图标按钮
        export_help_btn.setToolTip("关于导出有效卡组代码的说明")
        export_help_btn.clicked.connect(self.show_export_help)
        button_layout.addWidget(export_help_btn)
        
        right_layout.addLayout(button_layout) # 将按钮布局添加到右侧垂直布局
        # ---------------------
        
        # 添加两个面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置初始大小比例
        splitter.setSizes([800, 400])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        # 显示窗口
        self.show()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # --- Initial Column Resize --- 
        # Manually trigger column resize after UI is setup and shown
        # to ensure correct initial layout based on proportions.
        self.resize_table_columns()
    
    def create_menu_bar(self):
        """创建菜单栏和菜单项"""
        menu_bar = self.menuBar()
        
        # 文件菜单 (可选，如果需要可以添加其他功能)
        # file_menu = menu_bar.addMenu("文件")
        # exit_action = QAction("退出", self)
        # exit_action.triggered.connect(self.close)
        # file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        # 字体大小子菜单
        font_size_menu = view_menu.addMenu("字体大小")
        font_group = QActionGroup(self) # 用于互斥选择
        font_group.setExclusive(True)
        
        sizes = {
            "小 (默认)": self.base_font_size,
            "中": self.base_font_size + 1,
            "大": self.base_font_size + 2
        }
        
        for size_name, size_value in sizes.items():
            action = QAction(size_name, self, checkable=True)
            action.setData(size_value) # 存储字体大小值
            action.triggered.connect(lambda checked, s=size_value: self.set_font_size(s))
            font_group.addAction(action)
            font_size_menu.addAction(action)
            
            # 默认选中"小"
            if size_value == self.base_font_size:
                action.setChecked(True)

    def set_font_size(self, size):
        """设置表格和列表的字体大小"""
        self.current_font.setPointSize(size)
        # 应用到表格和列表
        self.cards_table.setFont(self.current_font)
        self.deck_list.setFont(self.current_font)
        
        # 调整行高以适应新字体
        self.cards_table.resizeRowsToContents()
        # 右侧列表可能也需要调整，但QListWidget通常能自动处理

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
        self.cards_table.sortItems(logical_index, self.sort_order)
    
    def import_report(self):
        """导入抽卡报告"""
        try:
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择抽卡报告",
                os.path.join("抽卡报告"),
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # 读取Excel文件
            import pandas as pd
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
            self.cards_table.setRowCount(0)
            self.deck_list.clear()
            
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
                    'attack_health': attack_health
                }
                self.all_cards.append(card)
            
            # 更新显示
            self.update_cards_list()
            self.update_deck_count()
            
            # --- Resize columns after import --- 
            # Re-apply proportional column widths after data is loaded and table updated
            # self.resize_table_columns()
            # ---------------------------------
            
            success_message = "抽卡报告导入成功！"
            if skipped_rows > 0:
                success_message += f" (已跳过 {skipped_rows} 行缺少卡牌名称的数据)"
            QMessageBox.information(self, "成功", success_message)
            
        except Exception as e:
            # Provide more specific error information
            import traceback
            traceback_str = traceback.format_exc()
            QMessageBox.critical(self, "错误", f"导入报告时出错：{str(e)}\n\n{traceback_str}")
    
    def on_class_changed(self, index):
        """职业选择改变时的处理"""
        # 如果选择未改变，则不执行任何操作
        if index == self.previous_class_index:
            return

        new_class_text = self.class_combo.currentText()

        # 检查卡组是否为空，如果不为空则提示
        if self.deck: # 如果卡组不为空
            reply = QMessageBox.question(self, '确认切换职业',
                                         "切换职业将清空当前卡组，您确定要继续吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                # 用户取消，恢复下拉框到上一个选项
                # 暂时阻塞信号，避免再次触发 on_class_changed
                self.class_combo.blockSignals(True)
                self.class_combo.setCurrentIndex(self.previous_class_index)
                self.class_combo.blockSignals(False)
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
        # 保存当前排序状态
        current_sort_column = self.sort_column
        current_sort_order = self.sort_order
        
        # 更新前禁用排序，避免冲突
        self.cards_table.setSortingEnabled(False)
        
        # 清空表格
        self.cards_table.setRowCount(0)
        
        # 过滤卡牌
        filtered_cards = []
        for card in self.all_cards:
            # 检查卡牌是否有完整信息 (name and class are essential)
            if not card['name'] or not card['class']:
                continue
                
            # Prepare class names for comparison (strip whitespace)
            card_class_name = card['class'].strip()
            selected_class_name = self.selected_class.strip() if self.selected_class else None
            
            # 职业过滤
            if selected_class_name is not None:
                # If a specific class is selected, show cards of that class AND neutral cards
                if not (card_class_name == selected_class_name or card_class_name == '中立'):
                    continue
            
            # 搜索过滤
            if self.search_text:
                searchable_text = f"{card['name']} {card['description']} {card['type']} {card_class_name} {card['set']} {card['rarity']}".lower()
                if self.search_text not in searchable_text:
                    continue
            
            filtered_cards.append(card)
        
        # 添加到表格
        for card in filtered_cards:
            row = self.cards_table.rowCount()
            self.cards_table.insertRow(row)
            
            # 创建单元格
            # 使用 NumericTableWidgetItem 来处理法力值列
            cost_item = NumericTableWidgetItem(str(card['cost'])) 
            cost_item.setTextAlignment(Qt.AlignCenter)  # 居中对齐
            
            name_item = QTableWidgetItem(card['name'])
            # 添加拥有数量单元格
            count_item = NumericTableWidgetItem(str(card['count'])) 
            count_item.setTextAlignment(Qt.AlignCenter)
            
            class_item = QTableWidgetItem(card['class'])
            set_item = QTableWidgetItem(card['set'])
            rarity_item = QTableWidgetItem(card['rarity'])
            type_item = QTableWidgetItem(card['type'])
            desc_item = QTableWidgetItem(card['description'])
            
            # 添加攻击力/生命值单元格
            attack_health_item = QTableWidgetItem(card.get('attack_health', ''))
            attack_health_item.setTextAlignment(Qt.AlignCenter)
            
            # 设置单元格数据
            self.cards_table.setItem(row, 0, cost_item)
            self.cards_table.setItem(row, 1, name_item)
            self.cards_table.setItem(row, 2, class_item)
            self.cards_table.setItem(row, 3, set_item)
            self.cards_table.setItem(row, 4, rarity_item)
            self.cards_table.setItem(row, 5, type_item)
            self.cards_table.setItem(row, 6, attack_health_item)
            self.cards_table.setItem(row, 7, desc_item)
            self.cards_table.setItem(row, 8, count_item)
            
            # 设置颜色
            if card['rarity'] == '传说':
                color = QColor("#FF7D0A")  # 橙色
            elif card['rarity'] == '史诗':
                color = QColor("#A335EE")  # 紫色
            elif card['rarity'] == '稀有':
                color = QColor("#0070DD")  # 蓝色
            else:
                color = QColor("#333333")  # 更深的灰色，接近黑色
            
            # 为整行设置颜色
            for col in range(self.cards_table.columnCount()):
                item = self.cards_table.item(row, col)
                if item: # Check if item exists before setting color
                    item.setForeground(color)
        
        # 恢复排序状态
        if current_sort_column >= 0:
            # 先设置排序列和顺序，再重新启用排序
            self.cards_table.sortItems(current_sort_column, current_sort_order)
        
        # 重新启用排序
        self.cards_table.setSortingEnabled(True)
            
        # 调整行高
        self.cards_table.resizeRowsToContents()
    
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
        card_name = self.cards_table.item(row, 1).text()
        try:
            owned_count = int(self.cards_table.item(row, 8).text())
        except (ValueError, TypeError):
            owned_count = 1 # Fallback if count is invalid
            print(f"Warning: Could not parse owned count for {card_name}, defaulting to 1.")
        
        card = {
            'name': card_name,
            'count': owned_count, # Store owned count here too for consistency
            'class': self.cards_table.item(row, 2).text(),
            'set': self.cards_table.item(row, 3).text(),
            'rarity': self.cards_table.item(row, 4).text(),
            'cost': int(self.cards_table.item(row, 0).text()),
            'type': self.cards_table.item(row, 5).text(),
            'description': self.cards_table.item(row, 7).text(),
            'attack_health': self.cards_table.item(row, 6).text()
        }
        # ---------------------------------------------
        
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
        self.deck_list.clear()
        
        # 按费用和名称排序
        sorted_cards = sorted(self.deck, key=lambda x: (x['cost'], x['name']))
        
        # 添加到列表
        for card in sorted_cards:
            # 创建显示文本
            display_text = f"{card['cost']}费 {card['name']} ({card['type']})"
            
            # 创建列表项
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, card)  # 存储卡牌数据
            
            # 设置颜色
            if card['rarity'] == '传说':
                item.setForeground(QColor("#FF7D0A"))  # 橙色
            elif card['rarity'] == '史诗':
                item.setForeground(QColor("#A335EE"))  # 紫色
            elif card['rarity'] == '稀有':
                item.setForeground(QColor("#0070DD"))  # 蓝色
            else:
                item.setForeground(QColor("#888888"))  # 灰色
            
            self.deck_list.addItem(item)
    
    def update_deck_count(self):
        """更新卡组数量显示"""
        self.deck_count_label.setText(f"卡牌数量: {len(self.deck)}/30")

    def load_card_data(self):
        """加载 card_infos.json 并构建映射，严格优先选择 CORE 系列卡牌。"""
        json_path = "hsJSON卡牌数据/card_infos.json"
        if not os.path.exists(json_path):
            QMessageBox.critical(self, "错误", f"找不到卡牌数据文件：{json_path}\n无法实现卡组导出/导入功能。")
            return
            
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
                    normalized_name = self.normalize_card_name(card_name)
                    
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
                            # print(f"  覆盖 '{card_name}': {existing_dbf_id}({existing_set}) -> {dbf_id}(CORE)")
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
                            # print(f"  覆盖 Norm '{normalized_name}': {existing_dbf_id}({existing_set}) -> {dbf_id}(CORE)")
                            normalized_name_to_dbf_id[normalized_name] = dbf_id
                        # 其他情况保持不变
            
            self.normalized_name_to_dbf_id = normalized_name_to_dbf_id
            
            print(f"Loaded {len(self.card_name_to_dbf_id)} collectible cards with CORE preference.")
            print(f"Created DBF ID map with {len(self.dbf_id_to_card_info)} entries.")
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            QMessageBox.critical(self, "错误", f"加载卡牌数据 {json_path} 时出错：{str(e)}\n\n{traceback_str}")
            self.card_name_to_dbf_id = {} 
            self.normalized_name_to_dbf_id = {}
            self.dbf_id_to_card_info = {}
    
    def normalize_card_name(self, name):
        """规范化卡牌名称，用于模糊匹配"""
        import re
        # 转为小写
        name = name.lower()
        # 移除所有空格
        name = name.replace(" ", "")
        # 移除所有标点符号
        name = re.sub(r'[^\w\s]', '', name)
        return name

    def export_deckstring(self):
        """将当前卡组导出为炉石传说可导入的卡组代码"""
        print("开始导出卡组代码...")
        
        if not self.selected_class or len(self.deck) == 0:
            QMessageBox.warning(self, "警告", "当前没有选择职业或卡组为空，无法导出卡组代码。")
            print("导出中止：未选择职业或卡组为空。")
            return
            
        print("检查卡牌数据映射...")
        if not hasattr(self, 'card_name_to_dbf_id') or not self.card_name_to_dbf_id:
            print("卡牌数据映射不存在，尝试重新加载...")
            self.load_card_data()
            if not self.card_name_to_dbf_id:  # load_card_data 失败
                print("卡牌数据加载失败，导出中止。")
                return
            print("卡牌数据重新加载完成。")
        else:
             print("卡牌数据映射已存在。")
                
        # 准确的英雄DBF ID (目前以主流皮肤为主)
        ACCURATE_HERO_DBF_IDS = {
            "德鲁伊": 274,     # 玛法里奥
            "猎人": 31,       # 雷克萨
            "法师": 637,      # 吉安娜
            "圣骑士": 671,     # 乌瑟尔
            "牧师": 813,      # 安度因
            "潜行者": 930,     # 瓦莉拉
            "萨满": 1066,     # 萨尔
            "术士": 893,      # 古尔丹
            "战士": 7,        # 加尔鲁什
            "恶魔猎手": 56550,  # 伊利丹
            "死亡骑士": 78065,  # 阿萨斯
        }
        
        hero_dbf_id = ACCURATE_HERO_DBF_IDS.get(self.selected_class)
        if not hero_dbf_id:
            QMessageBox.warning(self, "警告", f"未找到职业 '{self.selected_class}' 的英雄 DBF ID，卡组代码导出可能不正确。")
            # 尝试使用旧的映射，确保有一个备选值
            hero_dbf_id = self.default_hero_dbf_ids.get(self.selected_class, 7)  # 默认为战士
        print(f"英雄DBF ID: {hero_dbf_id}")
        
        print("开始统计和查找卡牌DBF ID...")
        # 统计卡牌数量
        card_counts = {}
        for card in self.deck:
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
            print(f"  查找卡牌 {card_index}/{total_cards}: {card_name} (数量: {count})...")
            # 尝试多种方式找到 DBF ID
            dbf_id = self.find_card_dbf_id(card_name)
            print(f"    找到DBF ID: {dbf_id if dbf_id else '未找到'}")
            
            if dbf_id:
                debug_info.append(f"{card_name}: DBF ID={dbf_id}, 数量={count}")
                if count == 1:
                    cards_x1.append(dbf_id)
                else:
                    cards_x2.append(dbf_id)
            else:
                missing_dbf_ids.append(card_name)
        print("卡牌DBF ID查找完成。")
                
        if missing_dbf_ids:
            warning_msg = f"以下 {len(missing_dbf_ids)} 张卡牌未找到 DBF ID，它们将不会包含在导出的卡组代码中：\n"
            warning_msg += "\n".join(missing_dbf_ids)
            QMessageBox.warning(self, "警告", warning_msg)
            
        # 排序很重要！
        print("对卡牌列表进行排序...")
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
        
        # Base64编码
        encoded = base64.b64encode(data).decode('utf-8')
        print("数据流构建和编码完成。")
        
        # 复制到剪贴板
        print("复制到剪贴板...")
        clipboard = QApplication.clipboard()
        clipboard.setText(encoded)
        
        # --- 显示包含代码的成功对话框 --- 
        # 创建一个简单的对话框来显示代码
        dialog = QDialog(self)
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
        
        print("导出流程结束。")
        
    def find_card_dbf_id(self, card_name):
        """尝试使用精确匹配找到卡牌的 DBF ID"""
        # 1. 直接使用卡牌名称查找
        if card_name in self.card_name_to_dbf_id:
            print(f"    找到DBF ID (直接匹配): {self.card_name_to_dbf_id[card_name]}")
            return self.card_name_to_dbf_id[card_name]
            
        # 2. 尝试使用规范化名称查找
        normalized_name = self.normalize_card_name(card_name)
        if normalized_name in self.normalized_name_to_dbf_id:
            print(f"    找到DBF ID (规范化匹配): {self.normalized_name_to_dbf_id[normalized_name]}")
            return self.normalized_name_to_dbf_id[normalized_name]
            
        # --- 移除模糊匹配 --- 
        # 3. 尝试模糊匹配 (已移除)
        # for name, dbf_id in self.card_name_to_dbf_id.items():
        #     if card_name in name or name in card_name:
        #         print(f"    找到DBF ID (模糊匹配1): {dbf_id}")
        #         return dbf_id
                
        # 4. 最后一次尝试：规范化后的模糊匹配 (已移除)
        # normalized_user_input = self.normalize_card_name(card_name)
        # for norm_name, dbf_id in self.normalized_name_to_dbf_id.items():
        #     if normalized_user_input in norm_name or norm_name in normalized_user_input:
        #         print(f"    找到DBF ID (模糊匹配2): {dbf_id}")
        #         return dbf_id
        # ----------------------
                
        print(f"    警告：未能通过精确匹配找到卡牌 '{card_name}' 的 DBF ID。")        
        return None

    # --- Resize Event Handling for Proportional Columns ---
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 在窗口大小改变后，按比例调整列宽
        self.resize_table_columns()

    def resize_table_columns(self):
        """根据预设比例调整大部分列宽，并拉伸描述列"""
        if not hasattr(self, 'cards_table') or not self.cards_table.horizontalHeader():
            return # 如果表格还未完全初始化，则跳过
            
        header = self.cards_table.horizontalHeader()
        header_width = header.width()

        # 检查垂直滚动条是否可见，并获取其宽度
        scrollbar_width = 0
        scrollbar = self.cards_table.verticalScrollBar()
        if scrollbar and scrollbar.isVisible():
            scrollbar_width = scrollbar.width()

        # 计算实际可用的内容区域宽度
        available_width = header_width - scrollbar_width

        if available_width <= 0:
             return # 如果可用宽度无效，则不调整

        if len(self.column_proportions) != header.count():
            print("Warning: Column proportions length does not match header count.")
            return
            
        # 设置"卡牌描述"列（索引7）自动拉伸
        header.setSectionResizeMode(7, QHeaderView.Stretch)

        # 按比例设置其他列的宽度
        for i in range(header.count()):
            if i == 7: # 跳过描述列，因为它会自动拉伸
                continue
            proportion = self.column_proportions[i]
            # 计算宽度，并确保至少有很小的宽度（例如10像素）
            width = max(10, int(available_width * proportion))
            # 设置为 Interactive 允许用户调整，然后设置固定宽度
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            header.resizeSection(i, width)
    # ------------------------------------------------------

    def prompt_import_deck_code(self):
        """弹出对话框让用户输入卡组代码"""
        deck_code, ok = QInputDialog.getText(self, '导入卡组代码', '请输入卡组代码:')
        
        if ok and deck_code:
            self.import_deck_from_string(deck_code.strip())
        elif ok:
            QMessageBox.warning(self, "提示", "未输入卡组代码。")
    
    def import_deck_from_string(self, deckstring):
        """根据卡组代码字符串导入卡组"""
        print(f"尝试导入卡组代码: {deckstring}")
        
        # 检查卡牌数据库是否加载
        if not hasattr(self, 'dbf_id_to_card_info') or not self.dbf_id_to_card_info:
            print("DBF ID 映射不存在，尝试重新加载...")
            self.load_card_data()
            if not self.dbf_id_to_card_info:
                QMessageBox.critical(self, "错误", "无法加载卡牌数据库 (DBF ID 映射)，无法导入卡组。")
                return
            print("DBF ID 映射重新加载完成。")

        if not self.all_cards:
             QMessageBox.warning(self, "提示", "请先导入您的抽卡报告 (Excel 文件)，以便程序了解您拥有的卡牌和数量。")
             return
        
        deck_data = parse_deckstring(deckstring)
        if not deck_data:
            QMessageBox.critical(self, "错误", "解析卡组代码失败，请检查代码是否有效。")
            return
            
        # --- 确定目标职业 --- 
        target_class = None
        code_class_identified = False
        
        if deck_data['heroes']:
            hero_dbf_id = deck_data['heroes'][0]
            code_class = HERO_ID_TO_CLASS.get(hero_dbf_id)
            
            if not code_class:
                # 尝试从卡牌推断
                for dbf_id, _ in deck_data['cards']:
                    if dbf_id in self.dbf_id_to_card_info:
                        card_class_hsjson = self.dbf_id_to_card_info[dbf_id].get('cardClass') 
                        if card_class_hsjson and card_class_hsjson != 'NEUTRAL':
                             # 查找 CLASS_NAMES 中的值（中文名）
                             for cn_key, cn_val in CLASS_NAMES.items():
                                 # HearthstoneJSON 的职业名是大写的，需要匹配
                                 if cn_key.upper() == card_class_hsjson:
                                     code_class = cn_val
                                     break
                        if code_class: break 
            
            if code_class:
                target_class = code_class
                code_class_identified = True
                print(f"从代码中识别出的职业: {target_class}")
            else:
                print(f"无法从代码的英雄ID {hero_dbf_id} 或卡牌中识别职业。")
        else:
            print("卡组代码中未包含英雄信息。")

        # 如果无法从代码中识别职业，则使用当前选中的职业
        if not code_class_identified:
            if self.selected_class is None:
                QMessageBox.warning(self, "需要选择职业", 
                                    "无法识别卡组代码中的职业，且当前未选择任何职业。\n请先在左上角选择一个具体职业再导入。")
                return
            else:
                target_class = self.selected_class
                QMessageBox.information(self, "提示", 
                                      f"无法识别卡组代码中的职业。\n将尝试把卡牌导入到当前选中的职业【{target_class}】中。")
                print(f"将使用当前选中的职业: {target_class}")
        
        # --- 处理职业切换和清空卡组 --- 
        proceed_import = False
        if self.selected_class != target_class:
            print(f"当前职业 '{self.selected_class}' 与目标职业 '{target_class}' 不匹配，尝试切换..." if self.selected_class else f"当前未选择职业，尝试切换到目标职业 '{target_class}'...")
            target_index = -1
            for i in range(self.class_combo.count()):
                if self.class_combo.itemText(i) == target_class:
                    target_index = i
                    break
            
            if target_index == -1:
                QMessageBox.critical(self, "错误", f"无法在下拉列表中找到职业 '{target_class}'。导入中止。")
                return
            
            # 触发职业切换 (会处理清空确认)
            self.class_combo.setCurrentIndex(target_index)
            
            # 检查切换是否成功 (用户可能取消)
            if self.selected_class == target_class:
                print("职业切换成功，卡组已清空 (或用户确认清空)。")
                proceed_import = True
            else:
                print("用户取消了职业切换或切换失败，导入中止。")
                return
        else:
            # 职业匹配，或使用当前职业导入，需要确认清空
            print(f"目标职业 '{target_class}' 与当前选中职业匹配。")
            if self.deck:
                reply = QMessageBox.question(self, '确认导入',
                                            f"导入新卡组到【{target_class}】将清空当前卡组，您确定要继续吗？",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.deck.clear()
                    print("已清空现有卡组。")
                    proceed_import = True
                else:
                    print("用户取消了导入。")
                    return
            else:
                # 当前卡组为空，直接继续
                proceed_import = True

        if not proceed_import:
             print("未能继续导入流程。") # 理论上不应执行到这里
             return
             
        # --- 开始添加卡牌 (后续逻辑保持不变) --- 
        print("开始添加卡牌到卡组...")
        imported_count = 0
        skipped_cards = [] # 记录无法添加或数量不足的卡牌
        missing_from_collection = [] # 记录用户根本没有的卡牌
        deck_full_skipped_start_index = -1 # 记录卡组满时处理到的卡牌在deck_data['cards']中的索引
        
        # 创建一个用户拥有卡牌的查找表 (名称 -> 卡牌对象列表)
        user_collection_map = {}
        for card_obj in self.all_cards:
            name = card_obj['name']
            if name not in user_collection_map:
                user_collection_map[name] = []
            user_collection_map[name].append(card_obj)
        
        for idx, (dbf_id, required_count) in enumerate(deck_data['cards']):
            if dbf_id not in self.dbf_id_to_card_info:
                skipped_cards.append(f"ID {dbf_id} (数据库中未找到)")
                continue
            
            card_info = self.dbf_id_to_card_info[dbf_id]
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
            
            print(f"  处理卡牌: {card_name}, 要求: {required_count}, 拥有: {owned_count}, 规则上限: {max_allowed}, 可添加: {can_add_count}")

            # 添加卡牌到卡组 (添加 can_add_count 次)
            actually_added = 0
            for _ in range(can_add_count):
                 # 检查卡组是否已满
                 if len(self.deck) >= 30:
                     print("卡组已满 (30张)，停止添加。")
                     deck_full_skipped_start_index = idx # 记录当前处理的卡牌索引
                     break # 跳出内层添加循环
                 self.deck.append(user_card_obj) # 添加用户收藏中的对象
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
                rem_name = self.dbf_id_to_card_info.get(rem_id, {}).get('name', f'ID {rem_id}')
                # 检查这张卡是否之前因为缺失被记录过
                if not any(rem_name in s for s in missing_from_collection):
                    skipped_cards.append(f"{rem_name} x{rem_count} (卡组已满)")
        
        print("卡牌添加处理完成。")
        
        # 更新UI
        self.update_deck_list()
        self.update_deck_count()
        self.update_cards_list() # 更新左侧列表以反映可能的职业变化
        
        # --- 显示导入结果 --- 
        summary_message = f"卡组导入完成。\n成功导入 {imported_count} / {sum(c[1] for c in deck_data['cards'])} 张卡牌到卡组。\n卡组当前共 {len(self.deck)} 张卡牌。"
        details = []
        if missing_from_collection:
            details.append("\n您未拥有的卡牌 (已跳过):")
            details.extend([f"- {s}" for s in missing_from_collection])
        if skipped_cards:
            details.append("\n未能完全添加或跳过的卡牌:")
            details.extend([f"- {s}" for s in skipped_cards])
            
        if details:
             QMessageBox.information(self, "导入结果", summary_message + "\n" + "\n".join(details))
        else:
             QMessageBox.information(self, "导入成功", summary_message)

    def show_export_help(self):
        """显示导出卡组代码的帮助信息"""
        help_text = """
        要成功导出游戏可识别的卡组代码，需要满足以下条件：

        1. 带满 30 张卡，即卡组不能是残缺的
        2. 没有奇利亚斯等需要子模块的特殊卡牌
        
        当前导出功能不会处理这些特殊卡牌的子选项，导出的代码可能无法直接在游戏中使用。
        """
        QMessageBox.information(self, "导出卡组代码帮助", help_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 实例化并显示
    deck_builder = DeckBuilder()
    
    sys.exit(app.exec_())