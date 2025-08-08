#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动系统完整测试脚本
测试角色检测和移动到目标位置的功能
"""

import cv2
import numpy as np
import mss
import time
import math
from config import GAME_WINDOW, COLORS

def detect_character(screen):
    """检测角色位置（通过绿色HP条）"""
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # 绿色HP条检测
    green_lower = np.array([40, 70, 70])
    green_upper = np.array([80, 255, 255])
    green_mask = cv2.inRange(hsv, green_lower, green_upper)
    
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    character_positions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 2000:
            x, y, w, h = cv2.boundingRect(contour)
            char_x = x + w // 2
            char_y = y + h + 30
            character_positions.append((char_x, char_y, area))
    
    return character_positions

def get_character_position(screen, cache={}):
    """获取主角色位置（带缓存）"""
    current_time = time.time()
    
    # 缓存1秒内的结果
    if 'last_check' in cache and current_time - cache['last_check'] < 1.0:
        if 'position' in cache:
            return cache['position']
    
    characters = detect_character(screen)
    
    if characters:
        # 选择面积最大的HP条作为主角色
        main_char = max(characters, key=lambda x: x[2])
        position = (main_char[0], main_char[1])
        
        cache['position'] = position
        cache['last_check'] = current_time
        return position
    
    # 如果检测不到，返回屏幕中心
    height, width = screen.shape[:2]
    fallback_pos = (width // 2, height // 2)
    cache['position'] = fallback_pos
    cache['last_check'] = current_time
    return fallback_pos

def detect_monsters(screen):
    """检测怪物（红色HP条）"""
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # 红色HP条检测
    red_lower1 = np.array([0, 120, 120])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 120, 120])
    red_upper2 = np.array([180, 255, 255])
    
    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    monsters = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 50 < area < 1500:
            x, y, w, h = cv2.boundingRect(contour)
            monster_x = x + w // 2
            monster_y = y + h + 20
            monsters.append((monster_x, monster_y, area))
    
    return monsters

def calculate_distance(pos1, pos2):
    """计算两点距离"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def calculate_movement_direction(current_pos, target_pos):
    """计算移动方向"""
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < 10:
        return "到达目标", 0, 0
    
    # 归一化方向向量
    direction_x = dx / distance
    direction_y = dy / distance
    
    # 确定主要移动方向
    if abs(direction_x) > abs(direction_y):
        if direction_x > 0:
            return "向右", direction_x, direction_y
        else:
            return "向左", direction_x, direction_y
    else:
        if direction_y > 0:
            return "向下", direction_x, direction_y
        else:
            return "向上", direction_x, direction_y

def draw_test_info(screen, char_pos, monsters, target=None):
    """绘制测试信息"""
    screen_copy = screen.copy()
    
    # 绘制角色位置
    if char_pos:
        cv2.circle(screen_copy, char_pos, 20, (0, 255, 0), 3)
        cv2.putText(screen_copy, "Player", (char_pos[0]-25, char_pos[1]-25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 绘制怪物
    for i, (x, y, area) in enumerate(monsters):
        cv2.circle(screen_copy, (x, y), 15, (0, 0, 255), 2)
        cv2.putText(screen_copy, f"M{i+1}", (x-10, y-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # 计算距离
        if char_pos:
            distance = calculate_distance(char_pos, (x, y))
            cv2.putText(screen_copy, f"{distance:.0f}", (x-10, y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
    
    # 绘制目标位置和移动方向
    if target and char_pos:
        cv2.circle(screen_copy, target, 10, (255, 0, 255), 2)
        cv2.line(screen_copy, char_pos, target, (255, 255, 0), 2)
        
        direction, dx, dy = calculate_movement_direction(char_pos, target)
        distance = calculate_distance(char_pos, target)
        
        cv2.putText(screen_copy, f"目标: {direction}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(screen_copy, f"距离: {distance:.0f}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return screen_copy

def main():
    """主测试函数"""
    print("🎮 移动系统测试开始...")
    print("左键点击设置目标位置，右键清除目标")
    print("按ESC退出")
    
    sct = mss.mss()
    monitor = GAME_WINDOW
    target_pos = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal target_pos
        if event == cv2.EVENT_LBUTTONDOWN:
            target_pos = (x, y)
            print(f"设置目标位置: ({x}, {y})")
        elif event == cv2.EVENT_RBUTTONDOWN:
            target_pos = None
            print("清除目标位置")
    
    cv2.namedWindow('移动系统测试')
    cv2.setMouseCallback('移动系统测试', mouse_callback)
    
    while True:
        # 获取屏幕截图
        screenshot = sct.grab(monitor)
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        
        # 检测角色和怪物
        char_pos = get_character_position(screen)
        monsters = detect_monsters(screen)
        
        # 绘制测试信息
        result_screen = draw_test_info(screen, char_pos, monsters, target_pos)
        
        # 添加状态信息
        status_text = f"角色: {char_pos} | 怪物: {len(monsters)}"
        cv2.putText(result_screen, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 显示结果
        cv2.imshow('移动系统测试', result_screen)
        
        # 等待按键
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC键
            break
        
        time.sleep(0.1)
    
    cv2.destroyAllWindows()
    print("测试结束")

if __name__ == "__main__":
    main()
