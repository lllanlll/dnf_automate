#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNF机器人调试版 - 带截图记录功能
用于调试角色识别问题
"""

import cv2
import pyautogui
import numpy as np
from PIL import Image
import time
import keyboard
from mss import mss
import os
import sys
import config
from datetime import datetime

class DNFBotDebug:
    def __init__(self):
        # 禁用PyAutoGUI的安全功能
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
        
        # 配置引用
        self.config = config
        
        # 屏幕截图对象
        self.sct = mss()
        
        # 获取程序运行目录（支持打包后的exe）
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            self.base_path = sys._MEIPASS
        else:
            # 如果是源码运行
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 游戏窗口区域（从配置文件读取）
        self.game_region = self.config.GAME_WINDOW
        
        # 技能键设置（从配置文件读取）
        self.attack_key = self.config.KEYS["attack"]
        self.pickup_key = self.config.KEYS["pickup"]
        
        # 运行状态
        self.running = False
        
        # 调试相关 - EXE兼容的路径设置
        if getattr(sys, 'frozen', False):
            # EXE运行时：保存到EXE文件所在目录
            exe_dir = os.path.dirname(sys.executable)
            self.debug_folder = os.path.join(exe_dir, "debug_screenshots")
        else:
            # 源码运行时：保存到脚本所在目录
            self.debug_folder = os.path.join(self.base_path, "debug_screenshots")
        
        # 创建调试文件夹
        try:
            if not os.path.exists(self.debug_folder):
                os.makedirs(self.debug_folder)
            print(f"📸 调试截图将保存到: {self.debug_folder}")
        except Exception as e:
            # 如果无法创建，则使用当前工作目录
            self.debug_folder = os.path.join(os.getcwd(), "debug_screenshots")
            if not os.path.exists(self.debug_folder):
                os.makedirs(self.debug_folder)
            print(f"⚠️  调试截图将保存到工作目录: {self.debug_folder}")
        
        self.last_debug_time = 0
        self.debug_interval = 10  # 10秒间隔
    
    def capture_screen(self):
        """截取游戏屏幕"""
        screenshot = self.sct.grab(self.game_region)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    def detect_character_by_green_text(self, screen):
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
        
        # 收集所有候选区域用于调试
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
    
    def detect_monsters(self, screen):
        """检测怪物 - 基础版本使用颜色检测"""
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        
        # 定义红色血条的HSV范围（怪物血条通常是红色）
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])
        
        # 创建掩码
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = mask1 + mask2
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        monsters = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # 过滤小的噪点
                x, y, w, h = cv2.boundingRect(contour)
                monsters.append((x + w//2, y + h//2))
        
        return monsters
    
    def save_debug_screenshot(self, screen, char_result, monsters):
        """保存调试截图，标注识别结果"""
        debug_screen = screen.copy()
        
        # 绘制角色检测结果
        if char_result:
            best_candidate, all_candidates = char_result
            
            # 绘制最佳候选
            if best_candidate:
                x, y, w, h = best_candidate['text_rect']
                char_x, char_y = best_candidate['char_pos']
                
                # 绘制文字区域（绿色框）
                cv2.rectangle(debug_screen, (x, y), (x + w, y + h), (0, 255, 0), 3)
                
                # 绘制推断的角色位置（红色大圆）
                cv2.circle(debug_screen, (char_x, char_y), 20, (0, 0, 255), 4)
                
                # 添加最佳候选信息
                info_text = f"BEST: A={best_candidate['area']:.0f} S={best_candidate['score']:.1f}"
                cv2.putText(debug_screen, info_text, (x, y - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.putText(debug_screen, "MAIN CHAR", (char_x - 40, char_y - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # 绘制所有候选（黄色框）
            for i, candidate in enumerate(all_candidates):
                if candidate == best_candidate:
                    continue
                    
                x, y, w, h = candidate['text_rect']
                char_x, char_y = candidate['char_pos']
                
                cv2.rectangle(debug_screen, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.circle(debug_screen, (char_x, char_y), 10, (0, 255, 255), 2)
                
                cv2.putText(debug_screen, f"C{i+1}", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # 绘制怪物
        for i, (mx, my) in enumerate(monsters):
            cv2.circle(debug_screen, (mx, my), 15, (255, 0, 0), 3)
            cv2.putText(debug_screen, f"M{i+1}", (mx - 10, my - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # 添加时间戳和统计信息
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(debug_screen, f"Time: {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        if char_result and char_result[0]:
            char_pos = char_result[0]['char_pos']
            cv2.putText(debug_screen, f"Char Pos: {char_pos}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.putText(debug_screen, f"Monsters: {len(monsters)}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.putText(debug_screen, f"Candidates: {len(char_result[1]) if char_result else 0}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 保存截图
        filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(self.debug_folder, filename)
        cv2.imwrite(filepath, debug_screen)
        
        print(f"📸 调试截图已保存: {filename}")
        
        # 详细日志
        if char_result and char_result[0]:
            best = char_result[0]
            print(f"🎯 最佳角色候选: 位置{best['char_pos']}, 面积{best['area']:.0f}, 得分{best['score']:.2f}")
        
        print(f"👹 检测到 {len(monsters)} 个怪物")
        print(f"📝 总候选数: {len(char_result[1]) if char_result else 0}")
        print("-" * 50)
    
    def main_loop(self):
        """主循环 - 调试版本"""
        print("🔍 DNF机器人调试模式启动...")
        print("按 F1 开始/暂停，按 F2 停止")
        print("每10秒自动保存一次调试截图")
        
        while True:
            if keyboard.is_pressed('f1'):
                self.running = not self.running
                print(f"{'🟢 开始' if self.running else '🟡 暂停'}运行")
                time.sleep(0.5)
            
            if keyboard.is_pressed('f2'):
                print("🔴 停止运行")
                break
            
            if not self.running:
                time.sleep(0.1)
                continue
            
            try:
                # 截取屏幕
                screen = self.capture_screen()
                
                # 检测角色
                char_result = self.detect_character_by_green_text(screen)
                
                # 检测怪物
                monsters = self.detect_monsters(screen)
                
                # 每10秒保存一次调试截图
                current_time = time.time()
                if current_time - self.last_debug_time >= self.debug_interval:
                    self.save_debug_screenshot(screen, char_result, monsters)
                    self.last_debug_time = current_time
                
                # 输出实时信息
                if char_result and char_result[0]:
                    char_pos = char_result[0]['char_pos']
                    print(f"🎯 角色位置: {char_pos}")
                else:
                    print("❌ 未检测到角色")
                
                time.sleep(1)  # 每秒检测一次
                
            except Exception as e:
                print(f"❌ 运行错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

if __name__ == "__main__":
    bot = DNFBotDebug()
    bot.main_loop()
