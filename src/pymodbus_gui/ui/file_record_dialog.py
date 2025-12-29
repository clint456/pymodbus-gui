"""
文件记录配置对话框
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QCheckBox, QPushButton,
    QLabel, QGroupBox, QFileDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

from pymodbus_gui.core.slave_server import FileRecordConfig


class FileRecordDialog(QDialog):
    """文件记录配置对话框"""
    
    # 信号
    file_configured = pyqtSignal(object)  # FileRecordConfig
    
    def __init__(self, file_config: Optional[FileRecordConfig] = None, parent=None):
        """
        初始化对话框
        
        Args:
            file_config: 文件配置（编辑模式）
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.file_config = file_config
        self.edit_mode = file_config is not None
        
        self.init_ui()
        
        if self.edit_mode:
            self.load_config()
    
    def init_ui(self):
        """初始化用户界面"""
        title = "编辑文件记录" if self.edit_mode else "添加文件记录"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        main_layout = QVBoxLayout()
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.file_number_spin = QSpinBox()
        self.file_number_spin.setRange(0, 65535)
        self.file_number_spin.setValue(1)
        basic_layout.addRow("文件号:", self.file_number_spin)
        
        file_path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择文件路径...")
        file_path_layout.addWidget(self.file_path_edit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_file)
        file_path_layout.addWidget(self.browse_btn)
        
        basic_layout.addRow("文件路径:", file_path_layout)
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 1000000)
        self.max_size_spin.setValue(65535)
        self.max_size_spin.setSuffix(" 字节")
        basic_layout.addRow("最大大小:", self.max_size_spin)
        
        # 固定长度配置
        self.file_length_spin = QSpinBox()
        self.file_length_spin.setRange(0, 65535)
        self.file_length_spin.setValue(0)
        self.file_length_spin.setSuffix(" 字节")
        self.file_length_spin.setSpecialValueText("未设置（使用长度寄存器）")
        basic_layout.addRow("固定长度:", self.file_length_spin)
        
        self.read_only_check = QCheckBox("只读")
        basic_layout.addRow("", self.read_only_check)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("文件描述...")
        basic_layout.addRow("描述:", self.description_edit)
        
        basic_group.setLayout(basic_layout)
        main_layout.addWidget(basic_group)
        
        # 触发配置
        trigger_group = QGroupBox("触发配置（可选）")
        trigger_layout = QFormLayout()
        
        self.trigger_enabled_check = QCheckBox("启用触发")
        self.trigger_enabled_check.stateChanged.connect(self.on_trigger_enabled_changed)
        trigger_layout.addRow("", self.trigger_enabled_check)
        
        self.trigger_function_combo = QComboBox()
        self.trigger_function_combo.addItem("06 - 写单个寄存器", 6)
        self.trigger_function_combo.addItem("03 - 读保持寄存器", 3)
        self.trigger_function_combo.setEnabled(False)
        trigger_layout.addRow("触发功能码:", self.trigger_function_combo)
        
        self.trigger_address_spin = QSpinBox()
        self.trigger_address_spin.setRange(0, 65535)
        self.trigger_address_spin.setEnabled(False)
        trigger_layout.addRow("触发地址:", self.trigger_address_spin)
        
        trigger_group.setLayout(trigger_layout)
        main_layout.addWidget(trigger_group)
        
        # 长度寄存器配置
        length_group = QGroupBox("长度寄存器配置（可选）")
        length_layout = QFormLayout()
        
        self.length_enabled_check = QCheckBox("从寄存器读取长度")
        self.length_enabled_check.stateChanged.connect(self.on_length_enabled_changed)
        length_layout.addRow("", self.length_enabled_check)
        
        self.length_function_combo = QComboBox()
        self.length_function_combo.addItem("03 - 读保持寄存器", 3)
        self.length_function_combo.addItem("04 - 读输入寄存器", 4)
        self.length_function_combo.setEnabled(False)
        length_layout.addRow("长度功能码:", self.length_function_combo)
        
        self.length_address_spin = QSpinBox()
        self.length_address_spin.setRange(0, 65535)
        self.length_address_spin.setEnabled(False)
        length_layout.addRow("长度地址:", self.length_address_spin)
        
        self.length_quantity_spin = QSpinBox()
        self.length_quantity_spin.setRange(1, 4)
        self.length_quantity_spin.setValue(2)
        self.length_quantity_spin.setEnabled(False)
        length_layout.addRow("寄存器数量:", self.length_quantity_spin)
        
        length_group.setLayout(length_layout)
        main_layout.addWidget(length_group)
        
        # 说明
        info_label = QLabel(
            "提示：\n"
            "• 文件号用于识别文件（功能码20/21）\n"
            "• 触发配置：在读取文件前先写入触发寄存器\n"
            "• 长度寄存器：从指定寄存器动态读取文件长度"
        )
        info_label.setStyleSheet("QLabel { color: #666; padding: 10px; background: #f0f0f0; border-radius: 3px; }")
        main_layout.addWidget(info_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept_config)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def browse_file(self):
        """浏览选择文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择文件",
            "",
            "所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def on_trigger_enabled_changed(self, state):
        """触发启用状态改变"""
        enabled = state == Qt.CheckState.Checked.value
        self.trigger_function_combo.setEnabled(enabled)
        self.trigger_address_spin.setEnabled(enabled)
    
    def on_length_enabled_changed(self, state):
        """长度启用状态改变"""
        enabled = state == Qt.CheckState.Checked.value
        self.length_function_combo.setEnabled(enabled)
        self.length_address_spin.setEnabled(enabled)
        self.length_quantity_spin.setEnabled(enabled)
    
    def load_config(self):
        """加载配置"""
        if not self.file_config:
            return
        
        self.file_number_spin.setValue(self.file_config.file_number)
        self.file_path_edit.setText(self.file_config.file_path)
        self.max_size_spin.setValue(self.file_config.max_size)
        
        # 固定长度配置
        if self.file_config.file_length is not None:
            self.file_length_spin.setValue(self.file_config.file_length)
        else:
            self.file_length_spin.setValue(0)
        
        self.read_only_check.setChecked(self.file_config.read_only)
        self.description_edit.setText(self.file_config.description)
        
        # 触发配置
        self.trigger_enabled_check.setChecked(self.file_config.trigger_enabled)
        
        # 查找并设置功能码
        for i in range(self.trigger_function_combo.count()):
            if self.trigger_function_combo.itemData(i) == self.file_config.trigger_function_code:
                self.trigger_function_combo.setCurrentIndex(i)
                break
        
        self.trigger_address_spin.setValue(self.file_config.trigger_address)
        
        # 长度寄存器配置
        self.length_enabled_check.setChecked(self.file_config.length_register_enabled)
        
        for i in range(self.length_function_combo.count()):
            if self.length_function_combo.itemData(i) == self.file_config.length_function_code:
                self.length_function_combo.setCurrentIndex(i)
                break
        
        self.length_address_spin.setValue(self.file_config.length_address)
        self.length_quantity_spin.setValue(self.file_config.length_quantity)
    
    def accept_config(self):
        """确认配置"""
        # 验证
        file_number = self.file_number_spin.value()
        file_path = self.file_path_edit.text().strip()
        
        if not file_path:
            QMessageBox.warning(self, "验证失败", "请选择文件路径")
            return
        
        # 创建配置
        file_length = self.file_length_spin.value()
        file_config = FileRecordConfig(
            file_number=file_number,
            file_path=file_path,
            max_size=self.max_size_spin.value(),
            file_length=file_length if file_length > 0 else None,  # 0表示未设置
            trigger_enabled=self.trigger_enabled_check.isChecked(),
            trigger_function_code=self.trigger_function_combo.currentData(),
            trigger_address=self.trigger_address_spin.value(),
            length_register_enabled=self.length_enabled_check.isChecked(),
            length_function_code=self.length_function_combo.currentData(),
            length_address=self.length_address_spin.value(),
            length_quantity=self.length_quantity_spin.value(),
            read_only=self.read_only_check.isChecked(),
            description=self.description_edit.text().strip()
        )
        
        # 发送信号
        self.file_configured.emit(file_config)
        
        self.accept()
