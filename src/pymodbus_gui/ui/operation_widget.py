"""
设备操作面板
支持完整的 Modbus 功能码操作
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QSpinBox, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from pymodbus_gui.core.device_manager import DeviceManager


class OperationWidget(QWidget):
    """操作面板组件"""
    
    FUNCTION_CODES = {
        "01 - 读线圈": 1,
        "02 - 读离散输入": 2,
        "03 - 读保持寄存器": 3,
        "04 - 读输入寄存器": 4,
        "05 - 写单个线圈": 5,
        "06 - 写单个寄存器": 6,
        "15 - 写多个线圈": 15,
        "16 - 写多个寄存器": 16,
    }
    
    def __init__(self, device_manager: DeviceManager, parent=None):
        """
        初始化操作面板
        
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
        
        # 设备选择和功能选择
        control_group = QGroupBox("操作控制")
        control_layout = QFormLayout()
        
        # 设备选择
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)
        
        refresh_device_btn = QPushButton("刷新")
        refresh_device_btn.clicked.connect(self.refresh_device_list)
        device_layout.addWidget(refresh_device_btn)
        control_layout.addRow("选择设备:", device_layout)
        
        # 功能码选择
        self.function_combo = QComboBox()
        self.function_combo.addItems(self.FUNCTION_CODES.keys())
        self.function_combo.currentTextChanged.connect(self.on_function_changed)
        control_layout.addRow("功能码:", self.function_combo)
        
        # 起始地址
        self.address_spin = QSpinBox()
        self.address_spin.setRange(0, 65535)
        self.address_spin.setValue(0)
        control_layout.addRow("起始地址:", self.address_spin)
        
        # 数量/值
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 125)
        self.count_spin.setValue(10)
        self.count_label = QLabel("读取数量:")
        control_layout.addRow(self.count_label, self.count_spin)
        
        # 写入值（用于写操作）
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("单个值: 123 或 True/False; 多个值: 1,2,3,4")
        self.value_edit.setVisible(False)
        self.value_label = QLabel("写入值:")
        self.value_label.setVisible(False)
        control_layout.addRow(self.value_label, self.value_edit)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 执行按钮
        button_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton("执行操作")
        self.execute_btn.clicked.connect(self.execute_operation)
        self.execute_btn.setStyleSheet("background-color: #0D825D; color: white; font-weight: bold;")
        button_layout.addWidget(self.execute_btn)
        
        self.clear_btn = QPushButton("清空结果")
        self.clear_btn.clicked.connect(self.clear_result)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 结果显示
        result_group = QGroupBox("操作结果")
        result_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["地址", "值", "十六进制"])
        
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        result_layout.addWidget(self.result_table)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 初始化
        self.refresh_device_list()
        self.on_function_changed(list(self.FUNCTION_CODES.keys())[0])
    
    def refresh_device_list(self):
        """刷新设备列表"""
        self.device_combo.clear()
        
        devices = self.device_manager.get_all_devices()
        connected_devices = [d for d in devices if d.connected]
        
        if connected_devices:
            for device in connected_devices:
                self.device_combo.addItem(
                    f"{device.config.name} ({device.config.device_id})",
                    device.config.device_id
                )
        else:
            self.device_combo.addItem("无已连接设备", None)
    
    def on_device_changed(self, text: str):
        """设备选择改变"""
        pass
    
    def on_function_changed(self, text: str):
        """功能码选择改变"""
        func_code = self.FUNCTION_CODES.get(text, 1)
        
        # 读操作
        if func_code in [1, 2, 3, 4]:
            self.count_label.setText("读取数量:")
            self.count_spin.setVisible(True)
            self.count_label.setVisible(True)
            self.value_edit.setVisible(False)
            self.value_label.setVisible(False)
        
        # 写单个
        elif func_code in [5, 6]:
            self.count_spin.setVisible(False)
            self.count_label.setVisible(False)
            self.value_edit.setVisible(True)
            self.value_label.setVisible(True)
            self.value_label.setText("写入值:")
        
        # 写多个
        elif func_code in [15, 16]:
            self.count_spin.setVisible(False)
            self.count_label.setVisible(False)
            self.value_edit.setVisible(True)
            self.value_label.setVisible(True)
            self.value_label.setText("写入值(逗号分隔):")
    
    def get_selected_device_id(self) -> str:
        """获取选中的设备ID"""
        return self.device_combo.currentData()
    
    def execute_operation(self):
        """执行操作"""
        device_id = self.get_selected_device_id()
        
        if not device_id:
            QMessageBox.warning(self, "提示", "请先连接一个设备")
            return
        
        device = self.device_manager.get_device(device_id)
        if not device or not device.connected:
            QMessageBox.warning(self, "提示", "设备未连接")
            return
        
        func_text = self.function_combo.currentText()
        func_code = self.FUNCTION_CODES.get(func_text)
        address = self.address_spin.value()
        
        try:
            result = None
            
            # 读操作
            if func_code == 1:
                count = self.count_spin.value()
                result = device.read_coils(address, count)
            elif func_code == 2:
                count = self.count_spin.value()
                result = device.read_discrete_inputs(address, count)
            elif func_code == 3:
                count = self.count_spin.value()
                result = device.read_holding_registers(address, count)
            elif func_code == 4:
                count = self.count_spin.value()
                result = device.read_input_registers(address, count)
            
            # 写单个
            elif func_code == 5:
                value_str = self.value_edit.text().strip().lower()
                if value_str in ['true', '1', 'on']:
                    value = True
                elif value_str in ['false', '0', 'off']:
                    value = False
                else:
                    raise ValueError("线圈值必须是 True/False 或 1/0")
                result = device.write_single_coil(address, value)
            
            elif func_code == 6:
                value = int(self.value_edit.text().strip())
                if not (0 <= value <= 65535):
                    raise ValueError("寄存器值必须在 0-65535 之间")
                result = device.write_single_register(address, value)
            
            # 写多个
            elif func_code == 15:
                value_str = self.value_edit.text().strip()
                values = []
                for v in value_str.split(','):
                    v = v.strip().lower()
                    if v in ['true', '1', 'on']:
                        values.append(True)
                    elif v in ['false', '0', 'off']:
                        values.append(False)
                    else:
                        raise ValueError(f"无效的线圈值: {v}")
                result = device.write_multiple_coils(address, values)
            
            elif func_code == 16:
                value_str = self.value_edit.text().strip()
                values = [int(v.strip()) for v in value_str.split(',')]
                for v in values:
                    if not (0 <= v <= 65535):
                        raise ValueError(f"寄存器值 {v} 超出范围 0-65535")
                result = device.write_multiple_registers(address, values)
            
            # 显示结果
            if result and result.success:
                self.display_result(result.data, func_code)
                if self.parent_window:
                    self.parent_window.log_message(
                        f"设备 {device_id} 执行功能码 {func_code} 成功", 
                        "SUCCESS"
                    )
            else:
                QMessageBox.critical(self, "操作失败", result.error if result else "未知错误")
                if self.parent_window:
                    self.parent_window.log_message(
                        f"设备 {device_id} 执行功能码 {func_code} 失败: {result.error if result else '未知错误'}", 
                        "ERROR"
                    )
        
        except ValueError as e:
            QMessageBox.warning(self, "参数错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "异常", f"执行异常: {str(e)}")
    
    def display_result(self, data: dict, func_code: int):
        """显示操作结果"""
        self.result_table.setRowCount(0)
        
        # 读操作结果
        if func_code in [1, 2, 3, 4] and 'values' in data:
            values = data['values']
            start_addr = data['address']
            
            for i, value in enumerate(values):
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)
                
                # 地址
                self.result_table.setItem(row, 0, QTableWidgetItem(str(start_addr + i)))
                
                # 值
                self.result_table.setItem(row, 1, QTableWidgetItem(str(value)))
                
                # 十六进制（仅用于寄存器）
                if func_code in [3, 4]:
                    hex_val = f"0x{value:04X}"
                    self.result_table.setItem(row, 2, QTableWidgetItem(hex_val))
                else:
                    self.result_table.setItem(row, 2, QTableWidgetItem("-"))
        
        # 写操作结果
        else:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            
            if 'address' in data:
                self.result_table.setItem(row, 0, QTableWidgetItem(str(data['address'])))
            
            if 'value' in data:
                self.result_table.setItem(row, 1, QTableWidgetItem(str(data['value'])))
            elif 'count' in data:
                self.result_table.setItem(row, 1, QTableWidgetItem(f"写入 {data['count']} 个值"))
            
            self.result_table.setItem(row, 2, QTableWidgetItem("成功"))
    
    def clear_result(self):
        """清空结果"""
        self.result_table.setRowCount(0)
