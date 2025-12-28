# 日志功能增强 - 更新说明

## 修改内容

### 1. slave_server.py 修改

在 `ModbusSlave` 类中添加了完整的日志回调支持：

#### 1.1 添加日志回调属性
```python
self.on_log: Optional[Callable[[str, str], None]] = None  # 日志回调 (message, level)
```

#### 1.2 添加日志记录方法
```python
def _log(self, message: str, level: str = "INFO"):
    """记录日志到日志窗口"""
    if self.on_log:
        try:
            self.on_log(f"[{self.config.name}] {message}", level)
        except Exception as e:
            logging.error(f"日志回调失败: {e}")
```

#### 1.3 在关键操作中添加日志

**数据存储初始化：**
- 记录数据块创建信息
- 记录点位初始化成功/失败
- 统计并显示初始化的点位数量

**服务器启动：**
- RTU 服务器：记录端口、波特率、从站地址
- TCP 服务器：记录主机、端口、从站地址
- 记录启动成功/失败状态

**服务器停止：**
- 记录停止操作和结果

**寄存器读取：**
- 记录每次读取操作的寄存器类型、地址和读取的值
- 记录读取失败的错误信息

**寄存器写入：**
- 记录每次写入操作的寄存器类型、地址和写入的值
- 记录只读检查警告
- 记录值范围验证警告
- 记录写入成功/失败状态

### 2. SlaveManager 类修改

#### 2.1 添加日志回调属性
```python
self.on_log: Optional[Callable[[str, str], None]] = None  # 日志回调
```

#### 2.2 在添加Slave时设置日志回调
```python
def add_slave(self, config: SlaveConfig) -> OperationResult:
    slave = ModbusSlave(config)
    # 设置日志回调
    if self.on_log:
        slave.on_log = self.on_log
    self.slaves[config.slave_id] = slave
```

### 3. main_window.py 修改

在 `init_ui` 方法中连接日志回调：
```python
# 设置slave_manager的日志回调
self.slave_manager.on_log = self.log_slave_message
```

## 日志级别

系统支持以下日志级别，每个级别有不同的颜色显示：

- **INFO** (蓝色)：一般信息，如读取操作、服务器状态
- **SUCCESS** (绿色)：成功操作，如启动成功、写入成功
- **WARNING** (橙色)：警告信息，如只读警告、值范围警告
- **ERROR** (红色)：错误信息，如启动失败、读写失败

## 日志格式

所有日志消息格式为：
```
[时间戳] [级别] [Slave名称] 消息内容
```

例如：
```
[2025-12-29 10:30:15] [SUCCESS] [测试Slave] 写入 holding_register 地址 0 = 888
[2025-12-29 10:30:16] [INFO] [测试Slave] 读取 holding_register 地址 0 = 888
[2025-12-29 10:30:17] [WARNING] [测试Slave] 地址 5 为只读
```

## 测试方法

运行测试脚本查看日志功能：
```bash
python test_logging.py
```

测试脚本会：
1. 创建主窗口
2. 添加一个测试Slave（触发初始化日志）
3. 启动Slave服务器（触发启动日志）
4. 执行多次读写操作（触发操作日志）
5. 10秒后自动停止并关闭

## 使用效果

现在在GUI的"Slave 服务器"标签页底部的日志窗口中，你可以实时看到：
- Slave服务器的启动/停止信息
- 数据存储初始化过程
- 点位初始化结果
- 每次寄存器读写操作的详细信息
- 各种警告和错误信息

所有日志都会自动带上时间戳和Slave名称，便于追踪和调试。
