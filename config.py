"""
DNF Bot 配置文件
用于存储游戏相关的配置参数
"""

# 游戏窗口配置
GAME_WINDOW = {
    "top": 0,
    "left": 0, 
    "width": 2134,
    "height": 1200
}

# 按键配置
KEYS = {
    "attack": "x",      # 攻击键
    "pickup": "x",      # 拾取键
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
    
    # 金币范围 (黄色/金色)
    "gold_coins": {
        "lower": [15, 100, 100],
        "upper": [35, 255, 255]
    }
}

# 检测阈值
THRESHOLDS = {
    "monster_area": 100,        # 怪物最小面积
    "item_area": 50,            # 物品最小面积
    "door_template": 0.7,       # 门模板匹配阈值
    "item_template": 0.65,      # 物品模板匹配阈值 (提高精确度)
    "movement_threshold": 20,   # 移动阈值
    "duplicate_distance": 50    # 去重距离阈值（像素）
}

# 模板文件配置
TEMPLATES = {
    "doors": ["door1.png", "door2.png", "door3.png", "door4.png"],
    "items": ["item1.png", "item2.png"]
}

# 时间延迟配置 (秒)
DELAYS = {
    "movement": 0.3,        # 移动延迟
    "attack": 0.5,          # 攻击延迟
    "pickup": 0.3,          # 拾取延迟
    "door_enter": 2.0,      # 进门等待时间
    "main_loop": 0.1        # 主循环延迟
}
