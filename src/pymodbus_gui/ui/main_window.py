"""
主窗口界面
完整的中文界面，支持多设备管理和 Modbus 操作
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from pymodbus_gui.core.device_manager import DeviceManager
from pymodbus_gui.core.excel_manager import ExcelManager
from pymodbus_gui.core.slave_server import SlaveManager
from pymodbus_gui.core.register_manager import RegisterManager


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
        self.slave_manager = SlaveManager()
        self.register_manager = RegisterManager()
        
        # 初始化界面
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Modbus Poll/Slave 管理工具 v2.0")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)
        
        # 设置全局样式
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border: 1px solid #c0c0c0;
                border-bottom-color: white;
            }
            QTabBar::tab:!selected {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                margin-top: 2px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                background-color: #f8f8f8;
                min-height: 14px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                gridline-color: #e0e0e0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QListWidget {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)
        
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
        
        # Poll 客户端菜单
        poll_menu = menubar.addMenu("Poll客户端(&P)")
        
        # 添加设备
        add_device_action = QAction("添加 Poll 客户端(&A)", self)
        add_device_action.setShortcut("Ctrl+N")
        add_device_action.setStatusTip("手动添加新的 Modbus Poll 客户端设备")
        add_device_action.triggered.connect(self.add_device_dialog)
        poll_menu.addAction(add_device_action)
        
        # 断开所有连接
        disconnect_all_action = QAction("断开所有连接(&D)", self)
        disconnect_all_action.setStatusTip("断开所有 Poll 客户端的连接")
        disconnect_all_action.triggered.connect(self.disconnect_all_devices)
        poll_menu.addAction(disconnect_all_action)
        
        # Slave 服务器菜单
        slave_menu = menubar.addMenu("Slave服务器(&S)")
        
        # 添加 Slave
        add_slave_action = QAction("添加 Slave 服务器(&A)", self)
        add_slave_action.setShortcut("Ctrl+Shift+N")
        add_slave_action.setStatusTip("手动添加新的 Modbus Slave 服务器")
        add_slave_action.triggered.connect(self.add_slave_dialog)
        slave_menu.addAction(add_slave_action)
        
        slave_menu.addSeparator()
        
        # 创建点表模板
        point_template_action = QAction("创建点表模板(&T)", self)
        point_template_action.setStatusTip("创建寄存器点表模板")
        point_template_action.triggered.connect(self.create_point_template)
        slave_menu.addAction(point_template_action)
        
        slave_menu.addSeparator()
        
        # 停止所有 Slave
        stop_all_slaves_action = QAction("停止所有服务器(&S)", self)
        stop_all_slaves_action.setStatusTip("停止所有 Slave 服务器")
        stop_all_slaves_action.triggered.connect(self.stop_all_slaves)
        slave_menu.addAction(stop_all_slaves_action)
        
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
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距
        main_layout.setSpacing(10)  # 设置间距
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # 使用文档模式，更简洁
        main_layout.addWidget(self.tab_widget)
        
        # Poll 管理选项卡（合并设备列表和操作）
        self.create_poll_tab()
        
        # Slave 管理选项卡
        self.create_slave_tab()
    
    def create_poll_tab(self):
        """创建 Poll 管理选项卡"""
        # 创建一个容器 widget
        poll_container = QWidget()
        poll_main_layout = QVBoxLayout(poll_container)
        poll_main_layout.setContentsMargins(10, 10, 10, 10)
        poll_main_layout.setSpacing(10)
        
        # 上方：设备列表和操作面板
        poll_top_layout = QHBoxLayout()
        poll_top_layout.setSpacing(15)
        
        # 左侧：Poll 设备列表
        from pymodbus_gui.ui.device_list_widget import DeviceListWidget
        self.device_list_widget = DeviceListWidget(self.device_manager, self)
        self.device_list_widget.setMinimumWidth(320)
        self.device_list_widget.setMaximumWidth(400)
        poll_top_layout.addWidget(self.device_list_widget)
        
        # 右侧：Poll 操作面板
        from pymodbus_gui.ui.operation_widget import OperationWidget
        self.operation_widget = OperationWidget(self.device_manager, self)
        poll_top_layout.addWidget(self.operation_widget, 1)
        
        poll_main_layout.addLayout(poll_top_layout, 3)
        
        # 下方：Poll 日志
        from pymodbus_gui.ui.log_widget import LogWidget
        self.poll_log_widget = LogWidget(self)
        poll_main_layout.addWidget(self.poll_log_widget, 1)
        
        self.tab_widget.addTab(poll_container, "Poll 客户端管理")
    
    def create_slave_tab(self):
        """创建 Slave 管理选项卡"""
        # 创建一个容器 widget
        slave_container = QWidget()
        slave_main_layout = QVBoxLayout(slave_container)
        slave_main_layout.setContentsMargins(10, 10, 10, 10)
        slave_main_layout.setSpacing(10)
        
        # 上方：Slave列表和详情
        slave_top_layout = QHBoxLayout()
        slave_top_layout.setSpacing(15)
        
        # 左侧：Slave 列表
        from pymodbus_gui.ui.slave_list_widget import SlaveListWidget
        self.slave_list_widget = SlaveListWidget(self.slave_manager, self)
        self.slave_list_widget.slave_selected.connect(self.on_slave_selected)
        self.slave_list_widget.slave_added.connect(lambda: self.add_slave_dialog())
        self.slave_list_widget.slave_removed.connect(self.on_slave_removed)
        self.slave_list_widget.status_message.connect(lambda msg: self.log_slave_message(msg))
        self.slave_list_widget.setMinimumWidth(320)
        self.slave_list_widget.setMaximumWidth(400)
        slave_top_layout.addWidget(self.slave_list_widget)
        
        # 右侧：Slave 详情（动态显示）
        self.slave_detail_container = QWidget()
        self.slave_detail_layout = QVBoxLayout(self.slave_detail_container)
        
        # 默认显示欢迎信息
        welcome_label = QLabel(
            "<h2>Modbus Slave 服务器</h2>"
            "<p>从左侧列表选择 Slave 服务器，或点击 '添加 Slave' 按钮创建新的服务器。</p>"
            "<h3>功能特性：</h3>"
            "<ul>"
            "<li>支持 RTU 和 TCP 协议</li>"
            "<li>支持功能码 1-21</li>"
            "<li>支持多 Slave 并发运行</li>"
            "<li>Excel 点表导入/导出</li>"
            "<li>寄存器实时监控和编辑</li>"
            "</ul>"
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setWordWrap(True)
        self.slave_detail_layout.addWidget(welcome_label)
        
        slave_top_layout.addWidget(self.slave_detail_container, 1)
        
        slave_main_layout.addLayout(slave_top_layout, 3)
        
        # 下方：Slave 日志
        from pymodbus_gui.ui.log_widget import LogWidget
        self.slave_log_widget = LogWidget(self)
        slave_main_layout.addWidget(self.slave_log_widget, 1)
        
        self.tab_widget.addTab(slave_container, "Slave 服务器")
        
        # 存储当前显示的 Slave widget
        self.current_slave_widget = None
    
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
        <h2>Modbus Poll & Slave 管理工具 v2.0</h2>
        <p>功能强大的 Modbus RTU/TCP 客户端和服务器管理软件</p>
        
        <h3>主要特性：</h3>
        <h4>Poll 客户端功能：</h4>
        <ul>
            <li>支持 Modbus RTU 和 TCP 协议</li>
            <li>支持功能码 1-21 的完整操作</li>
            <li>支持多设备并发连接管理</li>
            <li>Excel 配置导入/导出</li>
        </ul>
        
        <h4>Slave 服务器功能：</h4>
        <ul>
            <li>支持 RTU 和 TCP Slave 服务器</li>
            <li>支持功能码 1-21</li>
            <li>支持多 Slave 并发运行</li>
            <li>Excel 点表导入/导出</li>
            <li>寄存器实时监控和编辑</li>
        </ul>
        
        <p>完整的中文界面 | 操作日志记录</p>
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
    
    def add_slave_dialog(self):
        """显示添加 Slave 对话框"""
        from pymodbus_gui.ui.add_slave_dialog import AddSlaveDialog
        dialog = AddSlaveDialog(self)
        dialog.slave_configured.connect(self.on_slave_configured)
        dialog.exec()
    
    def on_slave_configured(self, config):
        """Slave 配置完成"""
        result = self.slave_manager.add_slave(config)
        
        if result.success:
            self.slave_list_widget.refresh_list()
            self.show_status_message(result.data)
            QMessageBox.information(self, "成功", result.data)
        else:
            QMessageBox.critical(self, "失败", result.error)
    
    def on_slave_selected(self, slave_id: str):
        """Slave 被选中"""
        slave = self.slave_manager.get_slave(slave_id)
        if not slave:
            return
        
        # 清理旧的 widget
        if self.current_slave_widget:
            self.slave_detail_layout.removeWidget(self.current_slave_widget)
            self.current_slave_widget.cleanup()
            self.current_slave_widget.deleteLater()
            self.current_slave_widget = None
        
        # 创建新的 Slave widget
        from pymodbus_gui.ui.slave_register_widget import SlaveRegisterWidget
        self.current_slave_widget = SlaveRegisterWidget(slave, self)
        self.current_slave_widget.status_message.connect(lambda msg: self.log_slave_message(msg))
        self.current_slave_widget.slave_status_changed.connect(self.on_slave_status_changed)  # 连接状态变化信号
        self.slave_detail_layout.addWidget(self.current_slave_widget)
    
    def on_slave_removed(self, slave_id: str):
        """Slave 被移除"""
        # 如果当前显示的就是被删除的 Slave，清理界面
        if self.current_slave_widget:
            self.slave_detail_layout.removeWidget(self.current_slave_widget)
            self.current_slave_widget.cleanup()
            self.current_slave_widget.deleteLater()
            self.current_slave_widget = None
    
    def on_slave_status_changed(self):
        """Slave 状态变化"""
        # 刷新 Slave 列表显示
        self.slave_list_widget.refresh_list()
    
    def create_point_template(self):
        """创建寄存器点表模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "创建点表模板",
            "寄存器点表模板.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        result = self.register_manager.create_template(file_path)
        
        if result.success:
            QMessageBox.information(self, "成功", f"点表模板已创建:\n{file_path}")
            self.show_status_message("模板创建成功")
        else:
            QMessageBox.critical(self, "失败", result.error)
    
    def stop_all_slaves(self):
        """停止所有 Slave"""
        slaves = self.slave_manager.get_all_slaves()
        running_count = sum(1 for s in slaves if s.running)
        
        if running_count == 0:
            QMessageBox.information(self, "提示", "没有正在运行的 Slave 服务器")
            return
        
        reply = QMessageBox.question(
            self,
            "确认停止",
            f"确定要停止所有正在运行的 Slave 服务器吗？\n共 {running_count} 个",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.slave_manager.stop_all()
            self.slave_list_widget.refresh_list()
            self.show_status_message("已停止所有 Slave 服务器")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出应用程序吗？\n所有连接和服务器将被停止。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 断开所有 Poll 设备连接
            self.device_manager.disconnect_all()
            # 停止所有 Slave 服务器
            self.slave_manager.stop_all()
            event.accept()
        else:
            event.ignore()
    
    def log_message(self, message: str, level: str = "INFO", target: str = "poll"):
        """
        记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO/WARNING/ERROR/SUCCESS)
            target: 日志目标 ("poll" 或 "slave")
        """
        if target == "slave":
            self.slave_log_widget.add_log(message, level)
        else:
            self.poll_log_widget.add_log(message, level)
    
    def log_slave_message(self, message: str, level: str = "INFO"):
        """
        记录Slave日志消息的便捷方法
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO/WARNING/ERROR/SUCCESS)
        """
        self.slave_log_widget.add_log(message, level)
        self.show_status_message(message)  # 同时显示在状态栏
