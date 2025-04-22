from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                      QPushButton, QScrollArea, QWidget, QSpinBox, 
                      QApplication, QMessageBox, QGridLayout, QLineEdit)
from PyQt5.QtCore import Qt
# 修改导入语句
from .text_display_manager import TextDisplayManager

class PackCountDialog(QDialog):
    """卡包数量设置对话框"""
    def __init__(self, parent=None, sets_info=None):
        super().__init__(parent)
        self.setWindowTitle("设置卡包数量")
        self.setMinimumWidth(400)
        self.setFixedSize(450, 450)  # 缩小对话框大小，避免内存问题
        
        # 初始化显示管理器
        self.display_manager = TextDisplayManager()
        
        # 将参数拷贝出来而不是直接引用
        self.sets_info = {}
        if sets_info:
            for set_id, set_data in dict(sets_info).items():  # 使用dict()创建副本
                try:
                    self.sets_info[set_id] = {
                        'name': set_data.get('name', set_id)
                    }
                except Exception as e:
                    print(f"处理扩展包 {set_id} 信息时出错: {e}")
                
        self.pack_counts = {}
        self._validated_pack_counts = {}  # 添加一个已验证的数据存储
        
        # 创建主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 如果没有选择扩展包，显示提示信息
        if not self.sets_info:
            label = QLabel("请先选择至少一个扩展包")
            label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(label)
            
            ok_button = QPushButton("确认")
            ok_button.clicked.connect(self.accept)
            ok_button.setMinimumWidth(100)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(ok_button)
            btn_layout.addStretch()
            
            main_layout.addLayout(btn_layout)
            return
        
        # 添加说明标签
        info_label = QLabel("请为每个扩展包设置抽卡数量:")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        
        # 创建滚动内容
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(5)  # 减少间距，显示更多内容
        
        # 为每个扩展包创建设置项，简化处理
        items_count = 0
        set_items = list(self.sets_info.items())[:50]  # 限制最多显示50个扩展包
        
        for set_id, set_info in set_items:
            # 创建一个水平布局的条目
            row = QHBoxLayout()
            
            # 标签只显示中文名称，不显示英文ID和括号
            name = set_info.get('name', '')
            if not name or name == set_id:  # 如果名称为空或等于ID，尝试使用display_manager获取
                name = self.display_manager.get_localized_set_name(set_id)
            if len(name) > 20:  # 截断长名称
                name = name[:20] + "..."
            label = QLabel(name)
            label.setMinimumWidth(200)
            row.addWidget(label)
            
            # 创建一个间隔
            row.addStretch()
            
            # 创建数量输入
            spin = QSpinBox()
            spin.setRange(1, 500)
            spin.setValue(1)
            spin.setFixedWidth(60)
            row.addWidget(spin)
            
            # 保存引用
            self.pack_counts[set_id] = spin
            
            # 将这一行添加到内容布局
            content_layout.addLayout(row)
            items_count += 1
            
            # 如果项目太多，中断添加以避免卡顿
            if items_count >= 50:
                break
                
        # 添加一些空间
        content_layout.addStretch()
        
        # 添加确认取消按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 确认按钮
        ok_button = QPushButton("确认")
        ok_button.clicked.connect(self.validate_and_accept)
        ok_button.setMinimumWidth(100)
        button_layout.addWidget(ok_button)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumWidth(100)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def validate_and_accept(self):
        """验证输入并确认"""
        try:
            # 验证并保存数据
            self._validated_pack_counts = {}
            
            for set_id, spinbox in list(self.pack_counts.items())[:50]:  # 限制处理数量
                try:
                    value = spinbox.value()
                    if value <= 0:
                        value = 1  # 确保至少为1
                    self._validated_pack_counts[set_id] = value
                except Exception as e:
                    print(f"获取 {set_id} 的卡包数量时出错: {e}")
                    self._validated_pack_counts[set_id] = 1  # 出错时使用默认值
            
            # 验证成功，接受对话框
            QApplication.processEvents()  # 处理任何挂起的事件
            self.accept()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"验证卡包数量时出错: {e}")
            # 错误处理时不关闭对话框
            QMessageBox.critical(self, "错误", f"设置卡包数量时出错: {str(e)}")
    
    def get_pack_counts(self):
        """获取用户设置的卡包数量"""
        # 返回已验证的数据
        if self._validated_pack_counts:
            return self._validated_pack_counts
            
        # 如果没有经过验证，简单返回默认值
        result = {}
        for set_id in self.sets_info.keys():
            result[set_id] = 1
                
        return result


