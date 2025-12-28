import pandas as pd
import random

REGISTER_TYPES = [
    ('线圈',    'Coil',           '01/05/15', False, 'bit'),
    ('离散输入', 'Discrete Input', '02',       True,  'bit'),
    ('保持寄存器','Holding Register','03/06/16', False, 'word'),
    ('输入寄存器','Input Register', '04',       True,  'word'),
]

UNITS = ['°C', 'kPa', 'A', 'V', 'rpm', '', '', '', '']
DESC_PREFIX = {
    '线圈': '设备运行状态',
    '离散输入': '故障报警',
    '保持寄存器': '参数设定',
    '输入寄存器': '设备测量值'
}

def pick_initial_value(reg_type):
    if reg_type in ['线圈', '离散输入']:
        return random.choice([0, 1])
    else:
        return random.randint(0, 65535)

def pick_unit():
    return random.choice(UNITS)

def min_max_value(reg_type):
    if reg_type in ['线圈', '离散输入']:
        return '', ''
    elif reg_type in ['保持寄存器', '输入寄存器']:
        minv = random.randint(0, 10000)
        maxv = random.randint(minv+1, min(65535, minv+50000))
        return minv, maxv
    return '', ''

def generate_examples(n_per_type=5):
    examples = []
    used_addresses = {reg_type[0]: set() for reg_type in REGISTER_TYPES}
    for reg_type, _, _, read_only_default, addr_type in REGISTER_TYPES:
        for i in range(n_per_type):
            # 线圈、离散输入(位地址): 0-65535
            # 保持、输入寄存器(字地址): 0-65535
            while True:
                addr = random.randint(0, 65535)
                if addr not in used_addresses[reg_type]:
                    used_addresses[reg_type].add(addr)
                    break
            minv, maxv = min_max_value(reg_type)
            unit = pick_unit() if reg_type in ['保持寄存器', '输入寄存器'] else ''
            example = {
                '地址': addr,
                '点位名称': f"{DESC_PREFIX[reg_type]}{i+1}",
                '寄存器类型': reg_type,
                '初始值': pick_initial_value(reg_type),
                '描述': f"{DESC_PREFIX[reg_type]}示例{i+1}",
                '单位': unit,
                '最小值': minv,
                '最大值': maxv,
                '只读': '是' if read_only_default else random.choice(['是', '否'])
            }
            examples.append(example)
    return examples

def save_to_excel(examples, filename='modbus_example.xlsx'):
    df = pd.DataFrame(examples)
    df.to_excel(filename, index=False)
    print(f"写入完毕，已生成 {filename}")

if __name__ == "__main__":
    examples = generate_examples(n_per_type=10) # 每种类型10条（共40条）
    save_to_excel(examples, "modbus_example.xlsx")