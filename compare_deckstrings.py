#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用于比较两个炉石卡组代码的原始字节流和解码后的数据
"""

import base64
import io
import itertools

try:
    # 尝试从 deckstring_parser 导入 read_varint
    from deckstring_parser import read_varint, load_card_database
except ImportError:
    print("错误：无法导入 deckstring_parser.py。请确保该文件在同一目录下。")
    # 定义一个备用的 read_varint 以便至少可以进行字节比较
    def read_varint(stream):
        result = 0
        shift = 0
        while True:
            byte = stream.read(1)
            if not byte: raise EOFError("EOF")
            value = ord(byte)
            result |= (value & 0x7F) << shift
            if (value & 0x80) == 0: break
            shift += 7
        return result
    # 备用加载函数，返回空字典
    def load_card_database(json_path=""):
        return {}

def decode_and_compare(deckstring1, deckstring2, card_db):
    """解码两个卡组代码并详细比较字节流和解码数据"""
    try:
        bytes1 = base64.b64decode(deckstring1)
        bytes2 = base64.b64decode(deckstring2)
        stream1 = io.BytesIO(bytes1)
        stream2 = io.BytesIO(bytes2)
        
        print("--- 原始字节流对比 ---")
        max_len = max(len(bytes1), len(bytes2))
        diff_found_bytes = False
        for i in range(max_len):
            b1 = bytes1[i:i+1]
            b2 = bytes2[i:i+1]
            hex1 = b1.hex() if b1 else ''
            hex2 = b2.hex() if b2 else ''
            marker = " "
            if hex1 != hex2:
                marker = "*"
                diff_found_bytes = True
            print(f"Byte {i:02d}: {hex1:>2s} | {hex2:>2s} {marker}")
        if not diff_found_bytes:
            print("原始字节流完全相同。")
        else:
             print("* 表示字节不同")
        print("-----------------------\n")
        
        print("--- Varint 解码对比 ---")
        results = []
        diff_found_decode = False

        def read_and_compare(step_name):
            nonlocal diff_found_decode
            try:
                val1 = read_varint(stream1)
            except EOFError:
                val1 = "(EOF)"
            try:
                val2 = read_varint(stream2)
            except EOFError:
                val2 = "(EOF)"
            
            marker = " "
            if val1 != val2:
                marker = "*"
                diff_found_decode = True
                
            results.append(f"{step_name:<15}: {str(val1):<10} | {str(val2):<10} {marker}")
            return val1, val2

        # 1. Header
        read_and_compare("Reserved")
        read_and_compare("Version")
        read_and_compare("Format")
        
        # 2. Heroes
        num_heroes1, num_heroes2 = read_and_compare("Num Heroes")
        heroes1, heroes2 = [], []
        num_heroes = max(num_heroes1 if isinstance(num_heroes1, int) else 0, 
                         num_heroes2 if isinstance(num_heroes2, int) else 0)
        for i in range(num_heroes):
            h1, h2 = read_and_compare(f"Hero {i+1} ID")
            heroes1.append(h1)
            heroes2.append(h2)

        # 3. Cards x1
        num_cards1_1, num_cards1_2 = read_and_compare("Num Cards x1")
        cards1_1, cards1_2 = [], []
        num_cards1 = max(num_cards1_1 if isinstance(num_cards1_1, int) else 0,
                           num_cards1_2 if isinstance(num_cards1_2, int) else 0)
        for i in range(num_cards1):
            c1, c2 = read_and_compare(f"Card x1 [{i}] ID")
            cards1_1.append(c1)
            cards1_2.append(c2)
            # 如果找到不同的卡牌 ID，并且有卡牌数据库，尝试显示卡牌名称
            if c1 != c2 and card_db:
                name1 = card_db.get(c1, {}).get('name', '未知')
                name2 = card_db.get(c2, {}).get('name', '未知')
                results.append(f"  -> 卡牌名称: {name1} | {name2} *")

        # 4. Cards x2
        num_cards2_1, num_cards2_2 = read_and_compare("Num Cards x2")
        cards2_1, cards2_2 = [], []
        num_cards2 = max(num_cards2_1 if isinstance(num_cards2_1, int) else 0,
                           num_cards2_2 if isinstance(num_cards2_2, int) else 0)
        for i in range(num_cards2):
            c1, c2 = read_and_compare(f"Card x2 [{i}] ID")
            cards2_1.append(c1)
            cards2_2.append(c2)
            if c1 != c2 and card_db:
                name1 = card_db.get(c1, {}).get('name', '未知')
                name2 = card_db.get(c2, {}).get('name', '未知')
                results.append(f"  -> 卡牌名称: {name1} | {name2} *")

        # 5. Cards xn (通常为空)
        num_cardsn_1, num_cardsn_2 = read_and_compare("Num Cards xn")
        cardsn_1, cardsn_2 = [], []
        num_cardsn = max(num_cardsn_1 if isinstance(num_cardsn_1, int) else 0,
                           num_cardsn_2 if isinstance(num_cardsn_2, int) else 0)
        for i in range(num_cardsn):
            id1, id2 = read_and_compare(f"Card xn [{i}] ID")
            count1, count2 = read_and_compare(f"Card xn [{i}] Count")
            cardsn_1.append((id1, count1))
            cardsn_2.append((id2, count2))
        
        # 打印结果
        print("步骤           | 代码 1      | 代码 2      | 差异")
        print("-"*50)
        for line in results:
            print(line)
        
        if not diff_found_decode:
            print("\n解码后的所有数值完全相同。")
        else:
            print("\n* 表示解码数值不同")
            
        print("------------------------")

    except Exception as e:
        print(f"比较过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 你的代码
    deckstring_yours = "AAECAa+nBwyh1ATLnwajogbHpAa9sQa6zgb23Qbh6gb9/AaSgwfDgwe8lAcJh/YEkMsGi9wGnuIG5uUGgf0GloIHl4IHtpQHAA=="
    # 官方代码
    deckstring_official = "AAECAa+nBwyh1ATLnwajogbHpAa9sQa6zgb23Qbh6gb9/AaSgwfDgwe8lAcJh/YEkMsGi9wGnuIG5uUGgf0GloIHl4IHtpQHAAED9bMGx6QG97MGx6QG6N4Gx6QGAAA="

    print("正在加载卡牌数据库...")
    card_database = load_card_database()
    if not card_database:
        print("警告：无法加载卡牌数据库，将无法显示卡牌名称。")
    else:
        print(f"卡牌数据库加载成功 ({len(card_database)} 条目)。")
    print("")

    decode_and_compare(deckstring_yours, deckstring_official, card_database) 