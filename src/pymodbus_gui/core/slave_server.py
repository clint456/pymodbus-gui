"""
Modbus Slave 服务器
支持 RTU 和 TCP，功能码 1-21，多设备并发
"""
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging
import socket
from pymodbus.server import StartAsyncSerialServer, StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext
)
from pymodbus.device import ModbusDeviceIdentification
import asyncio


class SlaveConnectionType(Enum):
    """Slave 连接类型枚举"""
    RTU = "RTU"
    TCP = "TCP"


@dataclass
class RegisterPoint:
    """寄存器点位配置"""
    address: int  # 地址
    name: str  # 点位名称
    register_type: str  # 寄存器类型: coil, discrete_input, holding_register, input_register
    value: Any = 0  # 初始值
    description: str = ""  # 描述
    unit: str = ""  # 单位
    min_value: Optional[float] = None  # 最小值
    max_value: Optional[float] = None  # 最大值
    read_only: bool = False  # 只读
    
    def validate_value(self, value: Any) -> bool:
        """验证值是否在有效范围内"""
        if self.register_type in ['coil', 'discrete_input']:
            return isinstance(value, (bool, int)) and value in [0, 1, True, False]
        
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True


@dataclass
class SlaveConfig:
    """Slave 配置数据类"""
    slave_id: str  # Slave 唯一标识
    name: str  # Slave 名称
    connection_type: SlaveConnectionType  # 连接类型
    device_address: int = 1  # 设备地址（从站地址）
    
    # RTU 配置
    port: Optional[str] = None  # 串口端口
    baudrate: int = 9600  # 波特率
    bytesize: int = 8  # 数据位
    parity: str = 'N'  # 校验位 N/E/O
    stopbits: int = 1  # 停止位
    
    # TCP 配置
    host: str = "0.0.0.0"  # 监听地址
    tcp_port: int = 502  # TCP端口
    
    # 寄存器配置
    coil_count: int = 1000  # 线圈数量
    discrete_input_count: int = 1000  # 离散输入数量
    holding_register_count: int = 1000  # 保持寄存器数量
    input_register_count: int = 1000  # 输入寄存器数量
    
    # 点位配置
    register_points: List[RegisterPoint] = field(default_factory=list)


@dataclass
class OperationResult:
    """操作结果数据类"""
    success: bool  # 操作是否成功
    data: Any = None  # 返回数据
    error: Optional[str] = None  # 错误信息


