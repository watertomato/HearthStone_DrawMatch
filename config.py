import os
from PyQt5.QtGui import QColor

# 稀有度概率设置
RARITY_PROBABILITIES = {
    'COMMON': 0.7162,    # 普通: 71.62%
    'RARE': 0.2266,      # 稀有: 22.66%
    'EPIC': 0.0448,     # 史诗: 4.48%
    'LEGENDARY': 0.0124 # 传说: 1.24%
}

# 稀有度颜色设置 - Qt颜色
RARITY_COLORS = {
    'LEGENDARY': QColor("#FF7D0A"),  # 橙色
    'EPIC': QColor("#A335EE"),       # 紫色
    'RARE': QColor("#0070DD"),       # 蓝色
    'COMMON': QColor("#888888")      # 灰色
}

# matplotlib绘图颜色
PLOT_COLORS = {
    'LEGENDARY': '#FF7D0A',  # 橙色
    'EPIC': '#A335EE',       # 紫色
    'RARE': '#0070DD',       # 蓝色
    'COMMON': '#888888'      # 灰色
}

# Excel报表颜色 - 淡色系
EXCEL_COLORS = {
    'LEGENDARY': '#FFD8B0',  # 淡橙色
    'EPIC': '#E0C8F5',       # 淡紫色
    'RARE': '#B8DEFF',       # 淡蓝色
    'COMMON': '#E0E0E0'      # 淡灰色
}

# 稀有度标记
RARITY_TAGS = {
    'LEGENDARY': "【橙】",
    'EPIC': "【紫】",
    'RARE': "【蓝】",
    'COMMON': "【灰】"
}

# 稀有度名称中文映射
RARITY_NAMES = {
    'LEGENDARY': '传说',
    'EPIC': '史诗',
    'RARE': '稀有',
    'COMMON': '普通'
}

# 职业映射
CLASS_NAMES = {
    'MAGE': '法师',
    'HUNTER': '猎人',
    'PALADIN': '圣骑士',
    'WARRIOR': '战士',
    'DRUID': '德鲁伊',
    'WARLOCK': '术士',
    'SHAMAN': '萨满',
    'ROGUE': '潜行者',
    'PRIEST': '牧师',
    'DEMONHUNTER': '恶魔猎手',
    'DEATHKNIGHT': '死亡骑士',
    'NEUTRAL': '中立'
}

# 扩展包名称映射表
SET_NAMES = {
    # 最新扩展包
    'EMERALD_DREAM': '漫游翡翠梦境',
    'SPACE': '深暗领域',
    'TITANS': '泰坦',
    'BATTLE_OF_THE_BANDS': '传奇音乐节',
    'RETURN_OF_THE_LICH_KING': '巫妖王的进军',
    'WHIZBANGS_WORKSHOP': '威兹班的工坊',
    'FESTIVAL_OF_LEGENDS': '传说节日',
    
    # 其他扩展包
    'THE_BARRENS': '贫瘠之地的锤炼',
    'SCHOLOMANCE': '通灵学院',
    'DARKMOON_FAIRE': '疯狂的暗月马戏团',
    'STORMWIND': '暴风城下的集结',
    'THE_SUNKEN_CITY': '探寻沉没之城',
    'REVENDRETH': '纳斯利亚堡的悬案',
    'ALTERAC_VALLEY': '奥特兰克的决裂',
    'BOOMSDAY': '砰砰计划',
    'DRAGONS': '巨龙降临',
    'BLACK_TEMPLE': '外域的灰烬',
    'WILD_WEST': '决战荒芜之地',
    'TROLL': '拉斯塔哈的大乱斗',
    'ULDUM': '奥丹姆奇兵',
    'DALARAN': '暗影崛起',
    'UNGORO': '勇闯安戈洛',
    'ICECROWN': '冰封王座的骑士',
    'GANGS': '龙争虎斗加基森',
    'KARA': '卡拉赞之夜',
    'OG': '上古之神的低语',
    'TGT': '冠军的试炼',
    'GVG': '地精大战侏儒',
    'NAXX': '纳克萨玛斯的诅咒',
    'BRM': '黑石山的火焰',
    'LOE': '探险者协会',
    'CORE': '核心',
    'EXPERT1': '经典卡牌',
    'VANILLA': '怀旧',
    'DEMON_HUNTER_INITIATE': '恶魔猎手新兵',
    'PATH_OF_ARTHAS': '阿尔萨斯之路',
    'LEGACY': '传统',
    'WONDERS': '诸多奇迹',
    'ISLAND_VACATION': '胜地历险记'
}

# 保底机制设置
GUARANTEE_RARE_OR_HIGHER = True  # 每包至少一张稀有或更高
LEGENDARY_PITY_TIMER = 40        # 每40包必出一张传说

# 数据路径设置
DATA_PATH = os.path.join("炉石卡牌分类")
REPORTS_DIR = os.path.join("抽卡报告") 