#!/usr/bin/env python3
"""
DNF Bot 模板测试工具
用于测试模板识别功能
"""

import cv2
import os
import sys
from dnf_bot import DNFBot

def test_templates():
    """测试模板文件"""
    print("🧪 DNF Bot 模板测试工具")
    print("=" * 40)
    
    bot = DNFBot()
    templates_dir = os.path.join(bot.base_path, "templates")
    
    # 检查模板文件
    print("📁 检查模板文件...")
    
    door_templates = ["door1.png", "door2.png", "door3.png", "door4.png"]
    item_templates = ["item1.png", "item2.png"]
    
    print("\n🚪 门模板检查:")
    for template in door_templates:
        path = os.path.join(templates_dir, template)
        if os.path.exists(path):
            # 检查图片是否可以正常加载
            img = cv2.imread(path)
            if img is not None:
                h, w = img.shape[:2]
                print(f"   ✅ {template} - 尺寸: {w}x{h}")
            else:
                print(f"   ❌ {template} - 无法加载图片")
        else:
            print(f"   ❌ {template} - 文件不存在")
    
    print("\n🎁 物品模板检查:")
    for template in item_templates:
        path = os.path.join(templates_dir, template)
        if os.path.exists(path):
            img = cv2.imread(path)
            if img is not None:
                h, w = img.shape[:2]
                print(f"   ✅ {template} - 尺寸: {w}x{h}")
            else:
                print(f"   ❌ {template} - 无法加载图片")
        else:
            print(f"   ❌ {template} - 文件不存在")
    
    print("\n🎮 模拟识别测试...")
    print("提示: 按 'q' 退出测试")
    
    try:
        while True:
            # 截取当前屏幕
            screen = bot.capture_screen()
            
            # 测试门识别
            doors = bot.detect_doors(screen)
            if doors:
                print(f"🚪 检测到 {len(doors)} 个门")
            
            # 测试物品识别
            items = bot.detect_items(screen)
            if items:
                print(f"🎁 检测到 {len(items)} 个物品")
            
            # 测试怪物识别
            monsters = bot.detect_monsters(screen)
            if monsters:
                print(f"👹 检测到 {len(monsters)} 个怪物")
            
            # 在屏幕上显示识别结果
            display_screen = screen.copy()
            
            # 绘制门（绿色圆圈）
            for door in doors:
                cv2.circle(display_screen, door, 20, (0, 255, 0), 3)
                cv2.putText(display_screen, "DOOR", (door[0]-20, door[1]-25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 绘制物品（蓝色圆圈）
            for item in items:
                cv2.circle(display_screen, item, 15, (255, 0, 0), 3)
                cv2.putText(display_screen, "ITEM", (item[0]-20, item[1]-25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # 绘制怪物（红色圆圈）
            for monster in monsters:
                cv2.circle(display_screen, monster, 10, (0, 0, 255), 3)
                cv2.putText(display_screen, "MON", (monster[0]-15, monster[1]-25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 2)
            
            # 显示结果
            display_screen = cv2.resize(display_screen, (960, 540))  # 缩放到一半大小
            cv2.imshow('DNF Bot - 模板识别测试 (按q退出)', display_screen)
            
            # 检查按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
    finally:
        cv2.destroyAllWindows()
        print("\n✅ 测试完成")

if __name__ == "__main__":
    test_templates()
