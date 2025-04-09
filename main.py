import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QMessageBox, QWidget, QDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# 尝试导入主应用程序类
try:
    from deck_builder import DeckBuilder
    print("DeckBuilder loaded successfully.")
except ImportError as e:
    print(f"错误：无法导入 DeckBuilder: {e}")
    DeckBuilder = None # 标记为加载失败

try:
    from hearthstone_pack_simulator import HearthstonePackSimulator
    print("HearthstonePackSimulator loaded successfully.")
except ImportError as e:
    print(f"错误：无法导入 HearthstonePackSimulator: {e}")
    HearthstonePackSimulator = None # 标记为加载失败

try:
    from hearthstone_data_manager import HearthstoneDataManager
    print("HearthstoneDataManager loaded successfully.")
except ImportError as e:
    print(f"错误：无法导入 HearthstoneDataManager: {e}")
    HearthstoneDataManager = None # 标记为加载失败

class UpdateThread(QThread):
    """更新数据的线程"""
    finished = pyqtSignal(bool)  # 发送更新是否成功的信号

    def run(self):
        try:
            data_manager = HearthstoneDataManager()
            success = data_manager.run_all()
            self.finished.emit(success)
        except Exception as e:
            print(f"更新过程中出错: {e}")
            self.finished.emit(False)

class UpdateDialog(QDialog):
    """更新进度窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更新数据")
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)  # 禁用关闭按钮
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加提示标签
        self.label = QLabel("正在更新数据，请勿关闭程序...", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # 创建并启动更新线程
        self.update_thread = UpdateThread()
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.start()
    
    def on_update_finished(self, success):
        """更新完成后的处理"""
        self.accept()  # 关闭对话框
        if success:
            QMessageBox.information(self.parent(), "更新完成", "卡牌数据更新成功！")
        else:
            QMessageBox.warning(self.parent(), "更新失败", "卡牌数据更新失败，请检查控制台输出。")

class MainApp(QMainWindow):
    """主应用程序窗口，直接集成功能选择"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("选择功能")
        self.resize(400, 250)  # 设置一个合适的窗口大小
        
        # 保存打开的窗口引用，防止垃圾回收
        self.deck_builder_window = None
        self.pack_simulator_window = None
        self.update_dialog = None
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.addWidget(QLabel("请选择要启动的功能："))
        
        # 根据模块是否成功加载来添加按钮
        if DeckBuilder:
            btn_deck_builder = QPushButton("卡组构建器")
            btn_deck_builder.clicked.connect(lambda: self.handle_tool_selection("deck_builder"))
            layout.addWidget(btn_deck_builder)
        else:
            layout.addWidget(QLabel("卡组构建器加载失败 (查看控制台)"))

        if HearthstonePackSimulator:
            btn_pack_sim = QPushButton("开包模拟器")
            btn_pack_sim.clicked.connect(lambda: self.handle_tool_selection("pack_simulator"))
            layout.addWidget(btn_pack_sim)
        else:
            layout.addWidget(QLabel("开包模拟器加载失败 (查看控制台)"))

        if HearthstoneDataManager:
            btn_data_manager = QPushButton("下载/更新数据")
            btn_data_manager.clicked.connect(lambda: self.handle_tool_selection("data_manager"))
            layout.addWidget(btn_data_manager)
        else:
            layout.addWidget(QLabel("数据管理器加载失败 (查看控制台)"))

        # 添加分隔符和取消按钮
        layout.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.close)
        layout.addWidget(btn_cancel)
    
    def handle_tool_selection(self, selected_tool):
        """处理工具选择"""
        if selected_tool == "deck_builder" and DeckBuilder:
            print("正在启动卡组构建器...")
            self.deck_builder_window = DeckBuilder()
            self.deck_builder_window.show()
            # 工具窗口打开后最小化主窗口
            self.setWindowState(Qt.WindowMinimized)
        
        elif selected_tool == "pack_simulator" and HearthstonePackSimulator:
            print("正在启动开包模拟器...")
            self.pack_simulator_window = HearthstonePackSimulator()
            self.pack_simulator_window.show()
            # 工具窗口打开后最小化主窗口
            self.setWindowState(Qt.WindowMinimized)
        
        elif selected_tool == "data_manager" and HearthstoneDataManager:
            print("正在启动数据管理器...")
            # 显示确认对话框
            reply = QMessageBox.question(self, '确认更新',
                                      "确定要下载/更新卡牌数据吗？\n这可能需要一些时间。",
                                      QMessageBox.Yes | QMessageBox.No,
                                      QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 显示更新进度窗口
                self.update_dialog = UpdateDialog(self)
                self.update_dialog.exec_()

def run_app():
    """主函数，处理应用程序的启动流程"""
    # 检查是否至少有一个模块成功加载
    if not DeckBuilder and not HearthstonePackSimulator and not HearthstoneDataManager:
         # 在尝试显示任何Qt窗口前打印错误
         print("致命错误：所有功能模块都未能加载。程序无法启动。")
         # 如果可能，尝试显示一个简单的消息框
         app_temp = QApplication.instance() # 尝试获取现有实例
         if not app_temp:
             app_temp = QApplication(sys.argv) # 创建一个临时实例
         QMessageBox.critical(None, "启动错误", "所有功能模块都未能加载。\n请检查控制台输出以获取详细信息。\n程序将退出。")
         sys.exit(1) # 退出程序

    # 创建主 QApplication 实例
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # 设置一个现代的外观风格

    # 创建并显示主应用窗口
    main_app = MainApp()
    main_app.show()
    
    # 启动事件循环
    print("启动 Qt 事件循环...")
    exit_code = app.exec_()
    print(f"应用程序退出，代码: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    print("正在执行 main.py...")
    run_app() 