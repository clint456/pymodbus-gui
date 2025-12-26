"""
主窗口界面
完整的中文界面，支持多设备管理和 Modbus 操作
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from pymodbus_gui.core.device_manager import DeviceManager
from pymodbus_gui.core.excel_manager import ExcelManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 自定义信号
    device_added = pyqtSignal(str)  # 设备添加信号
    device_removed = pyqtSignal(str)  # 设备移除信号
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化管理器
        self.device_manager = DeviceManager()
        self.excel_manager = ExcelManager()
        
        # 初始化界面
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Modbus 设备管理工具 v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中心部件
        self.create_central_widget()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 显示欢迎信息
        self.show_status_message("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 导入配置
        import_action = QAction("导入设备配置(&I)", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("从 Excel 文件导入设备配置")
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        # 导出配置
        export_action = QAction("导出设备配置(&E)", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("将设备配置导出到 Excel 文件")
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        # 创建模板
        template_action = QAction("创建配置模板(&T)", self)
        template_action.setStatusTip("创建设备配置模板文件")
        template_action.triggered.connect(self.create_template)
        file_menu.addAction(template_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设备菜单
        device_menu = menubar.addMenu("设备(&D)")
        
        # 添加设备
        add_device_action = QAction("添加设备(&A)", self)
        add_device_action.setShortcut("Ctrl+N")
        add_device_action.setStatusTip("手动添加新设备")
        add_device_action.triggered.connect(self.add_device_dialog)
        device_menu.addAction(add_device_action)
        
        # 断开所有连接
        disconnect_all_action = QAction("断开所有连接(&D)", self)
        disconnect_all_action.setStatusTip("断开所有设备的连接")
        disconnect_all_action.triggered.connect(self.disconnect_all_devices)
        device_menu.addAction(disconnect_all_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于此应用程序")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 使用说明
        usage_action = QAction("使用说明(&U)", self)
        usage_action.setStatusTip("查看使用说明")
        usage_action.triggered.connect(self.show_usage)
        help_menu.addAction(usage_action)
    
    def create_central_widget(self):
        """创建中心部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 设备管理选项卡
        from pymodbus_gui.ui.device_list_widget import DeviceListWidget
        self.device_list_widget = DeviceListWidget(self.device_manager, self)
        self.tab_widget.addTab(self.device_list_widget, "设备管理")
        
        # 操作面板选项卡
        from pymodbus_gui.ui.operation_widget import OperationWidget
        self.operation_widget = OperationWidget(self.device_manager, self)
        self.tab_widget.addTab(self.operation_widget, "设备操作")
        
        # 日志选项卡
        from pymodbus_gui.ui.log_widget import LogWidget
        self.log_widget = LogWidget(self)
        self.tab_widget.addTab(self.log_widget, "操作日志")
    
    def create_status_bar(self):
        """创建状态栏"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
    
    def show_status_message(self, message: str, timeout: int = 5000):
        """
        显示状态栏消息
        
        Args:
            message: 消息内容
            timeout: 显示时长（毫秒）
        """
        self.statusBar.showMessage(message, timeout)
    
    def import_config(self):
        """导入设备配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入设备配置",
            "",
            "Excel 文件 (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        # 导入配置
        result = self.excel_manager.import_devices(file_path)
        
        if result.success:
            devices = result.data
            success_count = 0
            
            for device_config in devices:
                add_result = self.device_manager.add_device(device_config)
                if add_result.success:
                    success_count += 1
            
            self.device_list_widget.refresh_device_list()
            
            message = f"成功导入 {success_count}/{len(devices)} 个设备"
            if result.error:
                message += f"\n\n警告:\n{result.error}"
            
            QMessageBox.information(self, "导入完成", message)
            self.show_status_message(f"导入了 {success_count} 个设备")
        else:
            QMessageBox.critical(self, "导入失败", result.error)
    
    def export_config(self):
        """导出设备配置"""
        devices = self.device_manager.get_all_devices()
        
        if not devices:
            QMessageBox.warning(self, "导出失败", "没有可导出的设备配置")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出设备配置",
            "设备配置.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        # 导出配置
        configs = [device.config for device in devices]
        result = self.excel_manager.export_devices(configs, file_path)
        
        if result.success:
            QMessageBox.information(self, "导出成功", result.data)
            self.show_status_message("配置导出成功")
        else:
            QMessageBox.critical(self, "导出失败", result.error)
    
    def create_template(self):
        """创建配置模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "创建配置模板",
            "设备配置模板.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        result = self.excel_manager.create_template(file_path)
        
        if result.success:
            QMessageBox.information(self, "创建成功", f"配置模板已保存到:\n{file_path}")
            self.show_status_message("模板创建成功")
        else:
            QMessageBox.critical(self, "创建失败", result.error)
    
    def add_device_dialog(self):
        """显示添加设备对话框"""
        from pymodbus_gui.ui.add_device_dialog import AddDeviceDialog
        dialog = AddDeviceDialog(self.device_manager, self)
        if dialog.exec():
            self.device_list_widget.refresh_device_list()
            self.show_status_message("设备添加成功")
    
    def disconnect_all_devices(self):
        """断开所有设备连接"""
        reply = QMessageBox.question(
            self,
            "确认操作",
            "确定要断开所有设备的连接吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.device_manager.disconnect_all()
            self.device_list_widget.refresh_device_list()
            self.show_status_message("已断开所有设备连接")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>Modbus 设备管理工具 v2.0</h2>
        <p>功能强大的 Modbus RTU/TCP 设备管理软件</p>
        
        <h3>主要特性：</h3>
        <ul>
            <li>支持 Modbus RTU 和 TCP 协议</li>
            <li>支持功能码 1-21 的完整操作</li>
            <li>支持多设备并发连接管理</li>
            <li>Excel 配置导入/导出</li>
            <li>完整的中文界面</li>
            <li>操作日志记录</li>
        </ul>
        
        <p>© 2025 版权所有</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def show_usage(self):
        """显示使用说明"""
        usage_text = """
        <h3>使用说明</h3>
        
        <h4>1. 设备管理</h4>
        <ul>
            <li>点击"添加设备"按钮手动添加设备</li>
            <li>使用"导入设备配置"从 Excel 批量导入</li>
            <li>双击设备可以编辑配置</li>
            <li>选中设备后可以连接/断开/删除</li>
        </ul>
        
        <h4>2. 设备操作</h4>
        <ul>
            <li>在"设备操作"选项卡中选择已连接的设备</li>
            <li>选择要执行的功能码操作</li>
            <li>输入地址和参数</li>
            <li>点击"执行"按钮进行操作</li>
        </ul>
        
        <h4>3. Excel 配置</h4>
        <ul>
            <li>使用"创建配置模板"生成示例文件</li>
            <li>在 Excel 中编辑设备信息</li>
            <li>通过"导入设备配置"批量添加设备</li>
        </ul>
        
        <h4>4. 支持的功能码</h4>
        <p>01-读线圈, 02-读离散输入, 03-读保持寄存器, 04-读输入寄存器<br>
        05-写单个线圈, 06-写单个寄存器, 15-写多个线圈, 16-写多个寄存器</p>
        """
        QMessageBox.information(self, "使用说明", usage_text)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出应用程序吗？\n所有连接将被断开。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 断开所有连接
            self.device_manager.disconnect_all()
            event.accept()
        else:
            event.ignore()
    
    def log_message(self, message: str, level: str = "INFO"):
        """
        记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO/WARNING/ERROR/SUCCESS)
        """
        self.log_widget.add_log(message, level)
