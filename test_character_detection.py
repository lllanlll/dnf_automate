#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色检测系统测试脚本
用于验证角色位置检测的准确性
"""

import cv2
import numpy as np
import mss
import time
from config import GAME_WINDOW, COLORS

def detect_character(screen):
    """检测角色位置（通过绿色HP条）"""
    # 转换为HSV
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # 绿色HP条检测（角色自己的）
    green_lower = np.array([40, 70, 70])
    green_upper = np.array([80, 255, 255])
    green_mask = cv2.inRange(hsv, green_lower, green_upper)
    
    # 查找轮廓
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    character_positions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 2000:  # HP条大小范围
            x, y, w, h = cv2.boundingRect(contour)
            # HP条通常在角色头顶，角色位置在HP条下方
            char_x = x + w // 2
            char_y = y + h + 30  # HP条下方30像素
            character_positions.append((char_x, char_y, area))
    
    return character_positions

def draw_character_detection(screen, positions):
    """在屏幕上绘制角色检测结果"""
    screen_copy = screen.copy()
    
    for i, (x, y, area) in enumerate(positions):
        # 绘制角色位置（红色圆圈）
        cv2.circle(screen_copy, (x, y), 15, (0, 0, 255), 3)
        # 绘制角色编号
        cv2.putText(screen_copy, f"Char{i+1}", (x-20, y-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        # 显示面积信息
        cv2.putText(screen_copy, f"A:{area}", (x-20, y+40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return screen_copy

def main():
    """主测试函数"""
    print("🔍 角色检测测试开始...")
    print("按下空格键进行截图检测，按ESC退出")
    
    sct = mss.mss()
    monitor = GAME_WINDOW
    
    while True:
        # 获取屏幕截图
        screenshot = sct.grab(monitor)
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        
        # 检测角色
        characters = detect_character(screen)
        
        # 绘制检测结果
        result_screen = draw_character_detection(screen, characters)
        
        # 添加信息显示
        info_text = f"检测到 {len(characters)} 个角色"
        cv2.putText(result_screen, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 显示结果
        cv2.imshow('角色检测测试', result_screen)
        
        # 等待按键
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC键
            break
        elif key == ord(' '):  # 空格键 - 打印详细信息
            print(f"\n检测结果:")
            print(f"角色数量: {len(characters)}")
            for i, (x, y, area) in enumerate(characters):
                print(f"角色{i+1}: 位置({x}, {y}), HP条面积: {area}")
        
        time.sleep(0.1)
    
    cv2.destroyAllWindows()
    print("测试结束")

if __name__ == "__main__":
    main()
