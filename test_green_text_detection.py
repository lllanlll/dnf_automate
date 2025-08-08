#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNF绿色文字检测测试脚本
专门用于测试角色名字/状态文字检测
"""

import cv2
import numpy as np
import mss
import time
from config import GAME_WINDOW

def detect_green_text(screen, debug=False):
    """检测绿色文字区域"""
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # 绿色文字检测范围
    lower_green_text = np.array([35, 40, 40])
    upper_green_text = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green_text, upper_green_text)
    
    # 形态学操作
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    if debug:
        cv2.imshow('绿色文字掩码', mask)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    text_regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 50 < area < 1500:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            if 1.5 < aspect_ratio < 8 and w > 20:
                # 角色位置：文字下方
                char_x = x + w // 2
                char_y = y + h + 40
                
                if (100 < char_x < screen.shape[1] - 100 and 
                    100 < char_y < screen.shape[0] - 100):
                    
                    text_regions.append({
                        'text_rect': (x, y, w, h),
                        'char_pos': (char_x, char_y),
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
    
    return text_regions

def draw_detection_results(screen, text_regions):
    """绘制检测结果"""
    result = screen.copy()
    
    for i, region in enumerate(text_regions):
        x, y, w, h = region['text_rect']
        char_x, char_y = region['char_pos']
        area = region['area']
        aspect_ratio = region['aspect_ratio']
        
        # 绘制文字区域边框（绿色）
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 绘制角色位置（红色圆圈）
        cv2.circle(result, (char_x, char_y), 15, (0, 0, 255), 3)
        
        # 添加信息标签
        label = f"T{i+1}: A={area:.0f}, R={aspect_ratio:.1f}"
        cv2.putText(result, label, (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 角色位置标签
        cv2.putText(result, f"Char{i+1}", (char_x - 25, char_y - 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    return result

def main():
    """主测试函数"""
    print("🔍 DNF绿色文字检测测试")
    print("按空格键显示详细信息")
    print("按'd'键开启/关闭调试模式")
    print("按ESC退出")
    
    sct = mss.mss()
    monitor = GAME_WINDOW
    debug_mode = False
    
    while True:
        # 截图
        screenshot = sct.grab(monitor)
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        
        # 检测绿色文字
        text_regions = detect_green_text(screen, debug_mode)
        
        # 绘制结果
        result_screen = draw_detection_results(screen, text_regions)
        
        # 状态信息
        status = f"检测到 {len(text_regions)} 个文字区域 | 调试模式: {'开' if debug_mode else '关'}"
        cv2.putText(result_screen, status, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 显示帮助信息
        help_text = "空格=详情 | d=调试 | ESC=退出"
        cv2.putText(result_screen, help_text, (10, result_screen.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        cv2.imshow('DNF绿色文字检测', result_screen)
        
        # 按键处理
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord(' '):  # 空格 - 详细信息
            print(f"\n=== 检测结果详情 ===")
            print(f"发现 {len(text_regions)} 个候选文字区域:")
            for i, region in enumerate(text_regions):
                x, y, w, h = region['text_rect']
                char_x, char_y = region['char_pos']
                print(f"文字区域{i+1}:")
                print(f"  位置: ({x}, {y}), 大小: {w}x{h}")
                print(f"  面积: {region['area']:.0f}, 宽高比: {region['aspect_ratio']:.2f}")
                print(f"  推断角色位置: ({char_x}, {char_y})")
                print()
        elif key == ord('d'):  # d键 - 调试模式
            debug_mode = not debug_mode
            print(f"调试模式: {'开启' if debug_mode else '关闭'}")
        
        time.sleep(0.1)
    
    cv2.destroyAllWindows()
    print("测试结束")

if __name__ == "__main__":
    main()
