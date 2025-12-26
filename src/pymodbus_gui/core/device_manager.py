"""
Modbus 设备管理器
支持多设备并发连接，包括 RTU 和 TCP 设备
"""
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import threading
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException


class ConnectionType(Enum):
    """连接类型枚举"""
    RTU = "RTU"
    TCP = "TCP"


class FunctionCode(Enum):
    """Modbus 功能码枚举"""
    READ_COILS = 1  # 读线圈
    READ_DISCRETE_INPUTS = 2  # 读离散输入
    READ_HOLDING_REGISTERS = 3  # 读保持寄存器
    READ_INPUT_REGISTERS = 4  # 读输入寄存器
    WRITE_SINGLE_COIL = 5  # 写单个线圈
    WRITE_SINGLE_REGISTER = 6  # 写单个寄存器
    READ_EXCEPTION_STATUS = 7  # 读异常状态
    DIAGNOSTICS = 8  # 诊断
    GET_COMM_EVENT_COUNTER = 11  # 获取通信事件计数器
    GET_COMM_EVENT_LOG = 12  # 获取通信事件日志
    WRITE_MULTIPLE_COILS = 15  # 写多个线圈
    WRITE_MULTIPLE_REGISTERS = 16  # 写多个寄存器
    REPORT_SLAVE_ID = 17  # 报告从站 ID
    READ_FILE_RECORD = 20  # 读文件记录
    WRITE_FILE_RECORD = 21  # 写文件记录


@dataclass
class DeviceConfig:
    """设备配置数据类"""
    device_id: str  # 设备唯一标识
    name: str  # 设备名称
    connection_type: ConnectionType  # 连接类型
    slave_id: int = 1  # 从站地址
    
    # RTU 配置
    port: Optional[str] = None  # 串口端口
    baudrate: int = 9600  # 波特率
    bytesize: int = 8  # 数据位
    parity: str = 'N'  # 校验位 N/E/O
    stopbits: int = 1  # 停止位
    
    # TCP 配置
    host: Optional[str] = None  # IP地址
    tcp_port: int = 502  # TCP端口
    
    # 通用配置
    timeout: float = 3.0  # 超时时间（秒）


@dataclass
class OperationResult:
    """操作结果数据类"""
    success: bool  # 操作是否成功
    data: Any = None  # 返回数据
    error: Optional[str] = None  # 错误信息


