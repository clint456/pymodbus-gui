"""
Slave 列表管理界面
显示和管理所有 Modbus Slave 服务器
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from pymodbus_gui.core.slave_server import SlaveManager, ModbusSlave, SlaveConfig


class SlaveListWidget(QWidget):
    """Slave 列表控件"""
    
    # 信号
    slave_selected = pyqtSignal(str)  # Slave 被选中
    slave_added = pyqtSignal(str)  # Slave 被添加
    slave_removed = pyqtSignal(str)  # Slave 被移除
    status_message = pyqtSignal(str)  # 状态消息
    
    def __init__(self, slave_manager: SlaveManager, parent=None):
        """
        初始化控件
        
        Args:
            slave_manager: Slave 管理器
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.slave_manager = slave_manager
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # 标题
        title_label = QLabel("Slave 服务器列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Slave 列表
        self.slave_list = QListWidget()
        self.slave_list.itemClicked.connect(self.on_slave_clicked)
        self.slave_list.itemDoubleClicked.connect(self.on_slave_double_clicked)
        self.slave_list.setSpacing(2)  # 列表项之间的间距
        layout.addWidget(self.slave_list)
        
        # 按钮组
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        
        self.add_btn = QPushButton("添加")
        self.add_btn.setToolTip("添加新的 Slave 服务器")
        self.add_btn.clicked.connect(self.add_slave)
        button_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("移除")
        self.remove_btn.setToolTip("移除选中的 Slave 服务器")
        self.remove_btn.clicked.connect(self.remove_slave)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)
        
        button_layout.addStretch()
        
        self.start_all_btn = QPushButton("启动全部")
        self.start_all_btn.setToolTip("启动所有 Slave 服务器")
        self.start_all_btn.clicked.connect(self.start_all_slaves)
        button_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("停止全部")
        self.stop_all_btn.setToolTip("停止所有 Slave 服务器")
        self.stop_all_btn.clicked.connect(self.stop_all_slaves)
        button_layout.addWidget(self.stop_all_btn)
        
        layout.addLayout(button_layout)
        
        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        self.update_stats()
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
    
    def refresh_list(self):
        """刷新 Slave 列表"""
        self.slave_list.clear()
        
        for slave in self.slave_manager.get_all_slaves():
            item_text = self.format_slave_item(slave)
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, slave.config.slave_id)
            
            # 根据运行状态设置颜色
            if slave.running:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif slave.error_message:
                item.setForeground(Qt.GlobalColor.red)
            
            self.slave_list.addItem(item)
        
        self.update_stats()
    
    def format_slave_item(self, slave: ModbusSlave) -> str:
        """
        格式化 Slave 列表项文本
        
        Args:
            slave: Slave 对象
            
        Returns:
            格式化的文本
        """
        config = slave.config
        status = "● 运行" if slave.running else "○ 停止"
        
        if config.connection_type.value == "TCP":
            conn_info = f"TCP:{config.tcp_port}"
        else:
            conn_info = f"RTU:{config.port}"
        
        points_count = len(config.register_points)
        
        return f"{status} | {config.name} | {conn_info} | {points_count}点"
    
    def on_slave_clicked(self, item: QListWidgetItem):
        """Slave 项被单击"""
        slave_id = item.data(Qt.ItemDataRole.UserRole)
        self.remove_btn.setEnabled(True)
        self.slave_selected.emit(slave_id)
    
    def on_slave_double_clicked(self, item: QListWidgetItem):
        """Slave 项被双击"""
        slave_id = item.data(Qt.ItemDataRole.UserRole)
        slave = self.slave_manager.get_slave(slave_id)
        
        if slave:
            if slave.running:
                self.status_message.emit(f"{slave.config.name} 正在运行")
            else:
                # 尝试启动
                result = self.slave_manager.start_slave(slave_id)
                if result.success:
                    self.status_message.emit(result.data)
                    self.refresh_list()
                else:
                    QMessageBox.warning(self, "启动失败", result.error)
    
    def add_slave(self):
        """添加 Slave"""
        # 这个信号会被主窗口接收并显示添加对话框
        self.slave_added.emit("request_add")
    
    def remove_slave(self):
        """移除 Slave"""
        current_item = self.slave_list.currentItem()
        if not current_item:
            return
        
        slave_id = current_item.data(Qt.ItemDataRole.UserRole)
        slave = self.slave_manager.get_slave(slave_id)
        
        if not slave:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 Slave '{slave.config.name}' 吗？\n如果服务器正在运行，将自动停止。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = self.slave_manager.remove_slave(slave_id)
            
            if result.success:
                self.status_message.emit(f"已删除 Slave: {slave.config.name}")
                self.slave_removed.emit(slave_id)
                self.refresh_list()
                self.remove_btn.setEnabled(False)
            else:
                QMessageBox.critical(self, "删除失败", result.error)
    
    def start_all_slaves(self):
        """启动所有 Slave"""
        slaves = self.slave_manager.get_all_slaves()
        
        if not slaves:
            QMessageBox.information(self, "提示", "没有可启动的 Slave 服务器")
            return
        
        success_count = 0
        fail_count = 0
        
        for slave in slaves:
            if not slave.running:
                result = slave.start()
                if result.success:
                    success_count += 1
                else:
                    fail_count += 1
        
        self.refresh_list()
        self.status_message.emit(f"启动完成: 成功 {success_count} 个，失败 {fail_count} 个")
        
        if fail_count > 0:
            QMessageBox.warning(
                self,
                "部分启动失败",
                f"成功启动 {success_count} 个 Slave\n失败 {fail_count} 个"
            )
    
    def stop_all_slaves(self):
        """停止所有 Slave"""
        slaves = self.slave_manager.get_all_slaves()
        
        if not slaves:
            return
        
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
            self.refresh_list()
            self.status_message.emit(f"已停止所有 Slave 服务器")
    
    def update_stats(self):
        """更新统计信息"""
        slaves = self.slave_manager.get_all_slaves()
        total = len(slaves)
        running = sum(1 for s in slaves if s.running)
        stopped = total - running
        
        self.stats_label.setText(
            f"总计: {total} | 运行中: {running} | 已停止: {stopped}"
        )
    
    def get_selected_slave_id(self) -> str | None:
        """获取当前选中的 Slave ID"""
        current_item = self.slave_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
