"""
测试点表导入和寄存器初始化
"""
import sys
sys.path.insert(0, 'src')

from pymodbus_gui.core.slave_server import SlaveConfig, SlaveConnectionType, RegisterPoint
from pymodbus_gui.core.register_manager import RegisterManager

# 创建测试点表
test_points = [
    RegisterPoint(
        address=0,
        name='运行状态',
        register_type='coil',
        value=1,
        description='设备运行状态',
    ),
    RegisterPoint(
        address=0,
        name='温度设定',
        register_type='holding_register',
        value=250,
        description='温度设定值',
        unit='0.1°C',
        min_value=0,
        max_value=1000
    ),
    RegisterPoint(
        address=1,
        name='当前温度',
        register_type='input_register',
        value=235,
        description='当前实际温度',
        unit='0.1°C',
        min_value=0,
        max_value=1000,
        read_only=True
    ),
]

# 创建 Slave 配置
config = SlaveConfig(
    slave_id='test_slave',
    name='测试Slave',
    connection_type=SlaveConnectionType.TCP,
    device_address=1,
    host='0.0.0.0',
    tcp_port=5020,
    register_points=test_points
)

# 导出点表进行验证
register_manager = RegisterManager()
result = register_manager.export_register_points(test_points, 'test_points.xlsx')
print(f"导出结果: {result.success}, {result.data or result.error}")

# 导入点表进行验证
result = register_manager.import_register_points('test_points.xlsx')
if result.success:
    print(f"导入成功，共 {len(result.data)} 个点位：")
    for point in result.data:
        print(f"  - {point.name} ({point.register_type}): 地址={point.address}, 值={point.value}")
else:
    print(f"导入失败: {result.error}")
