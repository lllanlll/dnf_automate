"""
DNF Bot 配置文件
用于存储游戏相关的配置参数
"""

# 游戏窗口配置
GAME_WINDOW = {
    "top": 0,
    "left": 0, 
    "width": 1920,
    "height": 1080
}

# 按键配置
KEYS = {
    "attack": "a",      # 攻击键
    "pickup": "z",      # 拾取键
    "up": "up",         # 上移动
    "down": "down",     # 下移动
    "left": "left",     # 左移动
    "right": "right",   # 右移动
    "enter_door": "up"  # 进门键
}

# 颜色检测配置 (HSV格式)
COLORS = {
    # 怪物血条红色范围
    "monster_hp": {
        "lower1": [0, 120, 70],
        "upper1": [10, 255, 255],
        "lower2": [170, 120, 70], 
        "upper2": [180, 255, 255]
    },
    
    # 金色物品范围
    "gold_items": {
        "lower": [15, 100, 100],
        "upper": [35, 255, 255]
    }
}

# 检测阈值
THRESHOLDS = {
    "monster_area": 100,    # 怪物最小面积
    "item_area": 50,        # 物品最小面积
    "template_match": 0.7,  # 模板匹配阈值
    "movement_threshold": 20 # 移动阈值
}

# 时间延迟配置 (秒)
DELAYS = {
    "movement": 0.3,        # 移动延迟
    "attack": 0.5,          # 攻击延迟
    "pickup": 0.3,          # 拾取延迟
    "door_enter": 2.0,      # 进门等待时间
    "main_loop": 0.1        # 主循环延迟
}
