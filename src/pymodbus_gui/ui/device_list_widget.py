"""
设备列表管理界面
显示和管理所有设备
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

from pymodbus_gui.core.device_manager import DeviceManager, ConnectionType


class DeviceListWidget(QWidget):
    """设备列表组件"""
    
    # 自定义信号
    device_selected = pyqtSignal(str)  # 设备选择信号
    
    def __init__(self, device_manager: DeviceManager, parent=None):
        """
        初始化设备列表组件
        
        Args:
            device_manager: 设备管理器
            parent: 父窗口
        """
        super().__init__(parent)
        self.device_manager = device_manager
        self.parent_window = parent
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        layout.setSpacing(8)  # 设置间距
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(5)  # 按钮之间的间距
        
        # 添加设备按钮
        self.add_btn = QPushButton("添加")
        self.add_btn.setToolTip("添加新的 Poll 客户端设备")
        self.add_btn.clicked.connect(self.add_device)
        toolbar_layout.addWidget(self.add_btn)
        
        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setToolTip("连接选中的设备")
        self.connect_btn.clicked.connect(self.connect_device)
        toolbar_layout.addWidget(self.connect_btn)
        
        # 断开按钮
        self.disconnect_btn = QPushButton("断开")
        self.disconnect_btn.setToolTip("断开选中设备的连接")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        toolbar_layout.addWidget(self.disconnect_btn)
        
        # 删除按钮
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setToolTip("删除选中的设备")
        self.delete_btn.clicked.connect(self.delete_device)
        toolbar_layout.addWidget(self.delete_btn)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setToolTip("刷新设备列表")
        self.refresh_btn.clicked.connect(self.refresh_device_list)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 设备列表表格
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(6)  # 减少列数
        self.device_table.setHorizontalHeaderLabels([
            "状态", "设备名称", "类型", 
            "连接信息", "从站", "超时"
        ])
        
        # 设置表格属性
        self.device_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.device_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.device_table.setAlternatingRowColors(True)
        self.device_table.verticalHeader().setDefaultSectionSize(32)  # 设置行高
        
        # 设置列宽
        header = self.device_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        # 双击事件
        self.device_table.doubleClicked.connect(self.edit_device)
        
        # 右键菜单
        self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.device_table)
        
        # 初始化加载设备列表
        self.refresh_device_list()
    
    def refresh_device_list(self):
        """刷新设备列表"""
        self.device_table.setRowCount(0)
        devices = self.device_manager.get_all_devices()
        
        for device in devices:
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            
            # 状态
            status_item = QTableWidgetItem("●")
            if device.connected:
                status_item.setForeground(QBrush(QColor(13, 130, 93)))  # 绿色
                status_item.setToolTip("已连接")
            else:
                status_item.setForeground(QBrush(QColor(213, 55, 52)))  # 红色
                status_item.setToolTip("未连接" + (f"\n{device.error_message}" if device.error_message else ""))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.device_table.setItem(row, 0, status_item)
            
            # 设备名称
            name_item = QTableWidgetItem(device.config.name)
            name_item.setToolTip(f"设备ID: {device.config.device_id}")
            self.device_table.setItem(row, 1, name_item)
            
            # 类型
            type_item = QTableWidgetItem(device.config.connection_type.value)
            self.device_table.setItem(row, 2, type_item)
            
            # 连接信息
            if device.config.connection_type == ConnectionType.RTU:
                conn_info = f"{device.config.port}\n{device.config.baudrate}bps"
            else:
                conn_info = f"{device.config.host}\n:{device.config.tcp_port}"
            conn_item = QTableWidgetItem(conn_info)
            self.device_table.setItem(row, 3, conn_item)
            
            # 从站地址
            slave_item = QTableWidgetItem(str(device.config.slave_id))
            slave_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.device_table.setItem(row, 4, slave_item)
            
            # 超时
            timeout_item = QTableWidgetItem(f"{device.config.timeout}s")
            timeout_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.device_table.setItem(row, 5, timeout_item)
    
    def get_selected_device_id(self) -> str:
        """
        获取选中的设备ID
        
        Returns:
            设备ID，未选中返回空字符串
        """
        current_row = self.device_table.currentRow()
        if current_row >= 0:
            # 从 tooltip 中获取设备ID
            name_item = self.device_table.item(current_row, 1)
            tooltip = name_item.toolTip()
            if tooltip.startswith("设备ID: "):
                return tooltip.replace("设备ID: ", "")
        return ""
    
    def add_device(self):
        """添加设备"""
        from pymodbus_gui.ui.add_device_dialog import AddDeviceDialog
        dialog = AddDeviceDialog(self.device_manager, self)
        if dialog.exec():
            self.refresh_device_list()
            if self.parent_window:
                self.parent_window.show_status_message("设备添加成功")
    
    def connect_device(self):
        """连接设备"""
        device_id = self.get_selected_device_id()
        if not device_id:
            QMessageBox.warning(self, "提示", "请先选择一个设备")
            return
        
        device = self.device_manager.get_device(device_id)
        if device.connected:
            QMessageBox.information(self, "提示", "设备已经连接")
            return
        
        result = self.device_manager.connect_device(device_id)
        
        if result.success:
            self.refresh_device_list()
            QMessageBox.information(self, "成功", result.data)
            if self.parent_window:
                self.parent_window.log_message(f"设备 {device_id} 连接成功", "SUCCESS")
        else:
            QMessageBox.critical(self, "连接失败", result.error)
            if self.parent_window:
                self.parent_window.log_message(f"设备 {device_id} 连接失败: {result.error}", "ERROR")
        
        self.refresh_device_list()
    
    def disconnect_device(self):
        """断开设备"""
        device_id = self.get_selected_device_id()
        if not device_id:
            QMessageBox.warning(self, "提示", "请先选择一个设备")
            return
        
        device = self.device_manager.get_device(device_id)
        if not device.connected:
            QMessageBox.information(self, "提示", "设备未连接")
            return
        
        result = self.device_manager.disconnect_device(device_id)
        
        if result.success:
            self.refresh_device_list()
            QMessageBox.information(self, "成功", result.data)
            if self.parent_window:
                self.parent_window.log_message(f"设备 {device_id} 断开连接", "INFO")
        else:
            QMessageBox.critical(self, "断开失败", result.error)
    
    def delete_device(self):
        """删除设备"""
        device_id = self.get_selected_device_id()
        if not device_id:
            QMessageBox.warning(self, "提示", "请先选择一个设备")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除设备 '{device_id}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = self.device_manager.remove_device(device_id)
            if result.success:
                self.refresh_device_list()
                if self.parent_window:
                    self.parent_window.show_status_message("设备删除成功")
                    self.parent_window.log_message(f"设备 {device_id} 已删除", "INFO")
            else:
                QMessageBox.critical(self, "删除失败", result.error)
    
    def edit_device(self):
        """编辑设备（双击触发）"""
        device_id = self.get_selected_device_id()
        if not device_id:
            return
        
        device = self.device_manager.get_device(device_id)
        if device.connected:
            QMessageBox.warning(self, "提示", "请先断开设备连接再编辑")
            return
        
        from pymodbus_gui.ui.add_device_dialog import AddDeviceDialog
        dialog = AddDeviceDialog(self.device_manager, self, edit_mode=True, device_config=device.config)
        if dialog.exec():
            self.refresh_device_list()
            if self.parent_window:
                self.parent_window.show_status_message("设备配置已更新")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        if self.device_table.currentRow() < 0:
            return
        
        menu = QMenu()
        
        device_id = self.get_selected_device_id()
        device = self.device_manager.get_device(device_id)
        
        if device:
            if device.connected:
                disconnect_action = menu.addAction("断开连接")
                disconnect_action.triggered.connect(self.disconnect_device)
            else:
                connect_action = menu.addAction("连接")
                connect_action.triggered.connect(self.connect_device)
                
                edit_action = menu.addAction("编辑")
                edit_action.triggered.connect(self.edit_device)
            
            menu.addSeparator()
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(self.delete_device)
        
        menu.exec(self.device_table.viewport().mapToGlobal(position))
