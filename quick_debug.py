#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速调试测试 - 验证角色识别
"""

import cv2
import numpy as np
import mss
import time
import os
from datetime import datetime
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
    
    # 收集所有候选区域
    candidates = []
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
                    
                    candidate_info = {
                        'text_rect': (x, y, w, h),
                        'char_pos': (char_x, char_y),
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'score': score,
                        'distance_from_center': distance_from_center
                    }
                    candidates.append(candidate_info)
                    
                    if score > best_score:
                        best_score = score
                        best_candidate = candidate_info
    
    return best_candidate, candidates

def save_debug_screenshot(screen, char_result):
    """保存调试截图"""
    debug_screen = screen.copy()
    
    if char_result:
        best_candidate, all_candidates = char_result
        
        # 绘制最佳候选
        if best_candidate:
            x, y, w, h = best_candidate['text_rect']
            char_x, char_y = best_candidate['char_pos']
            
            # 绘制文字区域（绿色框）
            cv2.rectangle(debug_screen, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # 绘制推断的角色位置（红色大圆）
            cv2.circle(debug_screen, (char_x, char_y), 25, (0, 0, 255), 4)
            
            # 添加信息
            info_text = f"BEST: A={best_candidate['area']:.0f} S={best_candidate['score']:.1f}"
            cv2.putText(debug_screen, info_text, (x, y - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.putText(debug_screen, "DETECTED PLAYER", (char_x - 60, char_y - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 绘制所有候选（黄色框）
        for i, candidate in enumerate(all_candidates):
            if candidate == best_candidate:
                continue
                
            x, y, w, h = candidate['text_rect']
            char_x, char_y = candidate['char_pos']
            
            cv2.rectangle(debug_screen, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.circle(debug_screen, (char_x, char_y), 15, (0, 255, 255), 2)
            
            cv2.putText(debug_screen, f"C{i+1}", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # 添加时间戳
    timestamp = datetime.now().strftime("%H:%M:%S")
    cv2.putText(debug_screen, f"Time: {timestamp}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    if char_result and char_result[0]:
        char_pos = char_result[0]['char_pos']
        cv2.putText(debug_screen, f"Player Pos: {char_pos}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    else:
        cv2.putText(debug_screen, "Player: NOT DETECTED", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    cv2.putText(debug_screen, f"Total Candidates: {len(char_result[1]) if char_result else 0}", (10, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # 保存截图
    debug_folder = "debug_screenshots"
    if not os.path.exists(debug_folder):
        os.makedirs(debug_folder)
    
    filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(debug_folder, filename)
    cv2.imwrite(filepath, debug_screen)
    
    print(f"📸 调试截图已保存: {filename}")
    
    # 详细日志
    if char_result and char_result[0]:
        best = char_result[0]
        print(f"🎯 检测到的'角色'位置: {best['char_pos']}")
        print(f"📝 文字区域: {best['text_rect']}, 面积: {best['area']:.0f}")
        print(f"⭐ 得分: {best['score']:.2f}, 距离中心: {best['distance_from_center']:.0f}px")
    else:
        print("❌ 未检测到任何角色候选")
    
    print(f"📊 总候选数: {len(char_result[1]) if char_result else 0}")
    print("-" * 60)

def main():
    """主函数"""
    print("🔍 DNF角色识别调试测试")
    print("连续5次截图并保存调试信息...")
    
    sct = mss.mss()
    monitor = GAME_WINDOW
    
    for i in range(5):
        try:
            print(f"\n第 {i+1} 次检测:")
            
            # 截图
            screenshot = sct.grab(monitor)
            screen = np.array(screenshot)
            screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
            
            # 检测角色
            char_result = detect_character_by_green_text(screen)
            
            # 保存调试截图
            save_debug_screenshot(screen, char_result)
            
            time.sleep(2)  # 每2秒一次
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✅ 调试测试完成！请检查 debug_screenshots 文件夹中的截图。")

if __name__ == "__main__":
    main()
