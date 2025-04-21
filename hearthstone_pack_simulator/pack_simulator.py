import os
import sys
from datetime import datetime
from collections import defaultdict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                          QHBoxLayout, QLabel, QPushButton, QListWidget, 
                          QListWidgetItem, QAbstractItemView, QTextEdit, 
                          QMessageBox, QDialog, QSplitter, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

# 导入自定义模块
from config import (RARITY_NAMES, RARITY_TAGS, SET_NAMES, CLASS_NAMES,
                 GUARANTEE_RARE_OR_HIGHER, LEGENDARY_PITY_TIMER,
                 RARITY_PROBABILITIES)
# 修改导入路径
from .simulator.simulator import PackSimulator, CardDataManager
from .ui.text_display_manager import TextDisplayManager
from .ui.ui_dialogs import PackCountDialog, RarityProbabilityDialog
from .report_generator import ReportGenerator

# 修改导入路径
from deck_builder.deck_builder_main import DeckBuilder

# 修改导入语句
from hearthstone_data_manager.data_manager import HearthstoneDataManager

class HearthstonePackSimulator(QMainWindow):
    def __init__(self):
        """初始化炉石传说卡包模拟器"""
        super().__init__()
        
        # 初始化模拟器和显示管理器
        self.card_manager = CardDataManager()
        self.simulator = PackSimulator(self.card_manager)
        self.display_manager = TextDisplayManager()
        
        # 初始化报告生成器
        self.report_generator = ReportGenerator()
        
        # 初始化UI元素
        self.rarity_tags = RARITY_TAGS
        
        # 抽卡设置
        self.selected_sets = []
        self.pack_counts = {}
        self.all_opened_cards = []  # 存储本次模拟中所有抽到的卡牌
        
        # 加载卡牌数据
        self.load_card_data()
        
        # 创建UI
        self.init_ui()
        
    def load_card_data(self):
        """加载所有可收藏卡牌数据"""
        try:
            result = self.card_manager.load_card_data()
            
            if not result:
                QMessageBox.critical(self, "错误", "加载卡牌数据失败，请检查数据路径")
                sys.exit(1)
            
        except Exception as e:
            print(f"加载卡牌数据时出错: {e}")
            QMessageBox.critical(self, "错误", f"加载卡牌数据时出错: {str(e)}")
            sys.exit(1)
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("炉石传说卡包模拟器")
        self.setMinimumSize(1000, 700)
        
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
        
        # 标题
        title_label = QLabel("扩展包选择")
        title_label.setFont(QFont("Sans Serif", 12, QFont.Bold))
        left_layout.addWidget(title_label)
        
        # 列表
        self.sets_list = QListWidget()
        self.sets_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.sets_list.setMinimumWidth(300)
        
        # 按照SET_NAMES中的顺序排序扩展包
        all_sets = self.card_manager.cards_by_set.items()
        
        # 创建一个按SET_NAMES顺序排序的函数
        def get_set_order(set_item):
            set_id = set_item[0]
            # 如果在SET_NAMES中，按其索引排序
            if set_id in SET_NAMES:
                # 获取在SET_NAMES中的索引位置
                keys = list(SET_NAMES.keys())
                return keys.index(set_id)
            # 如果不在SET_NAMES中，放到最后
            return float('inf')
        
        # 按照SET_NAMES的顺序排序
        sorted_sets = sorted(all_sets, key=get_set_order)
        
        # 填充扩展包列表
        for set_id, set_info in sorted_sets:
            # 获取本地化的扩展包名称
            localized_name = self.display_manager.get_localized_set_name(set_id)
            # 只使用本地化名称显示，不显示英文ID和括号
            item = QListWidgetItem(f"{localized_name}")
            # 存储原始ID作为用户数据
            item.setData(Qt.UserRole, set_id)
            self.sets_list.addItem(item)
        
        left_layout.addWidget(self.sets_list)
        
        # 按钮组
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.set_count_btn = QPushButton("设置抽卡数量")
        self.set_count_btn.clicked.connect(self.configure_pack_counts)
        buttons_layout.addWidget(self.set_count_btn)
        
        self.start_btn = QPushButton("开始抽卡")
        self.start_btn.clicked.connect(self.start_simulation)
        buttons_layout.addWidget(self.start_btn)
        
        self.set_prob_btn = QPushButton("设置稀有度概率")
        self.set_prob_btn.clicked.connect(self.configure_rarity_probabilities)
        buttons_layout.addWidget(self.set_prob_btn)
        
        self.gen_transmog_btn = QPushButton("生成幻变卡牌报告")
        self.gen_transmog_btn.clicked.connect(self.generate_transmog_report)
        buttons_layout.addWidget(self.gen_transmog_btn)
        
        self.gen_report_btn = QPushButton("生成抽卡报告")
        self.gen_report_btn.clicked.connect(self.generate_report)
        self.gen_report_btn.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.gen_report_btn)
        
        # 添加包含核心和活动卡的复选框
        self.include_core_event = QCheckBox("包含核心和活动卡")
        self.include_core_event.setChecked(True)  # 默认勾选
        buttons_layout.addWidget(self.include_core_event)
        
        left_layout.addLayout(buttons_layout)
        
        # ===== 右侧面板 =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 结果区域标题
        result_title = QLabel("抽卡结果")
        result_title.setFont(QFont("Sans Serif", 12, QFont.Bold))
        right_layout.addWidget(result_title)
        
        # 结果文本框
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Monospace", 10))
        self.results_text.setMinimumWidth(500)
        
        # 设置默认内容
        self.results_text.setPlainText("选择扩展包并设置卡包数量后，点击「开始抽卡」按钮开始模拟抽卡。")
        
        right_layout.addWidget(self.results_text)
        
        # 添加两个面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置初始大小比例
        splitter.setSizes([300, 700])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        # 显示窗口
        self.show()
        
    def configure_pack_counts(self):
        """配置每个扩展包的抽卡数量"""
        try:
            # 获取当前选中的扩展包
            selected_sets = {}
            for item in self.sets_list.selectedItems():
                set_id = item.data(Qt.UserRole)
                if set_id and set_id in self.card_manager.cards_by_set:
                    # 使用本地化的扩展包名称
                    localized_name = self.display_manager.get_localized_set_name(set_id)
                    selected_sets[set_id] = {
                        'name': localized_name
                    }
            
            if not selected_sets:
                QMessageBox.information(self, "提示", "请先选择至少一个扩展包")
                return
            
            # 保存选中的扩展包，以便在对话框关闭后仍能记住选择
            self.selected_sets = list(selected_sets.keys())
            
            # 创建并显示设置对话框
            dialog = PackCountDialog(self, selected_sets)
            
            # 显示对话框并等待结果
            result = dialog.exec_()
            
            # 只有在用户点击确认后才处理结果
            if result == QDialog.Accepted:
                try:
                    # 获取设置数据
                    new_pack_counts = dialog.get_pack_counts()
                    
                    # 检验数据有效性
                    if new_pack_counts and isinstance(new_pack_counts, dict):
                        self.pack_counts = new_pack_counts
                        
                        # 更新状态信息
                        count_info = []
                        for set_id, count in self.pack_counts.items():
                            if set_id in self.card_manager.cards_by_set:
                                # 使用本地化的扩展包名称
                                localized_name = self.display_manager.get_localized_set_name(set_id)
                                count_info.append(f"{localized_name}: {count}")
                        
                        if count_info:
                            self.statusBar().showMessage("已设置抽卡数量: " + ", ".join(count_info))
                    else:
                        # 数据无效，显示错误
                        print("获取的卡包数量数据无效")
                        self.statusBar().showMessage("设置卡包数量失败，请重试")
                except Exception as e:
                    print(f"处理卡包数量设置结果时出错: {e}")
                    self.statusBar().showMessage(f"设置卡包数量时出错: {str(e)}")
        except Exception as e:
            print(f"设置卡包数量时出错: {e}")
            QMessageBox.critical(self, "错误", f"设置卡包数量时出错: {str(e)}")
    
    def start_simulation(self):
        """开始抽卡模拟"""
        if not self.selected_sets:
            QMessageBox.information(self, "提示", "请先选择至少一个扩展包")
            return
        
        if not self.pack_counts:
            QMessageBox.information(self, "提示", "请先设置卡包数量")
            return
        
        try:
            # 显示正在抽卡的提示
            self.statusBar().showMessage("正在模拟抽卡，请稍候...")
            QApplication.processEvents()  # 让UI响应
            
            # 清空结果显示和之前的抽卡记录
            self.results_text.clear()
            self.all_opened_cards = []
            
            # 重置模拟器的传说卡记录
            self.simulator.reset_legendary_records()
            
            # 统计信息
            total_packs = 0
            rarity_counts = defaultdict(int)
            
            # 进行抽卡模拟
            for set_id in self.selected_sets:
                if set_id not in self.pack_counts:
                    continue
                
                pack_count = self.pack_counts[set_id]
                if pack_count <= 0:
                    continue
                
                # 检查扩展包数据是否存在
                if set_id not in self.card_manager.cards_by_set:
                    print(f"警告: 扩展包 {set_id} 数据不存在")
                    continue
                
                # 显示扩展包标题（只显示本地化名称，不显示英文ID和括号）
                set_name = self.display_manager.get_localized_set_name(set_id)
                self.append_to_results(f"\n=== {set_name} ===\n\n")
                
                # 初始化或重置该扩展包的保底计数器
                if set_id not in self.card_manager.pity_counter:
                    self.card_manager.pity_counter[set_id] = 0
                
                # 模拟抽卡
                for i in range(pack_count):
                    QApplication.processEvents()  # 处理事件，保持UI响应
                    
                    self.append_to_results(f"卡包 #{i+1}:\n")
                    
                    try:
                        # 抽取5张卡片
                        cards = self.simulator.simulate_pack_opening(set_id)
                        
                        # 显示结果
                        for card in cards:
                            rarity = card.get('rarity', 'COMMON')
                            rarity_counts[rarity] += 1
                            
                            # 保存抽到的卡牌用于报告生成
                            self.all_opened_cards.append(card)
                            
                            # 如果是传说卡，记录已抽到
                            if rarity == 'LEGENDARY':
                                card_id = card.get('id', '')
                                if card_id:
                                    self.simulator.add_legendary_record(set_id, card_id)
                            
                            # 根据稀有度添加不同颜色标记
                            card_name = card.get('name', '未知卡牌')
                            localized_rarity = self.display_manager.get_localized_rarity_name(rarity)
                            rarity_tag = self.rarity_tags.get(rarity, "【灰】")
                            
                            # 构建卡牌描述（只显示中文稀有度名称）
                            card_desc = f"  {rarity_tag}{card_name} ({localized_rarity})\n"
                            
                            # 计算颜色
                            color = QColor("black")
                            if rarity == 'LEGENDARY':
                                color = QColor("orange")
                            elif rarity == 'EPIC':
                                color = QColor("purple")
                            elif rarity == 'RARE':
                                color = QColor("blue")
                            
                            self.append_to_results(card_desc, color=color)
                        
                        self.append_to_results("\n")
                        
                        # 更新总卡包数
                        total_packs += 1
                        
                    except Exception as e:
                        self.append_to_results(f"  抽卡出错: {str(e)}\n", color=QColor("#FF0000"))
                
            # 模拟完成
            if total_packs > 0:
                # 启用报告生成按钮
                self.gen_report_btn.setEnabled(True)
                
                # 显示文本形式的统计信息
                # 计算稀有度百分比
                total_cards = sum(rarity_counts.values())
                percentages = {k: (v / total_cards * 100) for k, v in rarity_counts.items()}
                
                # 按稀有度顺序排序
                rarity_order = ['LEGENDARY', 'EPIC', 'RARE', 'COMMON']
                sorted_rarities = sorted(rarity_counts.keys(), key=lambda x: rarity_order.index(x) if x in rarity_order else 999)
                
                # 显示统计信息文本
                stats_text = f"\n\n=== 抽卡统计 ===\n\n"
                stats_text += f"总计抽取: {total_packs}个卡包 ({total_cards}张卡牌)\n\n"
                
                stats_text += "稀有度分布:\n"
                for rarity in sorted_rarities:
                    localized_rarity = self.display_manager.get_localized_rarity_name(rarity)
                    rarity_tag = self.rarity_tags.get(rarity, "【灰】")
                    stats_text += f"  {rarity_tag}{localized_rarity}: {rarity_counts[rarity]}张 ({percentages[rarity]:.2f}%)\n"
                
                # 显示统计文本
                self.append_to_results(stats_text)
                
                # 成功消息
                self.statusBar().showMessage(f"抽卡模拟完成！共模拟了 {total_packs} 个卡包的开启。")
            else:
                self.statusBar().showMessage("未能模拟任何卡包的开启。")
                
        except Exception as e:
            self.statusBar().showMessage("抽卡模拟出错")
            QMessageBox.critical(self, "错误", f"抽卡模拟过程中出错：{str(e)}")
    
    def append_to_results(self, text, color=None):
        """添加文本到结果显示区域，可选颜色"""
        cursor = self.results_text.textCursor()
        
        # 保存当前格式
        current_format = cursor.charFormat()
        
        # 如果指定了颜色，设置新格式
        if color:
            format = cursor.charFormat()
            format.setForeground(color)
            cursor.setCharFormat(format)
        
        # 添加文本
        cursor.insertText(text)
        
        # 恢复原始格式
        if color:
            cursor.setCharFormat(current_format)
        
        # 滚动到最新内容
        self.results_text.setTextCursor(cursor)
        self.results_text.ensureCursorVisible()
    
    def generate_report(self):
        """生成抽卡报告"""
        if not self.all_opened_cards:
            QMessageBox.information(self, "提示", "没有抽卡记录，请先进行抽卡")
            return
        
        try:
            # 显示正在生成报告的提示
            self.statusBar().showMessage("正在生成报告，请稍候...")
            QApplication.processEvents()  # 让UI响应
            
            # 获取时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 获取是否包含核心和活动卡的选项
            include_core_event = self.include_core_event.isChecked()
            
            # 生成Excel报告
            excel_report_path = self.report_generator.generate_pack_report(
                self.all_opened_cards, 
                timestamp,
                include_core_event=include_core_event
            )
            
            # 生成HTML报告
            html_report_path = os.path.join(os.path.dirname(excel_report_path), f"抽卡报告_{timestamp}.html")
            
            # 获取QTextEdit的HTML内容并增强
            enhanced_html = self.enhance_html_report()
            
            # 写入HTML文件
            with open(html_report_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_html)
            
            # 检查报告是否生成成功
            reports_generated = []
            if excel_report_path and os.path.exists(excel_report_path):
                reports_generated.append(f"Excel报告: {excel_report_path}")
            
            if os.path.exists(html_report_path):
                reports_generated.append(f"HTML报告: {html_report_path}")
                
            if reports_generated:
                # 显示成功信息
                self.statusBar().showMessage(f"报告已生成")
                
                # 延迟一下让UI有时间响应
                QApplication.processEvents()
                
                # 显示成功消息，修改提示内容
                report_msg = "\n".join(reports_generated)
                QMessageBox.information(self, "成功", f"抽卡报告已生成：\n{report_msg}\n\n可以手动打开HTML报告，并点击\"打印\"保存为PDF")
                
                # 打开报告文件所在目录
                try:
                    os.startfile(os.path.dirname(excel_report_path))
                except Exception as e:
                    print(f"打开报告目录失败: {e}")
            else:
                self.statusBar().showMessage("生成报告失败")
                QMessageBox.warning(self, "警告", "生成报告失败，请查看控制台输出")
                
        except Exception as e:
            print(f"生成报告时出错: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"生成报告时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成报告时出错: {str(e)}")
            
        finally:
            # 确保UI保持响应
            QApplication.processEvents()
            
    def enhance_html_report(self):
        """创建增强的HTML报告，保留颜色信息"""
        # 创建HTML文档头部
        html_doc = f"""<!DOCTYPE HTML>
<html>
<head>
    <meta charset="utf-8">
    <title>炉石传说抽卡报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.5;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .report-container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
        h1 {{
            color: #1E6BB8;
            text-align: center;
            margin-bottom: 30px;
        }}
        .pack-title {{
            font-weight: bold;
            margin: 10px 0 5px 0;
            background-color: #f0f0f0;
            padding: 5px;
            border-radius: 3px;
        }}
        .expansion-title {{
            font-size: 20px;
            font-weight: bold;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px solid #ddd;
            color: #333;
        }}
        .card {{
            margin-bottom: 5px;
            padding: 3px;
            border-radius: 3px;
        }}
        .legendary {{
            color: #FF7D0A !important;
            font-weight: bold;
        }}
        .epic {{
            color: #A335EE !important;
            font-weight: bold;
        }}
        .rare {{
            color: #0070DD !important;
        }}
        .common {{
            color: #888888 !important;
        }}
        .statistics {{
            margin-top: 30px;
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
        }}
        .timestamp {{
            text-align: right;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
        }}
        /* 打印时的样式 */
        @media print {{
            body {{
                background-color: white;
                margin: 0;
            }}
            .report-container {{
                box-shadow: none;
                max-width: 100%;
            }}
            .legendary {{
                color: #FF7D0A !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            .epic {{
                color: #A335EE !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            .rare {{
                color: #0070DD !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            .common {{
                color: #888888 !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <h1>炉石传说抽卡报告</h1>
        <div class="content">
"""

        # 直接从QTextEdit获取内容
        text_content = self.results_text.toPlainText()
        
        # 按行处理文本，并使用原始颜色信息
        lines = text_content.split('\n')
        in_statistics = False
        
        for line in lines:
            # 处理扩展包标题
            if line.strip().startswith('=== ') and line.strip().endswith(' ==='):
                expansion_name = line.strip(' =').strip()
                html_doc += f'<div class="expansion-title">{expansion_name}</div>\n'
                continue
                
            # 处理卡包编号
            if '卡包 #' in line or line.strip().startswith('第 '):
                html_doc += f'<div class="pack-title">{line}</div>\n'
                continue
                
            # 处理卡牌信息（使用原始颜色标记直接映射到CSS类）
            if '【橙】' in line:
                html_doc += f'<div class="card legendary">{line}</div>\n'
            elif '【紫】' in line:
                html_doc += f'<div class="card epic">{line}</div>\n'
            elif '【蓝】' in line:
                html_doc += f'<div class="card rare">{line}</div>\n'
            elif '【灰】' in line:
                html_doc += f'<div class="card common">{line}</div>\n'
            # 处理统计信息标题
            elif line.strip() == '=== 抽卡统计 ===':
                html_doc += f'<div class="statistics-title">{line.strip(" =")}</div>\n'
                html_doc += '<div class="statistics">\n'
                in_statistics = True
                continue
            # 处理普通行
            elif line.strip():
                html_doc += f'<div>{line}</div>\n'
            else:
                html_doc += '<br/>\n'
        
        # 关闭统计信息区域
        if in_statistics:
            html_doc += '</div>\n'
        
        # 添加时间戳
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_doc += f'<div class="timestamp">报告生成时间: {current_time}</div>\n'
        
        # 完成HTML文档
        html_doc += """
        </div>
    </div>
</body>
</html>
"""
        return html_doc
    
    def reset_simulator(self):
        """重置模拟器状态"""
        try:
            # 重置模拟器
            self.simulator.reset_legendary_records()
            
            # 清空结果显示
            self.results_text.clear()
            
            # 禁用报告按钮
            self.gen_report_btn.setEnabled(False)
            
            # 显示重置消息
            self.statusBar().showMessage("模拟器已重置")
            
            # 重新显示欢迎信息
            self.results_text.setPlainText("选择扩展包并设置卡包数量后，点击「开始抽卡」按钮开始模拟抽卡。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重置模拟器时出错：{str(e)}")
    
    def configure_rarity_probabilities(self):
        """配置不同稀有度的概率"""
        try:
            dialog = RarityProbabilityDialog(self, RARITY_PROBABILITIES)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # 获取设置的概率并更新到模拟器
                probabilities = dialog.get_probabilities()
                self.simulator.set_rarity_probabilities(probabilities)
                self.statusBar().showMessage("已更新稀有度概率设置")
        except Exception as e:
            print(f"设置稀有度概率时出错: {e}")
            QMessageBox.critical(self, "错误", f"设置稀有度概率时出错: {str(e)}")

    def generate_transmog_report(self):
        """生成幻变卡牌报告"""
        # 获取当前选中的扩展包
        selected_sets = []
        for item in self.sets_list.selectedItems():
            set_id = item.data(Qt.UserRole)
            if set_id:
                selected_sets.append(set_id)
        
        if not selected_sets:
            QMessageBox.information(self, "提示", "请先选择至少一个扩展包")
            return
        
        try:
            # 显示正在生成报告的提示
            self.statusBar().showMessage("正在生成幻变卡牌报告，请稍候...")
            QApplication.processEvents()  # 让UI响应
            
            # 获取时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 获取是否包含核心和活动卡的选项
            include_core_event = self.include_core_event.isChecked()
            
            # 生成Excel报告
            excel_report_path = self.report_generator.generate_transmog_report(
                selected_sets, 
                timestamp,
                include_core_event=include_core_event
            )
            
            # 检查报告是否生成成功
            if excel_report_path and os.path.exists(excel_report_path):
                # 显示成功信息
                self.statusBar().showMessage(f"幻变卡牌报告已生成")
                
                # 延迟一下让UI有时间响应
                QApplication.processEvents()
                
                # 显示成功消息
                QMessageBox.information(self, "成功", f"幻变卡牌报告已生成：\n{excel_report_path}")
                
                # 打开报告文件所在目录
                try:
                    os.startfile(os.path.dirname(excel_report_path))
                except Exception as e:
                    print(f"打开报告目录失败: {e}")
            else:
                self.statusBar().showMessage("生成幻变卡牌报告失败")
                QMessageBox.warning(self, "警告", "生成幻变卡牌报告失败，请查看控制台输出")
                
        except Exception as e:
            print(f"生成幻变卡牌报告时出错: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"生成幻变卡牌报告时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成幻变卡牌报告时出错: {str(e)}")
            
        finally:
            # 确保UI保持响应
            QApplication.processEvents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 实例化并显示
    simulator = HearthstonePackSimulator()
    
    sys.exit(app.exec_())