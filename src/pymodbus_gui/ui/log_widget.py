"""
操作日志组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat

from datetime import datetime


class LogWidget(QWidget):
    """日志组件"""
    
    def __init__(self, parent=None):
        """初始化日志组件"""
        super().__init__(parent)
        self.parent_window = parent
        self.log_data = []  # 存储日志数据用于导出
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("导出日志")
        self.export_btn.clicked.connect(self.export_logs)
        toolbar_layout.addWidget(self.export_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.log_text)
    
    def add_log(self, message: str, level: str = "INFO"):
        """
        添加日志
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO/WARNING/ERROR/SUCCESS)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 设置颜色
        color_map = {
            "INFO": QColor(156, 220, 254),      # 蓝色
            "WARNING": QColor(250, 153, 56),    # 橙色
            "ERROR": QColor(244, 71, 71),       # 红色
            "SUCCESS": QColor(94, 196, 108)     # 绿色
        }
        
        color = color_map.get(level, QColor(212, 212, 212))
        
        # 格式化消息
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # 添加到文本框
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        format = QTextCharFormat()
        format.setForeground(color)
        
        cursor.insertText(formatted_message + "\n", format)
        
        # 自动滚动到底部
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
        
        # 存储日志数据
        self.log_data.append({
            "时间": timestamp,
            "级别": level,
            "消息": message
        })
    
    def clear_logs(self):
        """清空日志"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有日志吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_text.clear()
            self.log_data.clear()
    
    def export_logs(self):
        """导出日志到文件"""
        if not self.log_data:
            QMessageBox.warning(self, "提示", "没有可导出的日志")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"操作日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel 文件 (*.xlsx);;文本文件 (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.xlsx'):
                # 导出为 Excel
                from pymodbus_gui.core.excel_manager import ExcelManager
                excel_mgr = ExcelManager()
                result = excel_mgr.export_operation_log(self.log_data, file_path)
                
                if result.success:
                    QMessageBox.information(self, "导出成功", result.data)
                else:
                    QMessageBox.critical(self, "导出失败", result.error)
            else:
                # 导出为文本文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    for log in self.log_data:
                        f.write(f"[{log['时间']}] [{log['级别']}] {log['消息']}\n")
                
                QMessageBox.information(self, "导出成功", f"成功导出 {len(self.log_data)} 条日志")
        
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出异常: {str(e)}")