class RarityProbabilityDialog(QDialog):
    """稀有度概率设置对话框"""
    def __init__(self, parent=None, current_probabilities=None):
        super().__init__(parent)
        self.setWindowTitle("设置稀有度概率")
        self.setFixedSize(350, 250)  # 固定大小，避免resize导致的布局问题
        
        current_probabilities = current_probabilities or {}
        self.rarity_inputs = {}
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 使用更简单的网格布局
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        # 添加表头
        header_label = QLabel("请输入各稀有度的概率百分比：")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        row = 0
        rarities = [('LEGENDARY', '传说'), ('EPIC', '史诗'), ('RARE', '稀有'), ('COMMON', '普通')]
        for rarity, rarity_name in rarities:
            # 标签
            label = QLabel(f"{rarity_name}:")
            form_layout.addWidget(label, row, 0)
            
            # 输入框
            line_edit = QLineEdit()
            line_edit.setFixedWidth(100)
            value = current_probabilities.get(rarity, 0) * 100
            # 改为四位小数显示
            line_edit.setText(f"{value:.4f}")
            form_layout.addWidget(line_edit, row, 1)
            
            # 百分比标签
            percent_label = QLabel("%")
            form_layout.addWidget(percent_label, row, 2)
            
            self.rarity_inputs[rarity] = line_edit
            row += 1
        
        layout.addLayout(form_layout)
        
        # 添加提示
        hint_label = QLabel("注意: 所有概率之和应为100%")
        hint_label.setStyleSheet("color: #666;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)
        
        # 添加间距
        layout.addStretch(1)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 确认按钮
        ok_button = QPushButton("确认")
        ok_button.clicked.connect(self.validate_and_accept)
        ok_button.setMinimumWidth(100)
        button_layout.addWidget(ok_button)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumWidth(100)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def validate_and_accept(self):
        """验证输入并确认"""
        try:
            total = 0
            probabilities = {}
            
            for rarity, input_field in self.rarity_inputs.items():
                try:
                    # 替换逗号为点，支持不同的数字格式
                    text = input_field.text().replace(',', '.')
                    value = float(text)
                    
                    if value < 0:
                        QMessageBox.warning(self, "警告", f"{rarity}概率不能为负数")
                        return
                        
                    probabilities[rarity] = value
                    total += value
                except ValueError:
                    QMessageBox.warning(self, "警告", f"请为{rarity}输入有效的数字")
                    return
            
            # 检查总和是否接近100%，使用更精确的范围
            if abs(total - 100) > 0.01:
                QMessageBox.warning(self, "警告", 
                               f"所有稀有度概率之和应为100%，当前为{total:.4f}%")
                return
            
            # 把验证通过的值保存下来，保持四位小数精度
            self._validated_probabilities = {rarity: value/100 for rarity, value in probabilities.items()}
            self.accept()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"验证数据时出错: {str(e)}")
    
    def get_probabilities(self):
        """获取用户设置的概率"""
        # 返回已经验证过的概率值
        if hasattr(self, '_validated_probabilities'):
            return self._validated_probabilities
            
        # 如果没有验证过，返回默认值
        from config import RARITY_PROBABILITIES
        return RARITY_PROBABILITIES