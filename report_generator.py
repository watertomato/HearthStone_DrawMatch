import os
import pandas as pd
from collections import defaultdict
from config import CLASS_NAMES, EXCEL_COLORS, REPORTS_DIR

class ReportGenerator:
    """抽卡报告生成器"""
    def __init__(self):
        self.reports_dir = REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
        
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
                        count = card.get('count', 1)
                        # 添加卡牌描述
                        description = card.get('text', '')
                        # 处理描述中可能的HTML标签
                        description = description.replace('<b>', '').replace('</b>', '')
                        description = description.replace('<i>', '').replace('</i>', '')
                        
                        all_cards_data.append([name, class_name, rarity, count, description])
                
                # 按稀有度排序
                rarity_values = {'LEGENDARY': 0, 'EPIC': 1, 'RARE': 2, 'COMMON': 3}
                all_cards_data.sort(key=lambda x: (rarity_values.get(x[2], 4), x[1], x[0]))
                
                # 创建所有卡牌的DataFrame
                all_cards_df = pd.DataFrame(all_cards_data, columns=['卡牌名称', '职业', '稀有度', '数量', '卡牌描述'])
                
                # 写入所有卡牌工作表
                all_cards_df.to_excel(writer, sheet_name='抽卡结果', index=False)
                all_cards_sheet = writer.sheets['抽卡结果']
                
                # 添加表头筛选功能
                all_cards_sheet.autofilter(0, 0, len(all_cards_data), 4)
                
                # 设置列宽
                all_cards_sheet.set_column('A:A', 30)  # 卡牌名称列宽
                all_cards_sheet.set_column('B:B', 15)  # 职业列宽
                all_cards_sheet.set_column('C:C', 12)  # 稀有度列宽
                all_cards_sheet.set_column('D:D', 8)   # 数量列宽
                all_cards_sheet.set_column('E:E', 120)  # 卡牌描述列宽
                
                # 应用格式到表头
                for col_num, value in enumerate(['卡牌名称', '职业', '稀有度', '数量', '卡牌描述']):
                    all_cards_sheet.write(0, col_num, value, header_format)
                
                # 应用稀有度颜色格式到数据行
                for row_num, (name, class_name, rarity, count, description) in enumerate(all_cards_data):
                    cell_format = rarity_formats.get(rarity, default_format)
                    
                    # 写入数据并应用格式
                    all_cards_sheet.write(row_num + 1, 0, name, cell_format)
                    all_cards_sheet.write(row_num + 1, 1, class_name, cell_format)
                    all_cards_sheet.write(row_num + 1, 2, rarity, cell_format)
                    all_cards_sheet.write(row_num + 1, 3, count, cell_format)
                    all_cards_sheet.write(row_num + 1, 4, description, cell_format)
                
                # 统计工作表 - 按稀有度统计
                rarity_stats = defaultdict(int)
                total_cards = 0
                
                for class_cards in cards_by_class.values():
                    for card in class_cards:
                        rarity = card.get('rarity', 'COMMON')
                        count = card.get('count', 1)
                        rarity_stats[rarity] += count
                        total_cards += count
                
                # 创建稀有度统计数据
                rarity_data = []
                for rarity in ['LEGENDARY', 'EPIC', 'RARE', 'COMMON']:
                    if rarity in rarity_stats:
                        count = rarity_stats[rarity]
                        percentage = (count / total_cards) * 100 if total_cards > 0 else 0
                        rarity_data.append([rarity, count, f"{percentage:.2f}%"])
                
                # 创建稀有度统计工作表
                rarity_df = pd.DataFrame(rarity_data, columns=['稀有度', '数量', '百分比'])
                rarity_df.to_excel(writer, sheet_name='稀有度统计', index=False)
                
                rarity_sheet = writer.sheets['稀有度统计']
                rarity_sheet.set_column('A:C', 15)
                
                # 为稀有度统计应用格式
                for row_num, (rarity, _, _) in enumerate(rarity_data):
                    cell_format = rarity_formats.get(rarity, default_format)
                    for col_num in range(3):
                        rarity_sheet.write(row_num + 1, col_num, rarity_df.iloc[row_num, col_num], cell_format)
        
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
    
    def generate_pack_report(self, all_opened_cards, timestamp=None):
        """生成抽卡报告数据
        
        Args:
            all_opened_cards: 所有抽到的卡牌列表
            timestamp: 可选时间戳，用于文件名
            
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
        for card in cards_copy:
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