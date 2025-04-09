from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
                              QListWidget, QListWidgetItem, QHeaderView, 
                              QAbstractItemView, QToolButton, QSplitter, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from utils import NumericTableWidgetItem
from config import CLASS_NAMES

class DeckBuilderUI:
    """卡组构建器UI组件管理类"""
    
    def __init__(self, parent):
        """
        初始化UI组件管理器
        
        Args:
            parent: 父窗口对象，通常是DeckBuilder实例
        """
        self.parent = parent
        self.central_widget = None
        self.cards_table = None
        self.deck_list = None
        self.class_combo = None
        self.deck_count_label = None
        self.current_runes_label = None  # 新增：当前符文标签
        self.search_edit = None
        self.export_help_btn = None
    
    def create_ui(self):
        """初始化创建卡组构建器UI"""
        self.parent.setWindowTitle("炉石传说卡组构建器")
        self.parent.setMinimumSize(1600, 800)
        
        # 主窗口部件
        self.central_widget = QWidget()
        self.parent.setCentralWidget(self.central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(self.central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        
        # 创建左侧和右侧面板
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()
        
        # 添加两个面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置初始大小比例
        splitter.setSizes([800, 400])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        # 显示窗口
        self.parent.show()
        
        # 调整列宽
        self.resize_table_columns()
    
    def create_left_panel(self):
        """创建左侧面板"""
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
        self.class_combo.currentIndexChanged.connect(self.parent.on_class_changed)
        class_layout.addWidget(class_label)
        class_layout.addWidget(self.class_combo)
        left_layout.addLayout(class_layout)
        
        # 导入报告按钮
        import_btn = QPushButton("导入抽卡报告")
        import_btn.clicked.connect(self.parent.import_report)
        left_layout.addWidget(import_btn)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        search_label.setFont(QFont("Sans Serif", 10))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入卡牌名称、描述等进行搜索...")
        self.search_edit.textChanged.connect(self.parent.on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        left_layout.addLayout(search_layout)
        
        # 卡牌列表标题
        cards_title = QLabel("可选卡牌")
        cards_title.setFont(QFont("Sans Serif", 12, QFont.Bold))
        left_layout.addWidget(cards_title)
        
        # 卡牌表格
        self.cards_table = QTableWidget()
        self.cards_table.setColumnCount(10)  # 10列，包括种族/类型列
        self.cards_table.setHorizontalHeaderLabels([
            "法力值", "卡牌名称", "职业", "扩展包", "稀有度", "卡牌类型", "攻/生", "种族/类型", "卡牌描述", "数量"
        ])
        # 设置列宽调整模式为 Interactive (允许用户调整，并由我们代码控制)
        self.cards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 取消最后列拉伸
        self.cards_table.horizontalHeader().setStretchLastSection(False)
        
        self.cards_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cards_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cards_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cards_table.itemDoubleClicked.connect(self.parent.add_card_to_deck)
        # 启用排序
        self.cards_table.setSortingEnabled(True)
        self.cards_table.horizontalHeader().sectionClicked.connect(self.parent.on_header_clicked)
        left_layout.addWidget(self.cards_table)
        
        return left_panel
    
    def create_right_panel(self):
        """创建右侧面板"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 卡组标题
        deck_title = QLabel("当前卡组")
        deck_title.setFont(QFont("Sans Serif", 12, QFont.Bold))
        right_layout.addWidget(deck_title)
        
        # 创建水平布局来放置卡牌数量和当前符文
        stats_layout = QHBoxLayout()
        
        # 卡牌数量显示
        self.deck_count_label = QLabel("卡牌数量: 0/30")
        self.deck_count_label.setFont(QFont("Sans Serif", 10))
        stats_layout.addWidget(self.deck_count_label)
        
        # 当前符文显示
        self.current_runes_label = QLabel("")
        self.current_runes_label.setFont(QFont("Sans Serif", 10))
        self.current_runes_label.hide()  # 初始时隐藏
        stats_layout.addWidget(self.current_runes_label)
        
        # 添加弹性空间
        stats_layout.addStretch()
        
        # 将水平布局添加到主布局
        right_layout.addLayout(stats_layout)
        
        # 卡组列表
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.deck_list.itemDoubleClicked.connect(self.parent.remove_card_from_deck)
        right_layout.addWidget(self.deck_list)
        
        # --- 添加按钮布局 --- 
        button_layout = QHBoxLayout()
        # 清空卡组按钮
        clear_deck_btn = QPushButton("清空卡组")
        clear_deck_btn.clicked.connect(self.parent.confirm_clear_deck)
        button_layout.addWidget(clear_deck_btn)

        # 导入代码按钮
        import_code_btn = QPushButton("导入代码")
        import_code_btn.clicked.connect(self.parent.prompt_import_deck_code)
        button_layout.addWidget(import_code_btn)
        
        # 导出卡组按钮
        export_deck_btn = QPushButton("导出卡组代码")
        export_deck_btn.clicked.connect(self.parent.export_deckstring)
        button_layout.addWidget(export_deck_btn)

        # 导出帮助按钮
        self.export_help_btn = QToolButton()
        self.export_help_btn.setText("?")
        self.export_help_btn.setFixedSize(24, 24) # 设置固定大小使其像图标按钮
        self.export_help_btn.setToolTip("关于导出有效卡组代码的说明")
        self.export_help_btn.clicked.connect(self.parent.show_export_help)
        button_layout.addWidget(self.export_help_btn)
        
        right_layout.addLayout(button_layout) # 将按钮布局添加到右侧垂直布局
        
        return right_panel
    
    def update_deck_list(self, deck):
        """
        更新右侧卡组列表
        
        Args:
            deck: 当前卡组列表
        """
        self.deck_list.clear()
        
        # 用于跟踪每种符文的最大值
        max_runes = {'红': 0, '蓝': 0, '绿': 0}
        
        # 按费用和名称排序
        sorted_cards = sorted(deck, key=lambda x: (x['cost'], x['name']))
        
        # 添加到列表
        for card in sorted_cards:
            # 创建显示文本
            display_text = f"{card['cost']}费 {card['name']} ({card['type']})"
            
            # 检查是否有符文消耗并更新最大值
            if 'description' in card and '符文：' in card['description']:
                rune_text = card['description'].split('符文：')[1].split('。')[0]
                
                # 解析符文消耗并更新最大值
                if '红' in rune_text:
                    count = int(rune_text.split('红')[0].strip())
                    max_runes['红'] = max(max_runes['红'], count)
                if '蓝' in rune_text:
                    count = int(rune_text.split('蓝')[0].strip().split(',')[-1].strip())
                    max_runes['蓝'] = max(max_runes['蓝'], count)
                if '绿' in rune_text:
                    count = int(rune_text.split('绿')[0].strip().split(',')[-1].strip())
                    max_runes['绿'] = max(max_runes['绿'], count)
                
                # 为显示文本添加符文信息
                runes = []
                if '红' in rune_text:
                    runes.append(rune_text.split('红')[0].strip() + '红')
                if '蓝' in rune_text:
                    runes.append(rune_text.split('蓝')[0].strip().split(',')[-1].strip() + '蓝')
                if '绿' in rune_text:
                    runes.append(rune_text.split('绿')[0].strip().split(',')[-1].strip() + '绿')
                if runes:
                    display_text += f" {' '.join(runes)}"
            
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
        
        # 更新当前符文显示
        rune_text_parts = []
        if max_runes['红'] > 0:
            rune_text_parts.append(f"{max_runes['红']}红")
        if max_runes['蓝'] > 0:
            rune_text_parts.append(f"{max_runes['蓝']}蓝")
        if max_runes['绿'] > 0:
            rune_text_parts.append(f"{max_runes['绿']}绿")
        
        if rune_text_parts:
            self.current_runes_label.setText("当前符文: " + " ".join(rune_text_parts))
            self.current_runes_label.show()
        else:
            self.current_runes_label.hide()
    
    def update_deck_count(self, deck_size):
        """
        更新卡组数量显示
        
        Args:
            deck_size: 当前卡组大小
        """
        self.deck_count_label.setText(f"卡牌数量: {deck_size}/30")
    
    def update_cards_list(self, filtered_cards, sort_column, sort_order):
        """
        更新左侧卡牌列表
        
        Args:
            filtered_cards: 过滤后的卡牌列表
            sort_column: 当前排序列索引
            sort_order: 当前排序顺序
        """
        # 更新前禁用排序，避免冲突
        self.cards_table.setSortingEnabled(False)
        
        # 清空表格
        self.cards_table.setRowCount(0)
        
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
            
            # 添加种族/类型单元格
            race_type_item = QTableWidgetItem(card.get('race_type', ''))
            race_type_item.setTextAlignment(Qt.AlignCenter)
            
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
            self.cards_table.setItem(row, 7, race_type_item)
            self.cards_table.setItem(row, 8, desc_item)
            self.cards_table.setItem(row, 9, count_item)
            
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
                if item: # 检查单元格是否存在
                    item.setForeground(color)
        
        # 恢复排序状态
        if sort_column >= 0:
            # 先设置排序列和顺序，再重新启用排序
            self.cards_table.sortItems(sort_column, sort_order)
        
        # 重新启用排序
        self.cards_table.setSortingEnabled(True)
            
        # 调整行高
        self.cards_table.resizeRowsToContents()
    
    def create_menu_bar(self, set_font_size_callback):
        """
        创建菜单栏和菜单项
        
        Args:
            set_font_size_callback: 设置字体大小的回调函数
        """
        from PyQt5.QtWidgets import QAction, QActionGroup
        
        menu_bar = self.parent.menuBar()
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        # 字体大小子菜单
        font_size_menu = view_menu.addMenu("字体大小")
        font_group = QActionGroup(self.parent) # 用于互斥选择
        font_group.setExclusive(True)
        
        base_font_size = self.parent.base_font_size
        sizes = {
            "小 (默认)": base_font_size,
            "中": base_font_size + 1,
            "大": base_font_size + 2
        }
        
        for size_name, size_value in sizes.items():
            action = QAction(size_name, self.parent, checkable=True)
            action.setData(size_value) # 存储字体大小值
            action.triggered.connect(lambda checked, s=size_value: set_font_size_callback(s))
            font_group.addAction(action)
            font_size_menu.addAction(action)
            
            # 默认选中"小"
            if size_value == base_font_size:
                action.setChecked(True)
    
    def resize_table_columns(self):
        """根据预设比例调整表格列宽"""
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

        column_proportions = self.parent.column_proportions
        if len(column_proportions) != header.count():
            print("Warning: Column proportions length does not match header count.")
            return
            
        # 设置"卡牌描述"列（索引8）自动拉伸
        header.setSectionResizeMode(8, QHeaderView.Stretch)

        # 按比例设置其他列的宽度
        for i in range(header.count()):
            if i == 8: # 跳过描述列，因为它会自动拉伸
                continue
            proportion = column_proportions[i]
            # 计算宽度，并确保至少有很小的宽度（例如10像素）
            width = max(10, int(available_width * proportion))
            # 设置为 Interactive 允许用户调整，然后设置固定宽度
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            header.resizeSection(i, width) 