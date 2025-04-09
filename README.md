# HearthStone_DrawMatch
# 炉石传说现开赛小助手

## 项目介绍
炉石传说现开赛小助手是一款针对炉石传说卡牌游戏的辅助工具，专注于帮助玩家进行现开赛的卡组构建和比赛准备。本工具提供了卡牌数据管理、卡牌图片获取、卡包模拟和卡组构建等核心功能，让玩家能够更好地进行现开赛准备和比赛。

## 主要功能

### 1. 卡牌数据管理 (hearthstone_data_manager.py)
- 从HearthstoneJSON获取完整的炉石传说卡牌数据
- 自动按照扩展包、职业和稀有度分类整理卡牌数据
- 提供结构化的JSON数据，方便程序调用和分析

### 2. 卡牌图片获取 (hearthstone_image_manager.py)(功能暂未完善)
- 支持批量下载不同类型的卡牌图片（原始图、艺术图、缩略图、渲染图等）
- 支持多语言版本的卡牌图片下载
- 自动管理图片存储目录，便于程序调用

### 3. 卡包模拟器 (hearthstone_pack_simulator.py)
- 模拟炉石传说卡包开启过程，遵循官方稀有度概率和保底机制
- 支持选择不同扩展包，自定义抽卡数量
- 生成详细的抽卡报告，包括稀有度分布和获得卡牌统计
- 可视化界面展示抽卡结果

### 4. 卡组构建器 (deck_builder.py)
- 基于已有卡牌构建炉石传说卡组
- 支持导入抽卡报告，基于已开出的卡牌构建卡组
- 提供卡牌搜索、排序、过滤等功能
- 支持导入/导出炉石传说官方卡组代码

## 使用说明
1. 首次运行前，请先使用数据管理器获取最新卡牌数据：
   - 运行 hearthstone_data_manager.py 获取卡牌数据
   - 运行 hearthstone_image_manager.py 下载所需卡牌图片（功能不完善，暂时不需要这一步）

2. 卡包模拟：
   - 运行 hearthstone_pack_simulator.py
   - 选择需要模拟的扩展包
   - 设置卡包数量
   - 点击"开始抽卡"
   - 可选择生成抽卡报告供后续卡组构建使用

3. 卡组构建：
   - 运行 deck_builder.py
   - 选择职业
   - 可导入抽卡报告数据
   - 通过双击添加/移除卡牌
   - 完成后可导出卡组代码

## 系统要求
- Python 3.6+
- PyQt5 图形界面库
- 网络连接（用于初始数据获取和图片下载）

## 许可证
本项目使用 MIT 许可证 - 详情请参阅 LICENSE 文件
