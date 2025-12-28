"""
Slave 设备配置对话框
用于添加和配置 Modbus Slave 服务器
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QPushButton,
    QGroupBox, QLabel, QMessageBox, QFileDialog,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from pymodbus_gui.core.slave_server import SlaveConfig, SlaveConnectionType, RegisterPoint
from pymodbus_gui.core.register_manager import RegisterManager


class AddSlaveDialog(QDialog):
    """添加 Slave 对话框"""
    
    slave_configured = pyqtSignal(SlaveConfig)
    
    def __init__(self, parent=None):
        """初始化对话框"""
        super().__init__(parent)
        
        self.register_points: list[RegisterPoint] = []
        self.register_manager = RegisterManager()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("添加 Modbus Slave 服务器")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.slave_id_edit = QLineEdit()
        self.slave_id_edit.setPlaceholderText("唯一标识，如: slave_001")
        basic_layout.addRow("Slave ID*:", self.slave_id_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("描述性名称")
        basic_layout.addRow("名称*:", self.name_edit)
        
        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(["TCP", "RTU"])
        self.connection_type_combo.currentTextChanged.connect(self.on_connection_type_changed)
        basic_layout.addRow("连接类型*:", self.connection_type_combo)
        
        self.device_address_spin = QSpinBox()
        self.device_address_spin.setRange(1, 247)
        self.device_address_spin.setValue(1)
        basic_layout.addRow("从站地址*:", self.device_address_spin)
        
        basic_group.setLayout(basic_layout)
        main_layout.addWidget(basic_group)
        
        # TCP 配置组
        self.tcp_group = QGroupBox("TCP 配置")
        tcp_layout = QFormLayout()
        
        self.host_edit = QLineEdit("0.0.0.0")
        self.host_edit.setPlaceholderText("监听地址，0.0.0.0 表示所有接口")
        tcp_layout.addRow("监听地址:", self.host_edit)
        
        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1, 65535)
        self.tcp_port_spin.setValue(502)
        tcp_layout.addRow("TCP 端口:", self.tcp_port_spin)
        
        self.tcp_group.setLayout(tcp_layout)
        main_layout.addWidget(self.tcp_group)
        
        # RTU 配置组
        self.rtu_group = QGroupBox("RTU 配置")
        rtu_layout = QFormLayout()
        
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("如: COM1 (Windows) 或 /dev/ttyUSB0 (Linux)")
        rtu_layout.addRow("串口端口*:", self.port_edit)
        
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        rtu_layout.addRow("波特率:", self.baudrate_combo)
        
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["8", "7", "6", "5"])
        self.bytesize_combo.setCurrentText("8")
        rtu_layout.addRow("数据位:", self.bytesize_combo)
        
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N (无校验)", "E (偶校验)", "O (奇校验)"])
        self.parity_combo.setCurrentText("N (无校验)")
        rtu_layout.addRow("校验位:", self.parity_combo)
        
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        rtu_layout.addRow("停止位:", self.stopbits_combo)
        
        self.rtu_group.setLayout(rtu_layout)
        main_layout.addWidget(self.rtu_group)
        
        # 寄存器配置组
        register_group = QGroupBox("寄存器配置")
        register_layout = QFormLayout()
        
        self.coil_count_spin = QSpinBox()
        self.coil_count_spin.setRange(0, 65536)
        self.coil_count_spin.setValue(1000)
        register_layout.addRow("线圈数量:", self.coil_count_spin)
        
        self.discrete_input_count_spin = QSpinBox()
        self.discrete_input_count_spin.setRange(0, 65536)
        self.discrete_input_count_spin.setValue(1000)
        register_layout.addRow("离散输入数量:", self.discrete_input_count_spin)
        
        self.holding_register_count_spin = QSpinBox()
        self.holding_register_count_spin.setRange(0, 65536)
        self.holding_register_count_spin.setValue(1000)
        register_layout.addRow("保持寄存器数量:", self.holding_register_count_spin)
        
        self.input_register_count_spin = QSpinBox()
        self.input_register_count_spin.setRange(0, 65536)
        self.input_register_count_spin.setValue(1000)
        register_layout.addRow("输入寄存器数量:", self.input_register_count_spin)
        
        register_group.setLayout(register_layout)
        main_layout.addWidget(register_group)
        
        # 点表配置组
        point_group = QGroupBox("点表配置")
        point_layout = QVBoxLayout()
        
        self.point_label = QLabel("未导入点表")
        self.point_label.setStyleSheet("color: gray;")
        point_layout.addWidget(self.point_label)
        
        point_btn_layout = QHBoxLayout()
        
        self.import_point_btn = QPushButton("导入点表")
        self.import_point_btn.clicked.connect(self.import_register_points)
        point_btn_layout.addWidget(self.import_point_btn)
        
        self.create_template_btn = QPushButton("创建模板")
        self.create_template_btn.clicked.connect(self.create_point_template)
        point_btn_layout.addWidget(self.create_template_btn)
        
        point_btn_layout.addStretch()
        point_layout.addLayout(point_btn_layout)
        
        point_group.setLayout(point_layout)
        main_layout.addWidget(point_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept_config)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 初始显示
        self.on_connection_type_changed("TCP")
    
    def on_connection_type_changed(self, connection_type: str):
        """连接类型改变事件"""
        if connection_type == "TCP":
            self.tcp_group.setVisible(True)
            self.rtu_group.setVisible(False)
        else:
            self.tcp_group.setVisible(False)
            self.rtu_group.setVisible(True)
    
    def import_register_points(self):
        """导入寄存器点表"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入寄存器点表",
            "",
            "Excel 文件 (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        result = self.register_manager.import_register_points(file_path)
        
        if result.success:
            self.register_points = result.data
            self.point_label.setText(f"已导入 {len(self.register_points)} 个点位")
            self.point_label.setStyleSheet("color: green;")
            
            if result.error:
                QMessageBox.warning(self, "部分导入失败", result.error)
            else:
                QMessageBox.information(self, "成功", f"成功导入 {len(self.register_points)} 个点位")
        else:
            QMessageBox.critical(self, "导入失败", result.error)
    
    def create_point_template(self):
        """创建点表模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存点表模板",
            "寄存器点表模板.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        result = self.register_manager.create_template(file_path)
        
        if result.success:
            QMessageBox.information(self, "成功", f"模板已创建:\n{file_path}")
        else:
            QMessageBox.critical(self, "失败", result.error)
    
    def validate_input(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.slave_id_edit.text().strip():
            return False, "请输入 Slave ID"
        
        if not self.name_edit.text().strip():
            return False, "请输入 Slave 名称"
        
        connection_type = self.connection_type_combo.currentText()
        
        if connection_type == "RTU":
            if not self.port_edit.text().strip():
                return False, "RTU 模式需要指定串口端口"
        
        return True, ""
    
    def accept_config(self):
        """接受配置"""
        # 验证输入
        valid, error = self.validate_input()
        if not valid:
            QMessageBox.warning(self, "输入错误", error)
            return
        
        # 获取连接类型
        connection_type_str = self.connection_type_combo.currentText()
        connection_type = SlaveConnectionType.TCP if connection_type_str == "TCP" else SlaveConnectionType.RTU
        
        # 创建配置
        config = SlaveConfig(
            slave_id=self.slave_id_edit.text().strip(),
            name=self.name_edit.text().strip(),
            connection_type=connection_type,
            device_address=self.device_address_spin.value()
        )
        
        # TCP 配置
        if connection_type == SlaveConnectionType.TCP:
            config.host = self.host_edit.text().strip()
            config.tcp_port = self.tcp_port_spin.value()
        
        # RTU 配置
        else:
            config.port = self.port_edit.text().strip()
            config.baudrate = int(self.baudrate_combo.currentText())
            config.bytesize = int(self.bytesize_combo.currentText())
            
            parity_text = self.parity_combo.currentText()
            config.parity = parity_text[0]  # N, E, O
            
            stopbits_text = self.stopbits_combo.currentText()
            config.stopbits = int(float(stopbits_text))
        
        # 寄存器配置
        config.coil_count = self.coil_count_spin.value()
        config.discrete_input_count = self.discrete_input_count_spin.value()
        config.holding_register_count = self.holding_register_count_spin.value()
        config.input_register_count = self.input_register_count_spin.value()
        
        # 点表配置
        config.register_points = self.register_points
        
        # 验证点表
        if self.register_points:
            result = self.register_manager.validate_points(self.register_points)
            if not result.success:
                reply = QMessageBox.question(
                    self,
                    "点表验证失败",
                    f"{result.error}\n\n是否继续？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # 发送信号
        self.slave_configured.emit(config)
        self.accept()
