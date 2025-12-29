"""
Slave 寄存器监控和编辑界面
显示和编辑 Modbus Slave 的寄存器值
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QComboBox, QSpinBox,
    QLineEdit, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

from pymodbus_gui.core.slave_server import ModbusSlave, RegisterPoint
from pymodbus_gui.core.register_manager import RegisterManager


class SlaveRegisterWidget(QWidget):
    """Slave 寄存器监控和编辑界面"""
    
    # 信号
    status_message = pyqtSignal(str)
    slave_status_changed = pyqtSignal()  # 新增：Slave 状态变化信号
    
    def __init__(self, slave: ModbusSlave, parent=None):
        """
        初始化界面
        
        Args:
            slave: Modbus Slave 对象
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.slave = slave
        self.register_manager = RegisterManager()
        self.auto_refresh = False
        
        self.init_ui()
        
        # 设置定时器用于自动刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_values)
        
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()
        
        # 顶部信息栏
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel()
        self.update_info_label()
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        # 状态指示器
        self.status_label = QLabel()
        self.update_status_label()
        info_layout.addWidget(self.status_label)
        
        main_layout.addLayout(info_layout)
        
        # 控制按钮组
        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("启动服务器")
        self.start_btn.clicked.connect(self.start_server)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止服务器")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addWidget(QLabel("|"))
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_values)
        control_layout.addWidget(self.refresh_btn)
        
        self.auto_refresh_btn = QPushButton("自动刷新: 关")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        control_layout.addWidget(self.auto_refresh_btn)
        
        control_layout.addWidget(QLabel("|"))
        
        self.export_btn = QPushButton("导出点表")
        self.export_btn.clicked.connect(self.export_register_points)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # 寄存器显示区域（分标签页）
        self.tab_widget = QTabWidget()
        
        # 创建各类寄存器的表格
        self.coil_table = self.create_register_table('coil')
        self.discrete_input_table = self.create_register_table('discrete_input')
        self.holding_register_table = self.create_register_table('holding_register')
        self.input_register_table = self.create_register_table('input_register')
        
        self.tab_widget.addTab(self.coil_table, f"线圈 ({len(self.get_points_by_type('coil'))})")
        self.tab_widget.addTab(self.discrete_input_table, f"离散输入 ({len(self.get_points_by_type('discrete_input'))})")
        self.tab_widget.addTab(self.holding_register_table, f"保持寄存器 ({len(self.get_points_by_type('holding_register'))})")
        self.tab_widget.addTab(self.input_register_table, f"输入寄存器 ({len(self.get_points_by_type('input_register'))})")
        
        # 文件操作标签页
        if self.slave.config.enable_file_operations:
            self.file_widget = self.create_file_operations_widget()
            self.tab_widget.addTab(self.file_widget, f"文件操作 ({len(self.slave.config.file_records)})")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
        
        # 初始加载数据
        self.refresh_values()
    
    def create_register_table(self, register_type: str) -> QTableWidget:
        """
        创建寄存器表格
        
        Args:
            register_type: 寄存器类型
            
        Returns:
            表格控件
        """
        table = QTableWidget()
        
        # 设置列
        if register_type in ['coil', 'discrete_input']:
            columns = ['地址', '点位名称', '当前值', '描述', '只读', '操作']
        else:
            columns = ['地址', '点位名称', '当前值', '单位', '范围', '描述', '只读', '操作']
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 设置表格属性
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 调整列宽 - 使用 Stretch 实现比例分配
        header = table.horizontalHeader()
        if header:
            if register_type in ['coil', 'discrete_input']:
                # 地址 | 点位名称(拉伸) | 当前值 | 描述(拉伸) | 只读 | 操作(固定)
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 地址
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 点位名称拉伸
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 当前值
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # 描述拉伸
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 只读
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # 操作
                header.resizeSection(5, 80)
            else:
                # 地址 | 点位名称(拉伸) | 当前值 | 单位 | 范围 | 描述(拉伸) | 只读 | 操作(固定)
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 地址
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 点位名称拉伸
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 当前值
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 单位
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 范围
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # 描述拉伸
                header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 只读
                header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # 操作
                header.resizeSection(7, 80)
                header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 只读
                header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # 操作
                header.resizeSection(7, 300)
        
        return table
    
    def create_file_operations_widget(self) -> QWidget:
        """创建文件操作界面"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 文件列表表格
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(7)
        self.file_table.setHorizontalHeaderLabels([
            '文件号', '文件路径', '当前大小', '最大大小', '只读', '描述', '操作'
        ])
        
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 调整列宽
        header = self.file_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(6, 200)
        
        self.refresh_file_table()
        
        layout.addWidget(self.file_table)
        widget.setLayout(layout)
        
        return widget
    
    def refresh_file_table(self):
        """刷新文件表格"""
        file_info = self.slave.get_file_info()
        self.file_table.setRowCount(len(file_info))
        
        for row, info in enumerate(file_info):
            # 文件号
            self.file_table.setItem(row, 0, QTableWidgetItem(str(info['file_number'])))
            
            # 文件路径
            from pathlib import Path
            file_name = Path(info['file_path']).name
            path_item = QTableWidgetItem(file_name)
            path_item.setToolTip(info['file_path'])
            self.file_table.setItem(row, 1, path_item)
            
            # 当前大小
            size_text = f"{info['size']} B"
            self.file_table.setItem(row, 2, QTableWidgetItem(size_text))
            
            # 最大大小
            max_size_text = f"{info['max_size']} B"
            self.file_table.setItem(row, 3, QTableWidgetItem(max_size_text))
            
            # 只读
            read_only_text = "是" if info['read_only'] else "否"
            self.file_table.setItem(row, 4, QTableWidgetItem(read_only_text))
            
            # 描述
            self.file_table.setItem(row, 5, QTableWidgetItem(info['description']))
            
            # 操作按钮
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            read_btn = QPushButton("读取")
            read_btn.clicked.connect(
                lambda checked, fn=info['file_number']: self.read_file(fn)
            )
            btn_layout.addWidget(read_btn)
            
            if not info['read_only']:
                write_btn = QPushButton("写入")
                write_btn.clicked.connect(
                    lambda checked, fn=info['file_number']: self.write_file(fn)
                )
                btn_layout.addWidget(write_btn)
            
            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)
            self.file_table.setCellWidget(row, 6, btn_widget)
    
    def read_file(self, file_number: int):
        """读取文件"""
        result = self.slave.read_file_record(file_number)
        
        if result.success:
            data = result.data
            # 显示文件内容（前256字节）
            preview = data[:256]
            hex_str = ' '.join([f'{b:02X}' for b in preview])
            
            msg = f"文件 {file_number} 读取成功\n"
            msg += f"大小: {len(data)} 字节\n\n"
            msg += f"数据预览 (十六进制，前256字节):\n{hex_str}"
            if len(data) > 256:
                msg += "\n..."
            
            QMessageBox.information(self, "读取成功", msg)
            self.status_message.emit(f"成功读取文件 {file_number}, {len(data)} 字节")
        else:
            QMessageBox.critical(self, "读取失败", result.error)
    
    def write_file(self, file_number: int):
        """写入文件"""
        # 简单的十六进制输入对话框
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(
            self,
            "写入文件数据",
            f"输入要写入文件 {file_number} 的数据 (十六进制，空格分隔):\n例如: 01 02 03 04",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and text:
            try:
                # 解析十六进制数据
                hex_values = text.strip().split()
                data = bytes([int(h, 16) for h in hex_values])
                
                result = self.slave.write_file_record(file_number, 0, data)
                
                if result.success:
                    QMessageBox.information(self, "写入成功", f"成功写入 {len(data)} 字节到文件 {file_number}")
                    self.refresh_file_table()
                    self.status_message.emit(f"成功写入文件 {file_number}, {len(data)} 字节")
                else:
                    QMessageBox.critical(self, "写入失败", result.error)
            except ValueError as e:
                QMessageBox.critical(self, "输入错误", f"无效的十六进制数据: {str(e)}")
    
    def get_points_by_type(self, register_type: str) -> list[RegisterPoint]:
        """获取指定类型的点位列表（按地址排序）"""
        points = [p for p in self.slave.config.register_points if p.register_type == register_type]
        # 按地址排序，确保显示顺序与地址顺序一致
        return sorted(points, key=lambda p: p.address)
    
    def refresh_values(self):
        """刷新所有寄存器值"""
        self.refresh_register_table('coil', self.coil_table)
        self.refresh_register_table('discrete_input', self.discrete_input_table)
        self.refresh_register_table('holding_register', self.holding_register_table)
        self.refresh_register_table('input_register', self.input_register_table)
        
        self.update_status_label()
    
    def refresh_register_table(self, register_type: str, table: QTableWidget):
        """
        刷新寄存器表格
        
        Args:
            register_type: 寄存器类型
            table: 表格控件
        """
        points = self.get_points_by_type(register_type)
        
        table.setRowCount(len(points))
        
        for row, point in enumerate(points):
            # 读取当前值
            result = self.slave.read_register(register_type, point.address)
            current_value = result.data if result.success else "读取失败"
            
            # 地址
            table.setItem(row, 0, QTableWidgetItem(str(point.address)))
            
            # 点位名称
            table.setItem(row, 1, QTableWidgetItem(point.name))
            
            # 当前值
            value_item = QTableWidgetItem(str(current_value))
            if not result.success:
                value_item.setForeground(QColor('red'))
            table.setItem(row, 2, value_item)
            
            col = 3
            
            # 单位（仅寄存器类型）
            if register_type in ['holding_register', 'input_register']:
                table.setItem(row, col, QTableWidgetItem(point.unit))
                col += 1
                
                # 范围
                range_str = ""
                if point.min_value is not None or point.max_value is not None:
                    min_val = point.min_value if point.min_value is not None else "无限制"
                    max_val = point.max_value if point.max_value is not None else "无限制"
                    range_str = f"{min_val} ~ {max_val}"
                table.setItem(row, col, QTableWidgetItem(range_str))
                col += 1
            
            # 描述
            table.setItem(row, col, QTableWidgetItem(point.description))
            col += 1
            
            # 只读
            read_only_text = "是" if point.read_only else "否"
            table.setItem(row, col, QTableWidgetItem(read_only_text))
            col += 1
            
            # 操作按钮
            if not point.read_only:
                write_btn = QPushButton("写入")
                write_btn.clicked.connect(
                    lambda checked, rt=register_type, p=point: self.write_register(rt, p)
                )
                table.setCellWidget(row, col, write_btn)
    
    def write_register(self, register_type: str, point: RegisterPoint):
        """
        写入寄存器值
        
        Args:
            register_type: 寄存器类型
            point: 点位配置
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"写入 - {point.name}")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        form_layout.addRow("地址:", QLabel(str(point.address)))
        form_layout.addRow("点位名称:", QLabel(point.name))
        form_layout.addRow("寄存器类型:", QLabel(self.register_manager.REGISTER_TYPES_CN.get(register_type, register_type)))
        
        # 当前值
        result = self.slave.read_register(register_type, point.address)
        current_value = result.data if result.success else 0
        form_layout.addRow("当前值:", QLabel(str(current_value)))
        
        # 输入新值
        if register_type in ['coil', 'discrete_input']:
            value_input = QComboBox()
            value_input.addItems(["0 (关)", "1 (开)"])
            value_input.setCurrentIndex(int(current_value) if isinstance(current_value, (int, bool)) else 0)
        else:
            value_input = QSpinBox()
            value_input.setRange(0, 65535)
            if point.min_value is not None:
                value_input.setMinimum(int(point.min_value))
            if point.max_value is not None:
                value_input.setMaximum(int(point.max_value))
            value_input.setValue(int(current_value) if isinstance(current_value, int) else 0)
        
        form_layout.addRow("新值*:", value_input)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 获取新值
            if register_type in ['coil', 'discrete_input']:
                new_value = value_input.currentIndex() if isinstance(value_input, QComboBox) else 0
            else:
                new_value = value_input.value() if isinstance(value_input, QSpinBox) else 0
            
            # 写入
            result = self.slave.write_register(register_type, point.address, new_value)
            
            if result.success:
                QMessageBox.information(self, "成功", result.data)
                self.refresh_values()
                self.status_message.emit(f"写入成功: {point.name} = {new_value}")
            else:
                QMessageBox.critical(self, "失败", result.error)
                self.status_message.emit(f"写入失败: {result.error}")
    
    def start_server(self):
        """启动服务器"""
        result = self.slave.start()
        
        if result.success:
            QMessageBox.information(self, "成功", result.data)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.update_status_label()
            self.status_message.emit(result.data)
            self.slave_status_changed.emit()  # 发送状态变化信号
        else:
            QMessageBox.critical(self, "失败", result.error)
            self.status_message.emit(f"启动失败: {result.error}")
    
    def stop_server(self):
        """停止服务器"""
        result = self.slave.stop()
        
        if result.success:
            QMessageBox.information(self, "成功", result.data)
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.update_status_label()
            self.status_message.emit(result.data)
            self.slave_status_changed.emit()  # 发送状态变化信号
        else:
            QMessageBox.warning(self, "提示", result.error)
    
    def toggle_auto_refresh(self):
        """切换自动刷新"""
        self.auto_refresh = not self.auto_refresh
        
        if self.auto_refresh:
            self.auto_refresh_btn.setText("自动刷新: 开")
            self.refresh_timer.start(1000)  # 每秒刷新
            self.status_message.emit("已启用自动刷新")
        else:
            self.auto_refresh_btn.setText("自动刷新: 关")
            self.refresh_timer.stop()
            self.status_message.emit("已禁用自动刷新")
    
    def export_register_points(self):
        """导出寄存器点表"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出寄存器点表",
            f"{self.slave.config.name}_点表.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        result = self.register_manager.export_register_points(
            self.slave.config.register_points,
            file_path
        )
        
        if result.success:
            QMessageBox.information(self, "成功", f"点表已导出:\n{file_path}")
            self.status_message.emit(result.data)
        else:
            QMessageBox.critical(self, "失败", result.error)
    
    def update_info_label(self):
        """更新信息标签"""
        config = self.slave.config
        if config.connection_type.value == "TCP":
            conn_info = f"TCP {config.host}:{config.tcp_port}"
        else:
            conn_info = f"RTU {config.port} {config.baudrate}"
        
        self.info_label.setText(
            f"<b>{config.name}</b> | {conn_info} | 从站地址: {config.device_address} | "
            f"点位数: {len(config.register_points)}"
        )
    
    def update_status_label(self):
        """更新状态标签"""
        if self.slave.running:
            self.status_label.setText("● 运行中")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("● 已停止")
            self.status_label.setStyleSheet("color: gray;")
    
    def cleanup(self):
        """清理资源"""
        self.refresh_timer.stop()