class ModbusSlave:
    """单个 Modbus Slave 服务器"""
    
    def __init__(self, config: SlaveConfig):
        """
        初始化 Slave
        
        Args:
            config: Slave 配置
        """
        self.config = config
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()
        self.error_message: Optional[str] = None
        
        # asyncio 相关
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server: Optional[Any] = None  # 保存服务器实例
        
        # 数据存储
        self.datastore_context: Optional[ModbusServerContext] = None
        self.slave_context: Optional[ModbusSlaveContext] = None
        
        # 回调函数
        self.on_value_change: Optional[Callable] = None
        self.on_log: Optional[Callable[[str, str], None]] = None  # 日志回调 (message, level)
        
        # 初始化数据存储
        self._init_datastore()
    
    def _init_datastore(self):
        """初始化数据存储"""
        # 创建数据块
        coils = ModbusSequentialDataBlock(0, [0] * self.config.coil_count)
        discrete_inputs = ModbusSequentialDataBlock(0, [0] * self.config.discrete_input_count)
        holding_registers = ModbusSequentialDataBlock(0, [0] * self.config.holding_register_count)
        input_registers = ModbusSequentialDataBlock(0, [0] * self.config.input_register_count)
        
        self._log(f"初始化数据存储 - Coils:{self.config.coil_count}, DI:{self.config.discrete_input_count}, HR:{self.config.holding_register_count}, IR:{self.config.input_register_count}", "INFO")
        
        # 创建从站上下文
        self.slave_context = ModbusSlaveContext(
            di=discrete_inputs,  # 离散输入
            co=coils,  # 线圈
            hr=holding_registers,  # 保持寄存器
            ir=input_registers  # 输入寄存器
        )
        
        # 根据点位配置初始化值
        # 注意：SlaveContext的getValues/setValues使用Modbus协议地址，
        # 但内部会+1转换为DataBlock索引
        initialized_count = 0
        for point in self.config.register_points:
            try:
                value = int(point.value)
                # 通过SlaveContext设置值，直接使用Modbus协议地址
                if point.register_type == 'coil':
                    self.slave_context.setValues(1, point.address, [value])
                elif point.register_type == 'discrete_input':
                    self.slave_context.setValues(2, point.address, [value])
                elif point.register_type == 'holding_register':
                    self.slave_context.setValues(3, point.address, [value])
                elif point.register_type == 'input_register':
                    self.slave_context.setValues(4, point.address, [value])
                logging.info(f"初始化点位 {point.name} (地址{point.address}) = {value}")
                initialized_count += 1
            except Exception as e:
                logging.warning(f"初始化点位 {point.name} 失败: {e}")
                self._log(f"初始化点位 {point.name} 失败: {e}", "WARNING")
        
        if initialized_count > 0:
            self._log(f"成功初始化 {initialized_count} 个寄存器点位", "SUCCESS")
        
        # 创建服务器上下文（支持单个从站地址）
        self.datastore_context = ModbusServerContext(
            slaves={self.config.device_address: self.slave_context},
            single=False
        )
    
    def start(self) -> OperationResult:
        """
        启动 Slave 服务器
        
        Returns:
            操作结果
        """
        with self.lock:
            if self.running:
                return OperationResult(False, error="服务器已在运行")
            
            try:
                # 创建设备标识
                identity = ModbusDeviceIdentification()
                identity.VendorName = 'Pymodbus GUI'
                identity.ProductCode = 'PM'
                identity.VendorUrl = 'https://github.com/pymodbus-dev/pymodbus/'
                identity.ProductName = self.config.name
                identity.ModelName = self.config.name
                identity.MajorMinorRevision = '2.0.0'
                
                # 根据连接类型启动服务器
                if self.config.connection_type == SlaveConnectionType.RTU:
                    if not self.config.port:
                        return OperationResult(False, error="RTU 模式需要指定串口端口")
                    
                    # 在单独的线程中启动 RTU 服务器
                    self.server_thread = threading.Thread(
                        target=self._run_rtu_server,
                        args=(identity,),
                        daemon=True
                    )
                    self.server_thread.start()
                
                elif self.config.connection_type == SlaveConnectionType.TCP:
                    # 在单独的线程中启动 TCP 服务器
                    self.server_thread = threading.Thread(
                        target=self._run_tcp_server,
                        args=(identity,),
                        daemon=True
                    )
                    self.server_thread.start()
                
                self.running = True
                self.error_message = None
                success_msg = f"Slave {self.config.name} 启动成功"
                self._log(success_msg, "SUCCESS")
                return OperationResult(True, data=success_msg)
                
            except Exception as e:
                self.error_message = str(e)
                self.running = False
                error_msg = f"启动失败: {str(e)}"
                self._log(error_msg, "ERROR")
                return OperationResult(False, error=error_msg)
    
    def _run_rtu_server(self, identity):
        """在线程中运行 RTU 服务器"""
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 创建并调度服务器启动任务
            self.loop.create_task(self._start_rtu_server(identity))
            
            # 运行事件循环直到被停止
            self.loop.run_forever()
            logging.info("RTU 服务器事件循环已退出")
            
        except Exception as e:
            self.error_message = f"RTU 服务器异常: {str(e)}"
            logging.error(self.error_message)
        finally:
            self.running = False
            # 清理任务并关闭循环
            try:
                if self.loop and not self.loop.is_closed():
                    # 取消所有待处理任务
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    # 等待任务取消完成
                    if pending:
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    self.loop.close()
                    logging.info("RTU 服务器事件循环已关闭")
            except Exception as e:
                logging.error(f"清理RTU任务失败: {e}")
    
    async def _start_rtu_server(self, identity):
        """启动 RTU 服务器的异步方法"""
        try:
            self.server = await StartAsyncSerialServer(
                context=self.datastore_context,
                identity=identity,
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.bytesize,
                parity=self.config.parity,
                stopbits=self.config.stopbits
            )
            info_msg = f"RTU 服务器已启动: {self.config.port} (波特率:{self.config.baudrate}, 从站地址:{self.config.device_address})"
            logging.info(info_msg)
            self._log(info_msg, "INFO")
            # 服务器运行直到被关闭
            await self.server.serve_forever()
        except asyncio.CancelledError:
            logging.info("RTU 服务器正常停止")
            self._log("RTU 服务器正常停止", "INFO")
            # 不重新抛出，让线程正常退出
        except Exception as e:
            error_msg = f"RTU 服务器错误: {e}"
            logging.error(error_msg)
            self._log(error_msg, "ERROR")
            raise
    
    def _run_tcp_server(self, identity):
        """在线程中运行 TCP 服务器"""
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 创建并调度服务器启动任务
            self.loop.create_task(self._start_tcp_server(identity))
            
            # 运行事件循环直到被停止
            self.loop.run_forever()
            logging.info("TCP 服务器事件循环已退出")
            
        except Exception as e:
            self.error_message = f"TCP 服务器异常: {str(e)}"
            logging.error(self.error_message)
        finally:
            self.running = False
            # 清理任务并关闭循环
            try:
                if self.loop and not self.loop.is_closed():
                    # 取消所有待处理任务
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    # 等待任务取消完成
                    if pending:
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    self.loop.close()
                    logging.info("TCP 服务器事件循环已关闭")
            except Exception as e:
                logging.error(f"清理TCP任务失败: {e}")
    
    async def _start_tcp_server(self, identity):
        """启动 TCP 服务器的异步方法"""
        try:
            self.server = await StartAsyncTcpServer(
                context=self.datastore_context,
                identity=identity,
                address=(self.config.host, self.config.tcp_port)
            )
            info_msg = f"TCP 服务器已启动: {self.config.host}:{self.config.tcp_port} (从站地址:{self.config.device_address})"
            logging.info(info_msg)
            self._log(info_msg, "INFO")
            # 服务器运行直到被关闭
            await self.server.serve_forever()
        except asyncio.CancelledError:
            logging.info("TCP 服务器正常停止")
            self._log("TCP 服务器正常停止", "INFO")
            # 不重新抛出，让线程正常退出
        except Exception as e:
            error_msg = f"TCP 服务器错误: {e}"
            logging.error(error_msg)
            self._log(error_msg, "ERROR")
            raise
    
    def stop(self) -> OperationResult:
        """
        停止 Slave 服务器
        
        Returns:
            操作结果
        """
        with self.lock:
            if not self.running:
                return OperationResult(True, data="服务器未运行")
            
            try:
                logging.info("开始停止服务器...")
                self.running = False
                
                # 关闭服务器并停止事件循环
                if self.loop and not self.loop.is_closed():
                    try:
                        # 先调用shutdown关闭服务器
                        if self.server:
                            future = asyncio.run_coroutine_threadsafe(self._shutdown_server(), self.loop)
                            try:
                                future.result(timeout=2.0)
                                logging.info("服务器shutdown完成")
                            except Exception as e:
                                logging.warning(f"shutdown超时: {e}")
                        
                        # 停止事件循环
                        self.loop.call_soon_threadsafe(self.loop.stop)
                        logging.info("已调度事件循环停止")
                    except Exception as e:
                        logging.error(f"停止事件循环失败: {e}")
                
                # 等待线程结束
                if self.server_thread and self.server_thread.is_alive():
                    self.server_thread.join(timeout=3.0)
                    if self.server_thread.is_alive():
                        logging.warning("服务器线程未能在3秒内停止，但已调度停止")
                    else:
                        logging.info("服务器线程已停止")
                
                self.error_message = None
                success_msg = f"Slave {self.config.name} 已停止"
                self._log(success_msg, "INFO")
                return OperationResult(True, data=success_msg)
                
            except Exception as e:
                error_msg = f"停止服务器失败: {e}"
                logging.error(error_msg)
                self._log(error_msg, "ERROR")
                return OperationResult(False, error=f"停止失败: {str(e)}")
    
    async def _shutdown_server(self):
        """异步关闭服务器"""
        try:
            if self.server:
                await self.server.shutdown()
                logging.info("服务器已关闭")
        except Exception as e:
            logging.error(f"关闭服务器时出错: {e}")
    
    def read_register(self, register_type: str, address: int) -> OperationResult:
        """
        读取寄存器值
        
        Args:
            register_type: 寄存器类型 (coil, discrete_input, holding_register, input_register)
            address: 地址（Modbus协议地址）
            
        Returns:
            操作结果
        """
        try:
            if not self.slave_context:
                return OperationResult(False, error="数据存储未初始化")
            
            # 直接使用 Modbus 协议地址
            if register_type == 'coil':
                values = self.slave_context.getValues(1, address, count=1)
            elif register_type == 'discrete_input':
                values = self.slave_context.getValues(2, address, count=1)
            elif register_type == 'holding_register':
                values = self.slave_context.getValues(3, address, count=1)
            elif register_type == 'input_register':
                values = self.slave_context.getValues(4, address, count=1)
            else:
                return OperationResult(False, error=f"无效的寄存器类型: {register_type}")
            
            value = values[0] if values else 0
            self._log(f"读取 {register_type} 地址 {address} = {value}", "INFO")
            return OperationResult(True, data=value)
            
        except Exception as e:
            error_msg = f"读取失败: {str(e)}"
            self._log(error_msg, "ERROR")
            return OperationResult(False, error=error_msg)
    
    def write_register(self, register_type: str, address: int, value: Any) -> OperationResult:
        """
        写入寄存器值
        
        Args:
            register_type: 寄存器类型 (coil, discrete_input, holding_register, input_register)
            address: 地址（Modbus协议地址）
            value: 值
            
        Returns:
            操作结果
        """
        try:
            if not self.slave_context:
                return OperationResult(False, error="数据存储未初始化")
            
            # 检查点位配置
            point = self._find_point(register_type, address)
            if point:
                if point.read_only:
                    error_msg = f"地址 {address} 为只读"
                    self._log(error_msg, "WARNING")
                    return OperationResult(False, error=error_msg)
                if not point.validate_value(value):
                    error_msg = f"值 {value} 超出有效范围"
                    self._log(error_msg, "WARNING")
                    return OperationResult(False, error=error_msg)
            
            # 直接使用 Modbus 协议地址
            if register_type == 'coil':
                self.slave_context.setValues(1, address, [int(value)])
            elif register_type == 'discrete_input':
                self.slave_context.setValues(2, address, [int(value)])
            elif register_type == 'holding_register':
                self.slave_context.setValues(3, address, [int(value)])
            elif register_type == 'input_register':
                self.slave_context.setValues(4, address, [int(value)])
            else:
                return OperationResult(False, error=f"无效的寄存器类型: {register_type}")
            
            # 触发回调
            if self.on_value_change:
                self.on_value_change(register_type, address, value)
            
            success_msg = f"写入 {register_type} 地址 {address} = {value}"
            self._log(success_msg, "SUCCESS")
            return OperationResult(True, data=success_msg)
            
        except Exception as e:
            error_msg = f"写入失败: {str(e)}"
            self._log(error_msg, "ERROR")
            return OperationResult(False, error=error_msg)
    
    def _find_point(self, register_type: str, address: int) -> Optional[RegisterPoint]:
        """查找点位配置"""
        for point in self.config.register_points:
            if point.register_type == register_type and point.address == address:
                return point
        return None
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志到日志窗口
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO/WARNING/ERROR/SUCCESS)
        """
        if self.on_log:
            try:
                self.on_log(f"[{self.config.name}] {message}", level)
            except Exception as e:
                logging.error(f"日志回调失败: {e}")
    
    def get_all_values(self) -> Dict[str, Any]:
        """
        获取所有寄存器的值
        
        Returns:
            寄存器值字典
        """
        values = {
            'coils': [],
            'discrete_inputs': [],
            'holding_registers': [],
            'input_registers': []
        }
        
        try:
            if self.slave_context:
                # 读取所有配置的点位
                for point in self.config.register_points:
                    result = self.read_register(point.register_type, point.address)
                    if result.success:
                        key_map = {
                            'coil': 'coils',
                            'discrete_input': 'discrete_inputs',
                            'holding_register': 'holding_registers',
                            'input_register': 'input_registers'
                        }
                        key = key_map.get(point.register_type)
                        if key:
                            values[key].append({
                                'address': point.address,
                                'name': point.name,
                                'value': result.data,
                                'description': point.description
                            })
        except Exception as e:
            logging.error(f"获取所有值失败: {e}")
        
        return values


class SlaveManager:
    """Slave 管理器 - 管理多个 Modbus Slave"""
    
    def __init__(self):
        """初始化 Slave 管理器"""
        self.slaves: Dict[str, ModbusSlave] = {}
        self.lock = threading.Lock()
        self.on_log: Optional[Callable[[str, str], None]] = None  # 日志回调
    
    def add_slave(self, config: SlaveConfig) -> OperationResult:
        """
        添加 Slave
        
        Args:
            config: Slave 配置
            
        Returns:
            操作结果
        """
        with self.lock:
            if config.slave_id in self.slaves:
                return OperationResult(False, error=f"Slave ID {config.slave_id} 已存在")
            
            slave = ModbusSlave(config)
            # 设置日志回调
            if self.on_log:
                slave.on_log = self.on_log
            self.slaves[config.slave_id] = slave
            return OperationResult(True, data=f"Slave {config.name} 添加成功")
    
    def remove_slave(self, slave_id: str) -> OperationResult:
        """
        移除 Slave
        
        Args:
            slave_id: Slave ID
            
        Returns:
            操作结果
        """
        with self.lock:
            if slave_id not in self.slaves:
                return OperationResult(False, error=f"Slave ID {slave_id} 不存在")
            
            slave = self.slaves[slave_id]
            if slave.running:
                slave.stop()
            
            del self.slaves[slave_id]
            return OperationResult(True, data="Slave 移除成功")
    
    def get_slave(self, slave_id: str) -> Optional[ModbusSlave]:
        """
        获取 Slave
        
        Args:
            slave_id: Slave ID
            
        Returns:
            Slave 对象，不存在返回 None
        """
        return self.slaves.get(slave_id)
    
    def get_all_slaves(self) -> List[ModbusSlave]:
        """
        获取所有 Slave
        
        Returns:
            Slave 列表
        """
        return list(self.slaves.values())
    
    def start_slave(self, slave_id: str) -> OperationResult:
        """
        启动指定 Slave
        
        Args:
            slave_id: Slave ID
            
        Returns:
            操作结果
        """
        slave = self.get_slave(slave_id)
        if not slave:
            return OperationResult(False, error=f"Slave ID {slave_id} 不存在")
        
        return slave.start()
    
    def stop_slave(self, slave_id: str) -> OperationResult:
        """
        停止指定 Slave
        
        Args:
            slave_id: Slave ID
            
        Returns:
            操作结果
        """
        slave = self.get_slave(slave_id)
        if not slave:
            return OperationResult(False, error=f"Slave ID {slave_id} 不存在")
        
        return slave.stop()
    
    def stop_all(self) -> None:
        """停止所有 Slave"""
        for slave in self.slaves.values():
            if slave.running:
                slave.stop()
