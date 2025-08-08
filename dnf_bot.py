import cv2
import pyautogui
import numpy as np
from PIL import Image
import time
import keyboard
from mss import mss
import os
import sys

class DNFBot:
    def __init__(self):
        # 禁用PyAutoGUI的安全功能
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
        
        # 屏幕截图对象
        self.sct = mss()
        
        # 获取程序运行目录（支持打包后的exe）
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            self.base_path = sys._MEIPASS
        else:
            # 如果是源码运行
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 游戏窗口区域 (需要根据实际调整)
        self.game_region = {"top": 0, "left": 0, "width": 1920, "height": 1080}
        
        # 技能键设置
        self.attack_key = 'a'  # 攻击键
        self.pickup_key = 'z'  # 拾取键
        
        # 运行状态
        self.running = False
        
    def capture_screen(self):
        """截取游戏屏幕"""
        screenshot = self.sct.grab(self.game_region)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    def find_template(self, screen, template_path, threshold=0.8):
        """模板匹配查找目标"""
        template = cv2.imread(template_path, 0)
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        for pt in zip(*locations[::-1]):
            matches.append((pt[0] + template.shape[1]//2, pt[1] + template.shape[0]//2))
        
        return matches
    
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
    
    def detect_items(self, screen):
        """检测掉落物品 - 基础版本"""
        # 物品通常有特定的光效或颜色
        # 这里需要根据实际游戏调整
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        
        # 检测金色物品（可根据需要调整）
        lower_gold = np.array([15, 100, 100])
        upper_gold = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_gold, upper_gold)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        items = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                x, y, w, h = cv2.boundingRect(contour)
                items.append((x + w//2, y + h//2))
        
        return items
    
    def detect_doors(self, screen):
        """检测传送门"""
        # 使用模板匹配或特征检测
        # 构建模板文件的完整路径
        template_path = os.path.join(self.base_path, "templates", "door.png")
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            print(f"警告: 模板文件不存在: {template_path}")
            return []
            
        doors = self.find_template(screen, template_path, 0.7)
        return doors
    
    def move_to_position(self, target_x, target_y):
        """移动角色到指定位置"""
        # 获取当前角色位置（通常在屏幕中央）
        center_x = self.game_region["width"] // 2
        center_y = self.game_region["height"] // 2
        
        # 计算移动方向
        diff_x = target_x - center_x
        diff_y = target_y - center_y
        
        # 根据差值按方向键
        if abs(diff_x) > 20:  # 阈值，避免微小移动
            if diff_x > 0:
                pyautogui.keyDown('right')
                time.sleep(0.3)
                pyautogui.keyUp('right')
            else:
                pyautogui.keyDown('left')
                time.sleep(0.3)
                pyautogui.keyUp('left')
        
        if abs(diff_y) > 20:
            if diff_y > 0:
                pyautogui.keyDown('down')
                time.sleep(0.3)
                pyautogui.keyUp('down')
            else:
                pyautogui.keyDown('up')
                time.sleep(0.3)
                pyautogui.keyUp('up')
    
    def attack_monsters(self, monsters):
        """攻击怪物"""
        if monsters:
            # 找最近的怪物
            center_x = self.game_region["width"] // 2
            center_y = self.game_region["height"] // 2
            
            closest_monster = min(monsters, 
                key=lambda m: ((m[0] - center_x)**2 + (m[1] - center_y)**2)**0.5)
            
            # 移动到怪物位置
            self.move_to_position(closest_monster[0], closest_monster[1])
            time.sleep(0.2)
            
            # 攻击
            pyautogui.press(self.attack_key)
            time.sleep(0.5)
    
    def collect_items(self, items):
        """收集物品"""
        for item in items:
            # 移动到物品位置
            self.move_to_position(item[0], item[1])
            time.sleep(0.2)
            
            # 拾取
            pyautogui.press(self.pickup_key)
            time.sleep(0.3)
    
    def go_to_next_room(self, doors):
        """前往下一个房间"""
        if doors:
            # 选择第一个门
            door = doors[0]
            self.move_to_position(door[0], door[1])
            time.sleep(0.5)
            
            # 进入门
            pyautogui.press('up')  # 或者是其他进门的键
            time.sleep(2)  # 等待加载
    
    def main_loop(self):
        """主循环"""
        print("DNF自动刷图开始运行...")
        print("按 F1 开始/暂停，按 F2 停止")
        
        while True:
            if keyboard.is_pressed('f1'):
                self.running = not self.running
                print(f"{'开始' if self.running else '暂停'}运行")
                time.sleep(0.5)
            
            if keyboard.is_pressed('f2'):
                print("停止运行")
                break
            
            if not self.running:
                time.sleep(0.1)
                continue
            
            try:
                # 截取屏幕
                screen = self.capture_screen()
                
                # 检测怪物
                monsters = self.detect_monsters(screen)
                if monsters:
                    print(f"发现 {len(monsters)} 个怪物")
                    self.attack_monsters(monsters)
                    continue
                
                # 检测物品
                items = self.detect_items(screen)
                if items:
                    print(f"发现 {len(items)} 个物品")
                    self.collect_items(items)
                    continue
                
                # 检测门
                doors = self.detect_doors(screen)
                if doors:
                    print("发现传送门，前往下一房间")
                    self.go_to_next_room(doors)
                    continue
                
                # 如果没有怪物、物品和门，检查是否需要重新开始
                # 这里可以添加"再来一次"的检测逻辑
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"错误: {e}")
                time.sleep(1)

if __name__ == "__main__":
    bot = DNFBot()
    bot.main_loop()
