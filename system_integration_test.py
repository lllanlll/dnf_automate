#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNF机器人系统集成测试
测试所有核心功能的协同工作
"""

import cv2
import numpy as np
import mss
import time
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import GAME_WINDOW
from dnf_bot import DNFBot

def test_character_detection(bot, screen):
    """测试角色检测功能"""
    print("=== 测试角色检测 ===")
    
    char_pos = bot.get_character_position(screen)
    if char_pos:
        print(f"✅ 角色位置检测成功: {char_pos}")
        return True
    else:
        print("❌ 角色位置检测失败")
        return False

def test_monster_detection(bot, screen):
    """测试怪物检测功能"""
    print("=== 测试怪物检测 ===")
    
    monsters = bot.detect_monsters(screen)
    print(f"检测到 {len(monsters)} 个怪物")
    
    for i, monster in enumerate(monsters):
        print(f"  怪物{i+1}: {monster}")
    
    return len(monsters) > 0

def test_item_detection(bot, screen):
    """测试物品检测功能"""
    print("=== 测试物品检测 ===")
    
    items = bot.detect_items(screen)
    print(f"检测到 {len(items)} 个物品/金币")
    
    for i, item in enumerate(items):
        print(f"  物品{i+1}: {item}")
    
    return len(items) > 0

def test_door_detection(bot, screen):
    """测试传送门检测功能"""
    print("=== 测试传送门检测 ===")
    
    doors = bot.detect_doors(screen)
    print(f"检测到 {len(doors)} 个传送门")
    
    for i, door in enumerate(doors):
        print(f"  传送门{i+1}: {door}")
    
    return len(doors) > 0

def test_movement_calculation(bot, screen):
    """测试移动计算功能"""
    print("=== 测试移动计算 ===")
    
    char_pos = bot.get_character_position(screen)
    if not char_pos:
        print("❌ 无法获取角色位置，跳过移动测试")
        return False
    
    # 模拟一个目标位置
    target_x = char_pos[0] + 100
    target_y = char_pos[1] + 50
    
    print(f"当前角色位置: {char_pos}")
    print(f"目标位置: ({target_x}, {target_y})")
    
    # 计算移动方向
    diff_x = target_x - char_pos[0]
    diff_y = target_y - char_pos[1]
    distance = (diff_x**2 + diff_y**2)**0.5
    
    print(f"需要移动距离: {distance:.1f} 像素")
    print(f"移动方向: X={diff_x:+.0f}, Y={diff_y:+.0f}")
    
    return True

def main():
    """主测试函数"""
    print("🤖 DNF机器人系统集成测试")
    print("=" * 50)
    
    try:
        # 初始化机器人
        print("初始化DNF机器人...")
        bot = DNFBot()
        print("✅ 机器人初始化成功")
        
        # 截取屏幕
        print("截取游戏屏幕...")
        screen = bot.capture_screen()
        print(f"✅ 屏幕截取成功，尺寸: {screen.shape}")
        
        # 执行各项测试
        test_results = []
        
        test_results.append(("角色检测", test_character_detection(bot, screen)))
        test_results.append(("怪物检测", test_monster_detection(bot, screen)))
        test_results.append(("物品检测", test_item_detection(bot, screen)))
        test_results.append(("传送门检测", test_door_detection(bot, screen)))
        test_results.append(("移动计算", test_movement_calculation(bot, screen)))
        
        # 显示测试结果汇总
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print("=" * 50)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:12s} - {status}")
            if result:
                passed_tests += 1
        
        print("-" * 50)
        print(f"通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！系统准备就绪。")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  大部分测试通过，系统基本可用。")
        else:
            print("❌ 多项测试失败，需要检查系统配置。")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
