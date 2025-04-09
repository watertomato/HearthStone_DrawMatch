from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt

def write_varint(data, value):
    """
    将整数编码为 varint 并添加到字节数组中
    
    Args:
        data: 目标字节数组，使用 bytearray 或支持 extend 方法的类似对象
        value: 要编码的整数值
        
    Returns:
        None，直接修改传入的 data 对象
    """
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        data.append(byte)
        if not value:
            break

class NumericTableWidgetItem(QTableWidgetItem):
    """自定义 TableWidgetItem 用于数字排序"""
    def __lt__(self, other):
        try:
            # 尝试将文本转换为浮点数进行比较
            return float(self.text()) < float(other.text())
        except ValueError:
            # 如果转换失败（例如文本不是数字），则按字符串比较
            return super().__lt__(other)

def normalize_card_name(name):
    """规范化卡牌名称，用于模糊匹配"""
    import re
    # 转为小写
    name = name.lower()
    # 移除所有空格
    name = name.replace(" ", "")
    # 移除所有标点符号
    name = re.sub(r'[^\w\s]', '', name)
    return name 