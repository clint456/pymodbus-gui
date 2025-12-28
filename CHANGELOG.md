# Modbus Poll & Slave 管理工具 v2.0

## 更新说明 (2025-12-26)

### 新增功能

#### 1. Modbus Slave 服务器功能
- 支持创建和管理多个 Modbus Slave 服务器
- 支持 RTU 和 TCP 协议
- 支持功能码 1-21 的完整操作
- 支持多 Slave 并发运行

#### 2. 寄存器点表管理
- 通过 Excel 导入/导出寄存器点表配置
- 支持四种寄存器类型：
  - 线圈 (Coil) - 功能码 01/05/15
  - 离散输入 (Discrete Input) - 功能码 02
  - 保持寄存器 (Holding Register) - 功能码 03/06/16
  - 输入寄存器 (Input Register) - 功能码 04
- 点表配置包含：地址、名称、描述、单位、范围、只读属性等

#### 3. 寄存器实时监控
- 实时显示所有寄存器的当前值
- 支持手动写入寄存器值（非只读）
- 自动刷新功能
- 按寄存器类型分标签页显示

#### 4. 用户界面改进
- 新增"Slave 服务器管理"选项卡
- 左侧列表显示所有 Slave 服务器状态
- 右侧详情面板显示选中 Slave 的寄存器监控界面
- 菜单栏分离 Poll 设备和 Slave 服务器功能

### 文件结构

```
src/pymodbus_gui/
├── core/
│   ├── slave_server.py         # Slave 服务器核心模块
│   ├── register_manager.py     # 寄存器点表管理
│   ├── device_manager.py        # Poll 设备管理（原有）
│   └── excel_manager.py         # Excel 导入导出（原有）
├── ui/
│   ├── add_slave_dialog.py      # 添加 Slave 对话框
│   ├── slave_list_widget.py     # Slave 列表界面
│   ├── slave_register_widget.py # Slave 寄存器监控界面
│   ├── main_window.py           # 主窗口（已更新）
│   └── ...                      # 其他界面（原有）
```

### 主要模块说明

#### slave_server.py
- `RegisterPoint`: 寄存器点位配置类
- `SlaveConfig`: Slave 配置类
- `ModbusSlave`: 单个 Modbus Slave 服务器
- `SlaveManager`: Slave 管理器

#### register_manager.py
- `RegisterManager`: 寄存器点表管理器
- 提供 Excel 导入/导出功能
- 点表验证功能

#### add_slave_dialog.py
- Slave 配置对话框
- 支持 RTU/TCP 参数配置
- 点表导入功能
- 模板创建功能

#### slave_register_widget.py
- 寄存器实时监控界面
- 支持启动/停止 Slave 服务器
- 支持手动写入寄存器
- 自动刷新功能

#### slave_list_widget.py
- Slave 列表管理界面
- 显示所有 Slave 状态
- 支持添加/删除/启动/停止操作

### 使用说明

#### 创建 Slave 服务器

1. 点击菜单"Slave服务器" -> "添加 Slave 服务器"
2. 填写基本信息：Slave ID、名称、连接类型、从站地址
3. 根据连接类型配置：
   - TCP: 监听地址和端口
   - RTU: 串口端口、波特率等
4. 配置寄存器数量
5. （可选）导入点表或创建模板
6. 点击"确定"

#### 导入点表

1. 先创建点表模板：菜单"Slave服务器" -> "创建点表模板"
2. 在 Excel 中编辑点表配置
3. 在添加 Slave 对话框中点击"导入点表"
4. 选择配置好的 Excel 文件

#### 监控和编辑寄存器

1. 在"Slave 服务器管理"选项卡左侧列表选择 Slave
2. 右侧显示寄存器监控界面
3. 点击"启动服务器"启动 Slave
4. 查看各类寄存器的当前值
5. 点击"写入"按钮可修改寄存器值（非只读）
6. 启用"自动刷新"实时监控

### Excel 点表格式

点表 Excel 文件包含以下列：

| 列名 | 说明 | 示例 |
|------|------|------|
| 地址 | Modbus 地址 | 0, 1, 2... |
| 点位名称 | 点位描述性名称 | 温度设定 |
| 寄存器类型 | 线圈/离散输入/保持寄存器/输入寄存器 | 保持寄存器 |
| 初始值 | 初始值 | 250 |
| 描述 | 详细描述 | 温度设定值 |
| 单位 | 单位 | 0.1°C |
| 最小值 | 最小值（可选） | 0 |
| 最大值 | 最大值（可选） | 1000 |
| 只读 | 是否只读 | 否 |

### 注意事项

1. Slave 服务器运行时会占用配置的端口或串口
2. 同一端口或串口只能被一个 Slave 使用
3. 点表中同一寄存器类型的地址不能重复
4. 只读寄存器只能通过界面修改，不能通过 Modbus 写入
5. 退出程序时会自动停止所有 Slave 服务器

### 技术细节

- 使用 pymodbus 库实现 Modbus 协议
- Slave 服务器在独立线程中运行
- 使用 ModbusServerContext 管理寄存器数据
- 支持并发多 Slave 运行
- 线程安全的寄存器读写操作

### 后续计划

- [ ] 添加 Slave 服务器日志记录
- [ ] 支持更多功能码（如诊断、文件记录等）
- [ ] 添加寄存器历史数据记录
- [ ] 支持脚本化的寄存器值变化
- [ ] 添加 Modbus 通信数据包监控
