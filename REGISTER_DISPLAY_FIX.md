# 寄存器显示位置修复说明

## 问题描述

之前用户导入Excel点表后，发现软件显示的寄存器值与导入的点表位置不一致，相差1个位置。例如：
- 点表中地址1的值应该是220
- 但软件界面显示的是地址2的值（55）

虽然使用Modbus客户端读取和写入的值是正确的，但界面显示顺序错乱。

## 问题原因

在 `slave_register_widget.py` 的 `get_points_by_type()` 方法中，获取点位列表时没有按地址排序。

**原代码：**
```python
def get_points_by_type(self, register_type: str) -> list[RegisterPoint]:
    """获取指定类型的点位列表"""
    return [p for p in self.slave.config.register_points if p.register_type == register_type]
```

这导致点位的显示顺序取决于：
1. Excel文件中的行顺序
2. 导入时的解析顺序

如果Excel文件中点位不是按地址从小到大排列的，显示时就会出现错位。

## 修复方案

在 `get_points_by_type()` 方法中添加按地址排序：

**修复后代码：**
```python
def get_points_by_type(self, register_type: str) -> list[RegisterPoint]:
    """获取指定类型的点位列表（按地址排序）"""
    points = [p for p in self.slave.config.register_points if p.register_type == register_type]
    # 按地址排序，确保显示顺序与地址顺序一致
    return sorted(points, key=lambda p: p.address)
```

## 修复效果

修复后：
1. ✅ 表格中的点位按地址从小到大排序显示
2. ✅ 地址0的点位显示在第1行，地址1的点位显示在第2行，以此类推
3. ✅ 无论Excel文件中点位的原始顺序如何，界面都会按地址顺序正确显示
4. ✅ Modbus客户端读写的值与界面显示的值完全对应

## 测试方法

1. 创建一个Excel点表，故意将点位地址打乱顺序：
   - 第1行：地址5
   - 第2行：地址1
   - 第3行：地址3
   - 第4行：地址0

2. 导入该点表到Slave

3. 启动Slave服务器

4. 查看界面显示，应该按地址排序：
   - 第1行：地址0
   - 第2行：地址1
   - 第3行：地址3
   - 第4行：地址5

5. 使用Modbus客户端读取/写入各个地址，验证界面显示的值正确对应

## 相关文件

- `src/pymodbus_gui/ui/slave_register_widget.py` - 寄存器界面显示组件

## 注意事项

此修复仅影响界面显示顺序，不影响：
- Modbus协议层的地址映射（依然正确）
- 实际的寄存器值存储（依然正确）
- Modbus客户端的读写操作（依然正确）

只是让界面显示更加直观，按地址顺序展示点位。
