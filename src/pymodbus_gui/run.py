"""
Modbus 设备管理工具 v2.0
主程序入口

功能特性:
- 支持 Modbus RTU 和 TCP 协议
- 支持功能码 1-21 的完整操作
- 支持多设备并发连接
- Excel 配置导入/导出
- 完整的中文界面
- 操作日志记录
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from pymodbus_gui.ui.main_window import MainWindow


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("Modbus 设备管理工具")
    app.setOrganizationName("ModbusGUI")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用程序事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
