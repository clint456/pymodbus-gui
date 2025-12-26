"""
添加/编辑设备对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator

from pymodbus_gui.core.device_manager import DeviceManager, DeviceConfig, ConnectionType
import serial.tools.list_ports


class AddDeviceDialog(QDialog):
    """添加/编辑设备对话框"""
    
    def __init__(self, device_manager: DeviceManager, parent=None, 
                 edit_mode=False, device_config=None):
        """
        初始化对话框
        
        Args:
            device_manager: 设备管理器
            parent: 父窗口
            edit_mode: 是否为编辑模式
            device_config: 编辑时的设备配置
        """
        super().__init__(parent)
        self.device_manager = device_manager
        self.edit_mode = edit_mode
        self.original_config = device_config
        
        self.setWindowTitle("编辑设备" if edit_mode else "添加设备")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.init_ui()
        
        # 如果是编辑模式，加载现有配置
        if edit_mode and device_config:
            self.load_config(device_config)
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        # 设备ID
        self.device_id_edit = QLineEdit()
        self.device_id_edit.setPlaceholderText("唯一标识，如 RTU_001")
        if self.edit_mode:
            self.device_id_edit.setReadOnly(True)
        basic_layout.addRow("设备ID *:", self.device_id_edit)
        
        # 设备名称
        self.device_name_edit = QLineEdit()
        self.device_name_edit.setPlaceholderText("设备描述名称")
        basic_layout.addRow("设备名称 *:", self.device_name_edit)
        
        # 连接类型
        self.conn_type_combo = QComboBox()
        self.conn_type_combo.addItems(["RTU", "TCP"])
        self.conn_type_combo.currentTextChanged.connect(self.on_connection_type_changed)
        basic_layout.addRow("连接类型 *:", self.conn_type_combo)
        
        # 从站地址
        self.slave_id_spin = QSpinBox()
        self.slave_id_spin.setRange(1, 247)
        self.slave_id_spin.setValue(1)
        basic_layout.addRow("从站地址:", self.slave_id_spin)
        
        # 超时时间
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 60.0)
        self.timeout_spin.setValue(3.0)
        self.timeout_spin.setSuffix(" 秒")
        basic_layout.addRow("超时时间:", self.timeout_spin)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # RTU 配置组
        self.rtu_group = QGroupBox("RTU 配置")
        rtu_layout = QFormLayout()
        
        # 串口选择
        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        rtu_layout.addRow("串口端口 *:", port_layout)
        
        # 波特率
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setEditable(True)
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        rtu_layout.addRow("波特率:", self.baudrate_combo)
        
        # 数据位
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["7", "8"])
        self.bytesize_combo.setCurrentText("8")
        rtu_layout.addRow("数据位:", self.bytesize_combo)
        
        # 校验位
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N (无)", "E (偶)", "O (奇)"])
        rtu_layout.addRow("校验位:", self.parity_combo)
        
        # 停止位
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        rtu_layout.addRow("停止位:", self.stopbits_combo)
        
        self.rtu_group.setLayout(rtu_layout)
        layout.addWidget(self.rtu_group)
        
        # TCP 配置组
        self.tcp_group = QGroupBox("TCP 配置")
        tcp_layout = QFormLayout()
        
        # IP地址
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("192.168.1.100")
        tcp_layout.addRow("IP地址 *:", self.host_edit)
        
        # TCP端口
        self.tcp_port_spin = QSpinBox()
        self.tcp_port_spin.setRange(1, 65535)
        self.tcp_port_spin.setValue(502)
        tcp_layout.addRow("TCP端口:", self.tcp_port_spin)
        
        self.tcp_group.setLayout(tcp_layout)
        layout.addWidget(self.tcp_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(test_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept_config)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # 初始状态
        self.on_connection_type_changed("RTU")
    
    def refresh_ports(self):
        """刷新串口列表"""
        current_text = self.port_combo.currentText()
        self.port_combo.clear()
        
        # 获取可用串口
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        if port_list:
            self.port_combo.addItems(port_list)
            if current_text in port_list:
                self.port_combo.setCurrentText(current_text)
        else:
            self.port_combo.addItem("无可用串口")
    
    def on_connection_type_changed(self, conn_type: str):
        """连接类型改变事件"""
        if conn_type == "RTU":
            self.rtu_group.setVisible(True)
            self.tcp_group.setVisible(False)
        else:  # TCP
            self.rtu_group.setVisible(False)
            self.tcp_group.setVisible(True)
    
    def load_config(self, config: DeviceConfig):
        """加载配置到界面"""
        self.device_id_edit.setText(config.device_id)
        self.device_name_edit.setText(config.name)
        self.conn_type_combo.setCurrentText(config.connection_type.value)
        self.slave_id_spin.setValue(config.slave_id)
        self.timeout_spin.setValue(config.timeout)
        
        if config.connection_type == ConnectionType.RTU:
            if config.port:
                self.port_combo.setCurrentText(config.port)
            self.baudrate_combo.setCurrentText(str(config.baudrate))
            self.bytesize_combo.setCurrentText(str(config.bytesize))
            
            parity_map = {'N': 'N (无)', 'E': 'E (偶)', 'O': 'O (奇)'}
            self.parity_combo.setCurrentText(parity_map.get(config.parity, 'N (无)'))
            
            self.stopbits_combo.setCurrentText(str(config.stopbits))
        else:  # TCP
            if config.host:
                self.host_edit.setText(config.host)
            self.tcp_port_spin.setValue(config.tcp_port)
    
    def get_config(self) -> DeviceConfig:
        """从界面获取配置"""
        conn_type = ConnectionType.RTU if self.conn_type_combo.currentText() == "RTU" else ConnectionType.TCP
        
        config = DeviceConfig(
            device_id=self.device_id_edit.text().strip(),
            name=self.device_name_edit.text().strip(),
            connection_type=conn_type,
            slave_id=self.slave_id_spin.value(),
            timeout=self.timeout_spin.value()
        )
        
        if conn_type == ConnectionType.RTU:
            config.port = self.port_combo.currentText().strip()
            config.baudrate = int(self.baudrate_combo.currentText())
            config.bytesize = int(self.bytesize_combo.currentText())
            
            parity_text = self.parity_combo.currentText()
            config.parity = parity_text[0]  # 取第一个字符 N/E/O
            
            config.stopbits = int(self.stopbits_combo.currentText())
        else:  # TCP
            config.host = self.host_edit.text().strip()
            config.tcp_port = self.tcp_port_spin.value()
        
        return config
    
    def validate_config(self, config: DeviceConfig) -> tuple:
        """
        验证配置
        
        Returns:
            (是否有效, 错误消息)
        """
        if not config.device_id:
            return False, "设备ID不能为空"
        
        if not config.name:
            return False, "设备名称不能为空"
        
        if config.connection_type == ConnectionType.RTU:
            if not config.port or config.port == "无可用串口":
                return False, "请选择有效的串口端口"
        else:  # TCP
            if not config.host:
                return False, "IP地址不能为空"
        
        return True, ""
    
    def test_connection(self):
        """测试连接"""
        config = self.get_config()
        valid, error = self.validate_config(config)
        
        if not valid:
            QMessageBox.warning(self, "验证失败", error)
            return
        
        # 创建临时设备进行测试
        from pymodbus_gui.core.device_manager import ModbusDevice
        test_device = ModbusDevice(config)
        
        result = test_device.connect()
        
        if result.success:
            test_device.disconnect()
            QMessageBox.information(self, "测试成功", "设备连接测试成功！")
        else:
            QMessageBox.critical(self, "测试失败", f"连接测试失败:\n{result.error}")
    
    def accept_config(self):
        """确认配置"""
        config = self.get_config()
        valid, error = self.validate_config(config)
        
        if not valid:
            QMessageBox.warning(self, "验证失败", error)
            return
        
        # 添加或更新设备
        if self.edit_mode:
            # 编辑模式：删除旧设备，添加新配置
            self.device_manager.remove_device(self.original_config.device_id)
            result = self.device_manager.add_device(config)
        else:
            # 添加模式
            result = self.device_manager.add_device(config)
        
        if result.success:
            self.accept()
        else:
            QMessageBox.critical(self, "操作失败", result.error)
