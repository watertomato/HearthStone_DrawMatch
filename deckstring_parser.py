#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
炉石传说卡组代码解析与生成工具
根据 HearthSim 文档实现 https://hearthsim.info/docs/deckstrings/
"""

import base64
import json
import os
import io

# 游戏模式常量
FORMAT_WILD = 1
FORMAT_STANDARD = 2
FORMAT_CLASSIC = 3

# 游戏模式名称映射
FORMAT_NAMES = {
    FORMAT_WILD: "狂野模式",
    FORMAT_STANDARD: "标准模式",
    FORMAT_CLASSIC: "经典模式"
}

# 英雄 DBF ID 到职业名称的映射
HERO_ID_TO_CLASS = {
    7: "战士",        # 加尔鲁什
    31: "猎人",       # 雷克萨
    274: "德鲁伊",     # 玛法里奥
    637: "法师",      # 吉安娜
    671: "圣骑士",     # 乌瑟尔
    813: "牧师",      # 安度因
    893: "术士",      # 古尔丹
    930: "潜行者",     # 瓦莉拉
    1066: "萨满",     # 萨尔
    56550: "恶魔猎手", # 伊利丹
    78065: "死亡骑士", # 阿萨斯
    # 添加其他英雄皮肤的映射...
}

# 职业名称到默认英雄 DBF ID 的映射
CLASS_TO_HERO_ID = {
    "战士": 7,        # 加尔鲁什
    "猎人": 31,       # 雷克萨
    "德鲁伊": 274,     # 玛法里奥
    "法师": 637,      # 吉安娜
    "圣骑士": 671,     # 乌瑟尔
    "牧师": 813,      # 安度因
    "术士": 893,      # 古尔丹
    "潜行者": 930,     # 瓦莉拉
    "萨满": 1066,     # 萨尔
    "恶魔猎手": 56550, # 伊利丹
    "死亡骑士": 78065, # 阿萨斯
}

def read_varint(stream):
    """
    从字节流中读取一个 varint 编码的整数
    
    Args:
        stream: 字节流对象，支持read方法
        
    Returns:
        解码后的整数值
    """
    result = 0
    shift = 0
    
    while True:
        byte = stream.read(1)
        if not byte:  # 如果没有更多字节，则终止
            raise EOFError("Unexpected end of stream while reading varint")
            
        value = ord(byte)
        result |= (value & 0x7F) << shift
        
        if (value & 0x80) == 0:  # 最高位为0，表示varint的结束
            break
            
        shift += 7
        
    return result

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

def parse_deckstring(deckstring):
    """
    解析炉石传说卡组代码字符串
    
    Args:
        deckstring: Base64编码的卡组代码字符串
        
    Returns:
        包含解析结果的字典，格式如下:
        {
            'format': 游戏模式 (1=狂野, 2=标准, 3=经典),
            'heroes': [英雄DBF ID列表],
            'cards': [卡牌列表],
            'cards_by_count': {
                '1': [单卡列表],
                '2': [双卡列表],
                'n': [(卡牌ID, 数量)的列表]
            }
        }
    """
    try:
        # 解码Base64字符串
        decoded_bytes = base64.b64decode(deckstring)
        stream = io.BytesIO(decoded_bytes)
        
        # 读取头部
        reserved_byte = stream.read(1)  # 应该是0x00，但我们不检查
        version = read_varint(stream)
        format_type = read_varint(stream)
        
        # 读取英雄数量
        num_heroes = read_varint(stream)
        heroes = []
        for _ in range(num_heroes):
            hero_dbf_id = read_varint(stream)
            heroes.append(hero_dbf_id)
            
        # 读取单张卡牌
        num_cards_x1 = read_varint(stream)
        cards_x1 = []
        for _ in range(num_cards_x1):
            card_dbf_id = read_varint(stream)
            cards_x1.append(card_dbf_id)
            
        # 读取双张卡牌
        num_cards_x2 = read_varint(stream)
        cards_x2 = []
        for _ in range(num_cards_x2):
            card_dbf_id = read_varint(stream)
            cards_x2.append(card_dbf_id)
            
        # 读取三张或更多卡牌 (在构筑模式下通常为空)
        num_cards_xn = read_varint(stream)
        cards_xn = []
        for _ in range(num_cards_xn):
            card_dbf_id = read_varint(stream)
            card_count = read_varint(stream)
            cards_xn.append((card_dbf_id, card_count))
            
        # 构建完整的卡牌列表
        all_cards = []
        for card_id in cards_x1:
            all_cards.append((card_id, 1))
        for card_id in cards_x2:
            all_cards.append((card_id, 2))
        for card_id, count in cards_xn:
            all_cards.append((card_id, count))
            
        # 返回结构化的结果
        return {
            'format': format_type,
            'heroes': heroes,
            'cards': all_cards,
            'cards_by_count': {
                '1': cards_x1,
                '2': cards_x2,
                'n': cards_xn
            }
        }
    except Exception as e:
        print(f"解析卡组代码时出错: {e}")
        return None

def create_deckstring(heroes, cards, format_type=FORMAT_STANDARD):
    """
    创建炉石传说卡组代码
    
    Args:
        heroes: 英雄 DBF ID 列表，通常只包含一个元素
        cards: 卡牌列表，格式为 [(dbf_id, count), ...]
        format_type: 游戏模式 (1=狂野, 2=标准, 3=经典)，默认为标准模式
        
    Returns:
        Base64编码的卡组代码字符串
    """
    try:
        # 按卡牌数量分类
        cards_x1 = []
        cards_x2 = []
        cards_xn = []
        
        for dbf_id, count in cards:
            if count == 1:
                cards_x1.append(dbf_id)
            elif count == 2:
                cards_x2.append(dbf_id)
            else:
                cards_xn.append((dbf_id, count))
        
        # 排序 (对于规范化的卡组代码很重要)
        cards_x1.sort()
        cards_x2.sort()
        cards_xn.sort()
        
        # 构建数据流
        data = bytearray()
        
        # 保留字节 + 版本 + 游戏模式
        data.append(0)  # 保留字节
        write_varint(data, 1)  # 版本 (目前总是1)
        write_varint(data, format_type)
        
        # 英雄
        write_varint(data, len(heroes))
        for hero_id in heroes:
            write_varint(data, hero_id)
        
        # 单张卡牌
        write_varint(data, len(cards_x1))
        for dbf_id in cards_x1:
            write_varint(data, dbf_id)
        
        # 双张卡牌
        write_varint(data, len(cards_x2))
        for dbf_id in cards_x2:
            write_varint(data, dbf_id)
        
        # 其他数量的卡牌
        write_varint(data, len(cards_xn))
        for dbf_id, count in cards_xn:
            write_varint(data, dbf_id)
            write_varint(data, count)
        
        # Base64编码
        encoded = base64.b64encode(data).decode('utf-8')
        return encoded
    
    except Exception as e:
        print(f"创建卡组代码时出错: {e}")
        return None

def load_card_database(json_path="hsJSON卡牌数据/card_infos.json"):
    """
    加载卡牌数据库，创建 DBF ID 到卡牌信息的映射
    
    Args:
        json_path: 卡牌数据JSON文件的路径
        
    Returns:
        DBF ID 到卡牌信息的字典
    """
    if not os.path.exists(json_path):
        print(f"找不到卡牌数据文件: {json_path}")
        return {}
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            all_cards = json.load(f)
            
        card_db = {}
        for card in all_cards:
            if 'dbfId' in card:
                card_db[card['dbfId']] = card
                
        return card_db
    except Exception as e:
        print(f"加载卡牌数据时出错: {e}")
        return {}

def format_deck_info(deck_data, card_db=None):
    """
    将解析后的卡组数据格式化为易读的文本
    
    Args:
        deck_data: parse_deckstring返回的字典
        card_db: DBF ID 到卡牌信息的字典，如果提供则显示卡牌名称
        
    Returns:
        格式化后的卡组信息文本
    """
    if not deck_data:
        return "无效的卡组代码"
        
    # 获取游戏模式名称
    format_name = FORMAT_NAMES.get(deck_data['format'], f"未知模式({deck_data['format']})")
    
    # 获取英雄和职业信息
    heroes_info = []
    for hero_id in deck_data['heroes']:
        class_name = HERO_ID_TO_CLASS.get(hero_id, "未知职业")
        if card_db and hero_id in card_db:
            hero_name = card_db[hero_id].get('name', f"英雄 {hero_id}")
            heroes_info.append(f"{hero_name} ({class_name}, ID: {hero_id})")
        else:
            heroes_info.append(f"{class_name} (ID: {hero_id})")
    
    # 构建结果文本
    result = []
    result.append(f"游戏模式: {format_name}")
    result.append(f"英雄: {', '.join(heroes_info)}")
    result.append(f"卡牌总数: {sum(count for _, count in deck_data['cards'])}")
    result.append("")
    
    # 按费用排序卡牌（如果有卡牌数据库）
    if card_db:
        # 卡牌列表: [(dbf_id, count), ...]
        card_list = []
        for dbf_id, count in deck_data['cards']:
            if dbf_id in card_db:
                card_info = card_db[dbf_id]
                name = card_info.get('name', f"未知卡牌 {dbf_id}")
                cost = card_info.get('cost', 0)
                card_list.append((dbf_id, count, name, cost))
            else:
                card_list.append((dbf_id, count, f"未知卡牌 {dbf_id}", 0))
                
        # 按费用和名称排序
        card_list.sort(key=lambda x: (x[3], x[2]))
        
        # 格式化卡牌列表
        result.append("卡牌列表 (费用 名称 x数量):")
        for dbf_id, count, name, cost in card_list:
            result.append(f"{cost}费 {name} x{count}")
    else:
        # 没有卡牌数据库，只显示DBF ID
        result.append("卡牌列表 (DBF ID x数量):")
        for dbf_id, count in sorted(deck_data['cards']):
            result.append(f"ID {dbf_id} x{count}")
    
    return "\n".join(result)

def main():
    """主函数，处理命令行参数并执行解析"""
    import argparse
    parser = argparse.ArgumentParser(description='解析或创建炉石传说卡组代码')
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 解析卡组代码的子命令
    parse_parser = subparsers.add_parser('parse', help='解析卡组代码')
    parse_parser.add_argument('deckstring', nargs='?', help='Base64编码的卡组代码 (可选，如果未提供则会提示输入)')
    parse_parser.add_argument('--json', '-j', help='卡牌数据JSON文件路径', default="hsJSON卡牌数据/card_infos.json")
    parse_parser.add_argument('--raw', '-r', action='store_true', help='输出原始解析结果')
    
    # 创建卡组代码的子命令
    create_parser = subparsers.add_parser('create', help='创建卡组代码')
    create_parser.add_argument('--hero', '-H', type=int, help='英雄DBF ID', required=True)
    create_parser.add_argument('--format', '-f', type=int, choices=[1, 2, 3], default=2, 
                              help='游戏模式 (1=狂野, 2=标准, 3=经典)')
    create_parser.add_argument('--cards', '-c', help='卡牌列表文件 (JSON格式，包含[dbfId, count]对数组)')
    
    args = parser.parse_args()
    
    if args.command == 'parse':
        deckstring = args.deckstring
        # 如果命令行没有提供 deckstring，则提示用户输入
        if not deckstring:
            try:
                deckstring = input("请输入要解析的卡组代码: ")
                if not deckstring:
                    print("未输入卡组代码。")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\n操作已取消。")
                return
        
        # 执行解析逻辑
        deck_data = parse_deckstring(deckstring)
        if not deck_data:
            print("无法解析卡组代码")
            return
        
        # 输出结果
        if args.raw:
            print(json.dumps(deck_data, indent=2, ensure_ascii=False))
        else:
            card_db = load_card_database(args.json)
            formatted_info = format_deck_info(deck_data, card_db)
            print("\n--- 解析结果 ---")
            print(formatted_info)
    
    elif args.command == 'create':
        # 加载卡牌列表
        if not args.cards:
            print("错误: 必须提供卡牌列表文件 (-c)")
            return
        
        try:
            with open(args.cards, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
            
            # 创建卡组代码
            deckstring = create_deckstring([args.hero], cards_data, args.format)
            if deckstring:
                print(f"卡组代码: {deckstring}")
            else:
                print("创建卡组代码失败")
        
        except Exception as e:
            print(f"处理卡牌列表时出错: {e}")
            
    else:
        # 如果没有提供命令，也默认进入交互式解析模式
        try:
            deckstring = input("请输入要解析的卡组代码: ")
            if not deckstring:
                print("未输入卡组代码。")
                return
                
            # 使用默认 JSON 路径，不支持 raw
            json_path = "hsJSON卡牌数据/card_infos.json"
            deck_data = parse_deckstring(deckstring)
            if not deck_data:
                print("无法解析卡组代码")
                return
                
            card_db = load_card_database(json_path)
            formatted_info = format_deck_info(deck_data, card_db)
            print("\n--- 解析结果 ---")
            print(formatted_info)
            
        except (EOFError, KeyboardInterrupt):
            print("\n操作已取消。")
            return

if __name__ == "__main__":
    main() 