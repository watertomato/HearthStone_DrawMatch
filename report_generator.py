import os
import pandas as pd
from collections import defaultdict
from config import (CLASS_NAMES, EXCEL_COLORS, REPORTS_DIR, RARITY_NAMES, 
                   SET_NAMES, CARD_TYPE_NAMES, RACE_TRANSLATIONS, 
                   SPELL_SCHOOL_TRANSLATIONS)

class ReportGenerator:
    """抽卡报告生成器"""
    def __init__(self):
        self.reports_dir = REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
        # 初始化卡牌管理器
        from simulator import CardDataManager
        self.card_manager = CardDataManager()
        self.card_manager.load_card_data()
        
    def create_excel_report(self, report_path, cards_by_class):
        """创建Excel格式的抽卡报告，所有职业卡牌合并到一个表格中"""
        try:
            # 创建Excel写入对象
            with pd.ExcelWriter(report_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # 创建表头格式
                header_format = workbook.add_format({
                    'bold': True,
                    'font_size': 12,
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1
                })
                
                # 创建每种稀有度的单元格格式
                rarity_formats = {
                    'LEGENDARY': workbook.add_format({
                        'bg_color': EXCEL_COLORS['LEGENDARY'],  # 淡橙色
                        'font_color': 'black',
                        'border': 1,
                        'align': 'center'
                    }),
                    'EPIC': workbook.add_format({
                        'bg_color': EXCEL_COLORS['EPIC'],  # 淡紫色
                        'font_color': 'black',
                        'border': 1,
                        'align': 'center'
                    }),
                    'RARE': workbook.add_format({
                        'bg_color': EXCEL_COLORS['RARE'],  # 淡蓝色
                        'font_color': 'black',
                        'border': 1,
                        'align': 'center'
                    }),
                    'COMMON': workbook.add_format({
                        'bg_color': EXCEL_COLORS['COMMON'],  # 淡灰色
                        'font_color': 'black',
                        'border': 1,
                        'align': 'center'
                    })
                }
                
                # 默认格式
                default_format = workbook.add_format({
                    'border': 1,
                    'align': 'center'
                })
                
                # 收集所有职业卡牌数据
                all_cards_data = []
                
                for class_id, cards in cards_by_class.items():
                    if not cards:  # 跳过没有卡牌的职业
                        continue
                        
                    class_name = CLASS_NAMES.get(class_id, class_id)
                    
                    # 按稀有度和名称排序
                    rarity_order = {'LEGENDARY': 0, 'EPIC': 1, 'RARE': 2, 'COMMON': 3}
                    sorted_cards = sorted(cards, key=lambda x: (rarity_order.get(x.get('rarity', 'COMMON'), 4), x.get('name', '')))
                    
                    # 添加每张卡牌到总列表中
                    for card in sorted_cards:
                        name = card.get('name', '未知卡牌')
                        rarity = card.get('rarity', 'COMMON')
                        # 转换稀有度为中文
                        rarity_cn = RARITY_NAMES.get(rarity, rarity)
                        count = card.get('count', 1)
                        
                        # 获取法力消耗
                        cost = card.get('cost', 0)
                        
                        # 获取卡牌类型并转换为中文
                        card_type = card.get('type', '')
                        card_type_cn = CARD_TYPE_NAMES.get(card_type, card_type)
                        
                        # 获取攻击力和生命值（只对随从有效）
                        attack_health = ""
                        if card_type == 'MINION':
                            attack = card.get('attack', 0)
                            health = card.get('health', 0)
                            attack_health = f"{attack}/{health}"
                        
                        # 获取种族/类型
                        race_type = ""
                        if card_type == 'MINION' and 'races' in card:
                            races = [RACE_TRANSLATIONS.get(race, race) for race in card['races']]
                            race_type = '、'.join(races)
                        elif card_type == 'SPELL' and 'spellSchool' in card:
                            race_type = SPELL_SCHOOL_TRANSLATIONS.get(card['spellSchool'], card['spellSchool'])
                        
                        # 添加卡牌描述
                        description = card.get('text', '')
                        # 处理描述中可能的HTML标签
                        description = description.replace('<b>', '').replace('</b>', '')
                        description = description.replace('<i>', '').replace('</i>', '')
                        
                        # 处理符文消耗
                        if 'runeCost' in card:
                            rune_cost = card['runeCost']
                            rune_text = []
                            if rune_cost.get('blood', 0) > 0:
                                rune_text.append(f"{rune_cost['blood']} 红")
                            if rune_cost.get('frost', 0) > 0:
                                rune_text.append(f"{rune_cost['frost']} 蓝")
                            if rune_cost.get('unholy', 0) > 0:
                                rune_text.append(f"{rune_cost['unholy']} 绿")
                            if rune_text:
                                description = f"符文：{', '.join(rune_text)}。\n{description}"
                        
                        # 获取卡牌所属的扩展包ID
                        card_set_id = card.get('set', '')
                        # 转换扩展包ID为中文名称
                        card_set = SET_NAMES.get(card_set_id, card_set_id)
                        
                        all_cards_data.append([name, class_name, card_set, rarity_cn, cost, card_type_cn, attack_health, race_type, count, description])
                
                # 按稀有度排序 (使用原始稀有度英文代码进行排序)
                rarity_mapping = {RARITY_NAMES['LEGENDARY']: 0, RARITY_NAMES['EPIC']: 1, RARITY_NAMES['RARE']: 2, RARITY_NAMES['COMMON']: 3}
                all_cards_data.sort(key=lambda x: (rarity_mapping.get(x[3], 4), x[1], x[0]))
                
                # 创建所有卡牌的DataFrame
                all_cards_df = pd.DataFrame(all_cards_data, columns=['卡牌名称', '职业', '扩展包', '稀有度', '法力值', '卡牌类型', '攻击力/生命值', '种族/类型', '数量', '卡牌描述'])
                
                # 写入所有卡牌工作表
                all_cards_df.to_excel(writer, sheet_name='抽卡结果', index=False)
                all_cards_sheet = writer.sheets['抽卡结果']
                
                # 添加表头筛选功能
                all_cards_sheet.autofilter(0, 0, len(all_cards_data), 9)  # 调整为包含新列
                
                # 设置列宽
                all_cards_sheet.set_column('A:A', 30)  # 卡牌名称列宽
                all_cards_sheet.set_column('B:B', 12)  # 职业列宽
                all_cards_sheet.set_column('C:C', 18)  # 扩展包列宽
                all_cards_sheet.set_column('D:D', 10)  # 稀有度列宽
                all_cards_sheet.set_column('E:E', 8)   # 法力值列宽
                all_cards_sheet.set_column('F:F', 10)  # 卡牌类型列宽
                all_cards_sheet.set_column('G:G', 15)  # 攻击力/生命值列宽
                all_cards_sheet.set_column('H:H', 15)  # 种族/类型列宽
                all_cards_sheet.set_column('I:I', 8)   # 数量列宽
                all_cards_sheet.set_column('J:J', 70)  # 卡牌描述列宽
                
                # 创建描述列的字体格式（字体更小）
                description_format = workbook.add_format({
                    'font_size': 9,  # 字体大小减小到9
                    'border': 1,
                    'align': 'left',  # 靠左对齐更适合长文本
                    'valign': 'top',
                    'text_wrap': True
                })
                
                # 应用格式到表头
                for col_num, value in enumerate(['卡牌名称', '职业', '扩展包', '稀有度', '法力值', '卡牌类型', '攻击力/生命值', '种族/类型', '数量', '卡牌描述']):
                    all_cards_sheet.write(0, col_num, value, header_format)
                
                # 应用稀有度颜色格式到数据行
                for row_num, (name, class_name, card_set, rarity_cn, cost, card_type_cn, attack_health, race_type, count, description) in enumerate(all_cards_data):
                    # 根据中文稀有度查找原始稀有度代码
                    original_rarity = next((k for k, v in RARITY_NAMES.items() if v == rarity_cn), None)
                    if not original_rarity:
                        # 回退到默认稀有度格式
                        original_rarity = 'COMMON'
                    
                    cell_format = rarity_formats.get(original_rarity, default_format)
                    
                    # 写入数据并应用格式
                    all_cards_sheet.write(row_num + 1, 0, name, cell_format)
                    all_cards_sheet.write(row_num + 1, 1, class_name, cell_format)
                    all_cards_sheet.write(row_num + 1, 2, card_set, cell_format)
                    all_cards_sheet.write(row_num + 1, 3, rarity_cn, cell_format)
                    all_cards_sheet.write(row_num + 1, 4, cost, cell_format)
                    all_cards_sheet.write(row_num + 1, 5, card_type_cn, cell_format)
                    all_cards_sheet.write(row_num + 1, 6, attack_health, cell_format)  # 攻击力/生命值
                    all_cards_sheet.write(row_num + 1, 7, race_type, cell_format)  # 种族/类型
                    all_cards_sheet.write(row_num + 1, 8, count, cell_format)
                    # 对描述列使用特殊格式
                    all_cards_sheet.write(row_num + 1, 9, description, description_format)
                
                # 统计工作表 - 按稀有度统计
                rarity_stats = defaultdict(int)
                total_cards = 0
                
                for class_cards in cards_by_class.values():
                    for card in class_cards:
                        rarity = card.get('rarity', 'COMMON')
                        count = card.get('count', 1)
                        rarity_stats[rarity] += count
                        total_cards += count
                
                # 创建稀有度统计数据（使用中文稀有度名称）
                rarity_data = []
                for rarity in ['LEGENDARY', 'EPIC', 'RARE', 'COMMON']:
                    if rarity in rarity_stats:
                        count = rarity_stats[rarity]
                        percentage = (count / total_cards) * 100 if total_cards > 0 else 0
                        # 使用中文稀有度名称
                        rarity_cn = RARITY_NAMES.get(rarity, rarity)
                        rarity_data.append([rarity_cn, count, f"{percentage:.2f}%"])
                
                # 创建稀有度统计工作表
                rarity_df = pd.DataFrame(rarity_data, columns=['稀有度', '数量', '百分比'])
                rarity_df.to_excel(writer, sheet_name='稀有度统计', index=False)
                
                rarity_sheet = writer.sheets['稀有度统计']
                rarity_sheet.set_column('A:C', 15)
                
                # 为稀有度统计应用格式
                for row_num, (rarity_cn, _, _) in enumerate(rarity_data):
                    # 查找对应的原始稀有度代码
                    original_rarity = next((k for k, v in RARITY_NAMES.items() if v == rarity_cn), None)
                    if not original_rarity:
                        original_rarity = 'COMMON'
                        
                    cell_format = rarity_formats.get(original_rarity, default_format)
                    
                    for col_num in range(3):
                        rarity_sheet.write(row_num + 1, col_num, rarity_df.iloc[row_num, col_num], cell_format)
                
                # 创建卡牌类型统计工作表
                card_type_stats = defaultdict(int)
                
                for class_cards in cards_by_class.values():
                    for card in class_cards:
                        card_type = card.get('type', '')
                        count = card.get('count', 1)
                        card_type_stats[card_type] += count
                
                # 创建卡牌类型统计数据
                card_type_data = []
                for card_type, count in card_type_stats.items():
                    if not card_type:
                        continue
                    # 使用中文卡牌类型名称
                    card_type_cn = CARD_TYPE_NAMES.get(card_type, card_type)
                    percentage = (count / total_cards) * 100 if total_cards > 0 else 0
                    card_type_data.append([card_type_cn, count, f"{percentage:.2f}%"])
                
                # 按数量排序
                card_type_data.sort(key=lambda x: x[1], reverse=True)
                
                # 创建卡牌类型统计工作表
                if card_type_data:
                    card_type_df = pd.DataFrame(card_type_data, columns=['卡牌类型', '数量', '百分比'])
                    card_type_df.to_excel(writer, sheet_name='卡牌类型统计', index=False)
                    
                    card_type_sheet = writer.sheets['卡牌类型统计']
                    card_type_sheet.set_column('A:C', 15)
                    
                    # 应用格式
                    for row_num in range(len(card_type_data)):
                        for col_num in range(3):
                            card_type_sheet.write(row_num + 1, col_num, card_type_df.iloc[row_num, col_num], default_format)
        
            # 文件保存后释放资源
            workbook = None
            writer = None
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            print(f"创建Excel报告时出错: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    def generate_pack_report(self, all_opened_cards, timestamp=None, include_core_event=False):
        """生成抽卡报告数据
        
        Args:
            all_opened_cards: 所有抽到的卡牌列表
            timestamp: 可选时间戳，用于文件名
            include_core_event: 是否包含核心和活动卡
            
        Returns:
            str: 报告文件路径
        """
        # 导入时间模块
        import datetime
        
        # 获取时间戳
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建报告文件名
        report_filename = f"抽卡报告_{timestamp}.xlsx"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        # 按职业分类卡牌并统计数量
        cards_by_class = {}
        # 先按职业和ID分类卡牌
        cards_temp = defaultdict(lambda: defaultdict(int))
        
        # 使用副本避免修改原始数据
        cards_copy = list(all_opened_cards)
        
        # 如果需要包含核心和活动卡
        if include_core_event:
            # 从卡牌管理器中获取核心和活动卡
            core_cards = self.card_manager.get_cards_by_set('CORE')
            event_cards = self.card_manager.get_cards_by_set('EVENT')
            
            # 预先处理核心和活动卡，并设置固定数量
            for card_list, set_id in [(core_cards, 'CORE'), (event_cards, 'EVENT')]:
                for card in card_list:
                    card_class = card.get('cardClass', 'NEUTRAL')
                    card_id = card.get('id', '')
                    if not card_id:
                        continue
                    
                    # 根据稀有度设置固定数量
                    if card.get('rarity') == 'LEGENDARY':
                        # 传说卡设置为1张
                        fixed_count = 1
                    else:
                        # 非传说卡设置为2张
                        fixed_count = 2
                    
                    # 直接设置到cards_temp中
                    cards_temp[card_class][card_id] = fixed_count
                    
                    # 将卡牌添加到cards_copy以便后续提取卡牌信息
                    card_copy = card.copy()
                    card_copy['set'] = set_id
                    cards_copy.append(card_copy)
        
        # 处理常规抽到的卡牌
        for card in all_opened_cards:  # 注意这里使用原始的all_opened_cards而不是cards_copy
            card_class = card.get('cardClass', 'NEUTRAL')
            card_id = card.get('id', '')
            if not card_id:
                continue
            cards_temp[card_class][card_id] += 1
        
        # 转换为最终数据结构
        for class_id, card_counts in cards_temp.items():
            cards_by_class[class_id] = []
            for card_id, count in card_counts.items():
                # 找到该卡牌的完整信息
                card_info = None
                for card in cards_copy:
                    if card.get('id') == card_id:
                        card_info = card.copy()  # 复制一份避免修改原始数据
                        break
                if card_info:
                    card_info['count'] = count
                    cards_by_class[class_id].append(card_info)
        
        # 创建Excel报告
        if self.create_excel_report(report_path, cards_by_class):
            return report_path
        
        return None 

    def generate_transmog_report(self, selected_sets, timestamp=None, include_core_event=False):
        """生成幻变卡牌报告
        
        Args:
            selected_sets: 所选扩展包的ID列表
            timestamp: 可选时间戳，用于文件名
            include_core_event: 是否包含核心和活动卡
            
        Returns:
            str: 报告文件路径
        """
        # 导入时间模块
        import datetime
        
        # 获取时间戳
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建报告文件名
        report_filename = f"幻变卡牌报告_{timestamp}.xlsx"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        # 按职业分类卡牌
        cards_by_class = {}
        cards_temp = defaultdict(lambda: defaultdict(int))
        
        # 处理选中的扩展包卡牌
        for set_id in selected_sets:
            cards = self.card_manager.get_cards_by_set(set_id)
            for card in cards:
                card_class = card.get('cardClass', 'NEUTRAL')
                card_id = card.get('id', '')
                if not card_id:
                    continue
                
                # 根据稀有度设置固定数量
                if card.get('rarity') == 'LEGENDARY':
                    # 传说卡设置为1张
                    fixed_count = 1
                else:
                    # 非传说卡设置为2张
                    fixed_count = 2
                
                # 直接设置到cards_temp中
                cards_temp[card_class][card_id] = fixed_count
        
        # 如果需要包含核心和活动卡
        if include_core_event:
            # 从卡牌管理器中获取核心和活动卡
            core_cards = self.card_manager.get_cards_by_set('CORE')
            event_cards = self.card_manager.get_cards_by_set('EVENT')
            
            # 预先处理核心和活动卡，并设置固定数量
            for card_list in [core_cards, event_cards]:
                for card in card_list:
                    card_class = card.get('cardClass', 'NEUTRAL')
                    card_id = card.get('id', '')
                    if not card_id:
                        continue
                    
                    # 根据稀有度设置固定数量
                    if card.get('rarity') == 'LEGENDARY':
                        # 传说卡设置为1张
                        fixed_count = 1
                    else:
                        # 非传说卡设置为2张
                        fixed_count = 2
                    
                    # 直接设置到cards_temp中
                    cards_temp[card_class][card_id] = fixed_count
        
        # 收集所有卡牌信息
        all_cards = []
        for set_id in selected_sets:
            cards = self.card_manager.get_cards_by_set(set_id)
            for card in cards:
                all_cards.append(card)
        
        if include_core_event:
            all_cards.extend(core_cards)
            all_cards.extend(event_cards)
        
        # 转换为最终数据结构
        for class_id, card_counts in cards_temp.items():
            cards_by_class[class_id] = []
            for card_id, count in card_counts.items():
                # 找到该卡牌的完整信息
                card_info = None
                for card in all_cards:
                    if card.get('id') == card_id:
                        card_info = card.copy()  # 复制一份避免修改原始数据
                        break
                if card_info:
                    card_info['count'] = count
                    cards_by_class[class_id].append(card_info)
        
        # 创建Excel报告
        if self.create_excel_report(report_path, cards_by_class):
            return report_path
        
        return None 