class ModbusDevice:
    """单个 Modbus 设备封装"""
    
    def __init__(self, config: DeviceConfig):
        """
        初始化设备
        
        Args:
            config: 设备配置
        """
        self.config = config
        self.client: Optional[Any] = None
        self.connected = False
        self.lock = threading.Lock()  # 线程锁，保证并发安全
        self.error_message: Optional[str] = None
    
    def connect(self) -> OperationResult:
        """
        连接设备
        
        Returns:
            操作结果
        """
        with self.lock:
            try:
                if self.config.connection_type == ConnectionType.RTU:
                    # 创建 RTU 客户端
                    if not self.config.port:
                        return OperationResult(False, error="RTU 模式需要指定串口端口")
                    
                    self.client = ModbusSerialClient(
                        method='rtu',
                        port=self.config.port,
                        baudrate=self.config.baudrate,
                        bytesize=self.config.bytesize,
                        parity=self.config.parity,
                        stopbits=self.config.stopbits,
                        timeout=self.config.timeout
                    )
                
                elif self.config.connection_type == ConnectionType.TCP:
                    # 创建 TCP 客户端
                    if not self.config.host:
                        return OperationResult(False, error="TCP 模式需要指定主机地址")
                    
                    self.client = ModbusTcpClient(
                        host=self.config.host,
                        port=self.config.tcp_port,
                        timeout=self.config.timeout
                    )
                
                # 连接到设备
                self.connected = self.client.connect()
                
                if self.connected:
                    self.error_message = None
                    return OperationResult(True, data=f"设备 {self.config.name} 连接成功")
                else:
                    self.error_message = "连接失败"
                    return OperationResult(False, error="连接失败")
                    
            except Exception as e:
                self.error_message = str(e)
                self.connected = False
                return OperationResult(False, error=f"连接异常: {str(e)}")
    
    def disconnect(self) -> OperationResult:
        """
        断开设备连接
        
        Returns:
            操作结果
        """
        with self.lock:
            try:
                if self.client and self.connected:
                    self.client.close()
                    self.connected = False
                    self.error_message = None
                    return OperationResult(True, data="断开连接成功")
                return OperationResult(True, data="设备未连接")
            except Exception as e:
                return OperationResult(False, error=f"断开连接异常: {str(e)}")
    
    def read_coils(self, address: int, count: int) -> OperationResult:
        """读取线圈 (功能码 01)"""
        return self._read_operation(1, address, count, "线圈")
    
    def read_discrete_inputs(self, address: int, count: int) -> OperationResult:
        """读取离散输入 (功能码 02)"""
        return self._read_operation(2, address, count, "离散输入")
    
    def read_holding_registers(self, address: int, count: int) -> OperationResult:
        """读取保持寄存器 (功能码 03)"""
        return self._read_operation(3, address, count, "保持寄存器")
    
    def read_input_registers(self, address: int, count: int) -> OperationResult:
        """读取输入寄存器 (功能码 04)"""
        return self._read_operation(4, address, count, "输入寄存器")
    
    def write_single_coil(self, address: int, value: bool) -> OperationResult:
        """写单个线圈 (功能码 05)"""
        with self.lock:
            if not self.connected or not self.client:
                return OperationResult(False, error="设备未连接")
            
            try:
                response = self.client.write_coil(
                    address=address,
                    value=value,
                    slave=self.config.slave_id
                )
                
                if response.isError():
                    return OperationResult(False, error=f"写入失败: {response}")
                
                return OperationResult(True, data={"address": address, "value": value})
                
            except Exception as e:
                return OperationResult(False, error=f"写入异常: {str(e)}")
    
    def write_single_register(self, address: int, value: int) -> OperationResult:
        """写单个寄存器 (功能码 06)"""
        with self.lock:
            if not self.connected or not self.client:
                return OperationResult(False, error="设备未连接")
            
            try:
                response = self.client.write_register(
                    address=address,
                    value=value,
                    slave=self.config.slave_id
                )
                
                if response.isError():
                    return OperationResult(False, error=f"写入失败: {response}")
                
                return OperationResult(True, data={"address": address, "value": value})
                
            except Exception as e:
                return OperationResult(False, error=f"写入异常: {str(e)}")
    
    def write_multiple_coils(self, address: int, values: List[bool]) -> OperationResult:
        """写多个线圈 (功能码 15)"""
        with self.lock:
            if not self.connected or not self.client:
                return OperationResult(False, error="设备未连接")
            
            try:
                response = self.client.write_coils(
                    address=address,
                    values=values,
                    slave=self.config.slave_id
                )
                
                if response.isError():
                    return OperationResult(False, error=f"写入失败: {response}")
                
                return OperationResult(True, data={"address": address, "count": len(values)})
                
            except Exception as e:
                return OperationResult(False, error=f"写入异常: {str(e)}")
    
    def write_multiple_registers(self, address: int, values: List[int]) -> OperationResult:
        """写多个寄存器 (功能码 16)"""
        with self.lock:
            if not self.connected or not self.client:
                return OperationResult(False, error="设备未连接")
            
            try:
                response = self.client.write_registers(
                    address=address,
                    values=values,
                    slave=self.config.slave_id
                )
                
                if response.isError():
                    return OperationResult(False, error=f"写入失败: {response}")
                
                return OperationResult(True, data={"address": address, "count": len(values)})
                
            except Exception as e:
                return OperationResult(False, error=f"写入异常: {str(e)}")
    
    def _read_operation(self, func_code: int, address: int, count: int, 
                        data_type: str) -> OperationResult:
        """
        通用读取操作
        
        Args:
            func_code: 功能码
            address: 起始地址
            count: 读取数量
            data_type: 数据类型描述
            
        Returns:
            操作结果
        """
        with self.lock:
            if not self.connected or not self.client:
                return OperationResult(False, error="设备未连接")
            
            try:
                if func_code == 1:
                    response = self.client.read_coils(
                        address=address, count=count, slave=self.config.slave_id
                    )
                elif func_code == 2:
                    response = self.client.read_discrete_inputs(
                        address=address, count=count, slave=self.config.slave_id
                    )
                elif func_code == 3:
                    response = self.client.read_holding_registers(
                        address=address, count=count, slave=self.config.slave_id
                    )
                elif func_code == 4:
                    response = self.client.read_input_registers(
                        address=address, count=count, slave=self.config.slave_id
                    )
                else:
                    return OperationResult(False, error=f"不支持的功能码: {func_code}")
                
                if response.isError():
                    return OperationResult(False, error=f"读取{data_type}失败: {response}")
                
                # 提取数据
                if func_code in [1, 2]:
                    data = response.bits[:count]
                else:
                    data = response.registers[:count]
                
                return OperationResult(True, data={
                    "address": address,
                    "count": count,
                    "values": data
                })
                
            except Exception as e:
                return OperationResult(False, error=f"读取{data_type}异常: {str(e)}")


class DeviceManager:
    """设备管理器 - 管理多个 Modbus 设备"""
    
    def __init__(self):
        """初始化设备管理器"""
        self.devices: Dict[str, ModbusDevice] = {}
        self.lock = threading.Lock()
    
    def add_device(self, config: DeviceConfig) -> OperationResult:
        """
        添加设备
        
        Args:
            config: 设备配置
            
        Returns:
            操作结果
        """
        with self.lock:
            if config.device_id in self.devices:
                return OperationResult(False, error=f"设备 ID {config.device_id} 已存在")
            
            device = ModbusDevice(config)
            self.devices[config.device_id] = device
            return OperationResult(True, data=f"设备 {config.name} 添加成功")
    
    def remove_device(self, device_id: str) -> OperationResult:
        """
        移除设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            操作结果
        """
        with self.lock:
            if device_id not in self.devices:
                return OperationResult(False, error=f"设备 ID {device_id} 不存在")
            
            device = self.devices[device_id]
            if device.connected:
                device.disconnect()
            
            del self.devices[device_id]
            return OperationResult(True, data="设备移除成功")
    
    def get_device(self, device_id: str) -> Optional[ModbusDevice]:
        """
        获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备对象，不存在返回 None
        """
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[ModbusDevice]:
        """
        获取所有设备
        
        Returns:
            设备列表
        """
        return list(self.devices.values())
    
    def connect_device(self, device_id: str) -> OperationResult:
        """
        连接指定设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            操作结果
        """
        device = self.get_device(device_id)
        if not device:
            return OperationResult(False, error=f"设备 ID {device_id} 不存在")
        
        return device.connect()
    
    def disconnect_device(self, device_id: str) -> OperationResult:
        """
        断开指定设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            操作结果
        """
        device = self.get_device(device_id)
        if not device:
            return OperationResult(False, error=f"设备 ID {device_id} 不存在")
        
        return device.disconnect()
    
    def disconnect_all(self) -> None:
        """断开所有设备连接"""
        for device in self.devices.values():
            if device.connected:
                device.disconnect()
