"""
测试日志打印功能
"""
import sys
import time
from PyQt6.QtWidgets import QApplication
from src.pymodbus_gui.core.slave_server import SlaveConfig, SlaveConnectionType, RegisterPoint
from src.pymodbus_gui.ui.main_window import MainWindow


def test_logging():
    """测试日志功能"""
    print("创建应用程序...")
    app = QApplication(sys.argv)
    
    # 创建主窗口
    print("创建主窗口...")
    window = MainWindow()
    window.show()
    
    # 切换到Slave标签
    window.tab_widget.setCurrentIndex(1)
    
    # 模拟添加一个Slave
    print("添加测试Slave...")
    config = SlaveConfig(
        slave_id="test_slave_1",
        name="测试日志Slave",
        connection_type=SlaveConnectionType.TCP,
        device_address=1,
        host="0.0.0.0",
        tcp_port=5020,
        register_points=[
            RegisterPoint(
                address=0,
                name="测试点位1",
                register_type="holding_register",
                value=100,
                description="用于测试日志的点位"
            ),
            RegisterPoint(
                address=1,
                name="测试点位2",
                register_type="holding_register",
                value=200,
                description="另一个测试点位"
            )
        ]
    )
    
    # 添加slave（这会触发初始化日志）
    result = window.slave_manager.add_slave(config)
    print(f"添加Slave结果: {result.success}, {result.data if result.success else result.error}")
    
    # 获取slave对象
    slave = window.slave_manager.get_slave("test_slave_1")
    
    if slave:
        # 启动slave（这会触发启动日志）
        print("\n启动Slave服务器...")
        result = window.slave_manager.start_slave("test_slave_1")
        print(f"启动结果: {result.success}, {result.data if result.success else result.error}")
        
        # 等待服务器启动
        time.sleep(2)
        
        # 执行一些读写操作（这会触发操作日志）
        print("\n执行读写操作...")
        
        # 读取寄存器
        result = slave.read_register("holding_register", 0)
        print(f"读取地址0结果: {result.data}")
        
        result = slave.read_register("holding_register", 1)
        print(f"读取地址1结果: {result.data}")
        
        # 写入寄存器
        result = slave.write_register("holding_register", 0, 888)
        print(f"写入地址0结果: {result.success}")
        
        result = slave.write_register("holding_register", 1, 999)
        print(f"写入地址1结果: {result.success}")
        
        # 再次读取验证
        result = slave.read_register("holding_register", 0)
        print(f"读取地址0新值: {result.data}")
        
        result = slave.read_register("holding_register", 1)
        print(f"读取地址1新值: {result.data}")
        
        # 等待一会儿让用户查看日志窗口
        print("\n请查看GUI窗口中的日志输出...")
        print("窗口将在10秒后自动关闭，或手动关闭窗口...")
        
        # 使用定时器自动停止和关闭
        from PyQt6.QtCore import QTimer
        def auto_cleanup():
            print("\n停止Slave服务器...")
            window.slave_manager.stop_slave("test_slave_1")
            time.sleep(1)
            print("测试完成，关闭窗口...")
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(auto_cleanup)
        timer.setSingleShot(True)
        timer.start(10000)  # 10秒后执行
    
    # 启动应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    test_logging()
