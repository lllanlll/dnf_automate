#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版角色检测测试
"""

import cv2
import numpy as np
import mss
import time
from config import GAME_WINDOW

def detect_character_by_green_text(screen):
    """检测绿色文字并推断角色位置"""
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # 绿色文字检测范围
    lower_green_text = np.array([35, 40, 40])
    upper_green_text = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green_text, upper_green_text)
    
    # 形态学操作
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_candidate = None
    best_score = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if 50 < area < 1500:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            if 1.5 < aspect_ratio < 8 and w > 20:
                char_x = x + w // 2
                char_y = y + h + 40
                
                if (100 < char_x < screen.shape[1] - 100 and 
                    100 < char_y < screen.shape[0] - 100):
                    
                    center_x = screen.shape[1] // 2
                    center_y = screen.shape[0] // 2
                    distance_from_center = ((char_x - center_x)**2 + (char_y - center_y)**2)**0.5
                    
                    score = area * 0.1 - distance_from_center * 0.01
                    
                    if score > best_score:
                        best_score = score
                        best_candidate = (char_x, char_y, x, y, w, h, area, aspect_ratio)
    
    return best_candidate

def main():
    """主测试函数"""
    print("🎮 简化版角色检测测试")
    print("按任意键退出")
    
    sct = mss.mss()
    monitor = GAME_WINDOW
    
    for i in range(10):  # 测试10次
        try:
            # 截图
            screenshot = sct.grab(monitor)
            screen = np.array(screenshot)
            screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
            
            # 检测角色
            result = detect_character_by_green_text(screen)
            
            if result:
                char_x, char_y, text_x, text_y, text_w, text_h, area, aspect_ratio = result
                print(f"第{i+1}次检测:")
                print(f"  文字区域: ({text_x}, {text_y}) 大小: {text_w}x{text_h}")
                print(f"  面积: {area:.0f}, 宽高比: {aspect_ratio:.2f}")
                print(f"  推断角色位置: ({char_x}, {char_y})")
            else:
                print(f"第{i+1}次检测: 未找到角色")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"错误: {e}")
            break
    
    print("测试完成")

if __name__ == "__main__":
    main()
