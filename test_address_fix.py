"""
测试地址偏移修复
验证导入的地址与值是否对应正确
"""
import sys
sys.path.insert(0, 'src')

from pymodbus_gui.core.slave_server import ModbusSlave, SlaveConfig, SlaveConnectionType, RegisterPoint

# 创建测试点表 - 从地址0开始
test_points = [
    RegisterPoint(
        address=0,
        name='点位0',
        register_type='holding_register',
        value=100,
        description='地址0的点位，值应该是100',
    ),
    RegisterPoint(
        address=1,
        name='点位1',
        register_type='holding_register',
        value=200,
        description='地址1的点位，值应该是200',
    ),
    RegisterPoint(
        address=2,
        name='点位2',
        register_type='holding_register',
        value=300,
        description='地址2的点位，值应该是300',
    ),
]

# 创建 Slave 配置
config = SlaveConfig(
    slave_id='test_slave',
    name='地址测试Slave',
    connection_type=SlaveConnectionType.TCP,
    device_address=1,
    host='0.0.0.0',
    tcp_port=5020,
    register_points=test_points
)

# 创建 Slave 实例
slave = ModbusSlave(config)

print("=" * 60)
print("测试寄存器地址与值的对应关系")
print("=" * 60)

# 测试读取每个点位的值
for point in test_points:
    result = slave.read_register('holding_register', point.address)
    if result.success:
        print(f"✓ 地址 {point.address} ({point.name}): 期望值={point.value}, 实际值={result.data}", end="")
        if result.data == point.value:
            print(" - 正确 ✓")
        else:
            print(f" - 错误 ✗ (值不匹配!)")
    else:
        print(f"✗ 地址 {point.address} ({point.name}): 读取失败 - {result.error}")

print("\n" + "=" * 60)
print("测试写入操作")
print("=" * 60)

# 测试写入新值
test_address = 1
new_value = 999
print(f"\n向地址 {test_address} 写入新值 {new_value}...")
write_result = slave.write_register('holding_register', test_address, new_value)
if write_result.success:
    print(f"✓ 写入成功")
    
    # 验证写入的值
    read_result = slave.read_register('holding_register', test_address)
    if read_result.success:
        print(f"✓ 读回验证: 地址 {test_address} 的值为 {read_result.data}", end="")
        if read_result.data == new_value:
            print(" - 写入验证成功 ✓")
        else:
            print(f" - 写入验证失败 ✗ (期望 {new_value}, 实际 {read_result.data})")
    else:
        print(f"✗ 读回验证失败: {read_result.error}")
else:
    print(f"✗ 写入失败: {write_result.error}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
