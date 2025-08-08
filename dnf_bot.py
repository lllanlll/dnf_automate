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
        try:
            template = cv2.imread(template_path, 0)
            if template is None:
                print(f"警告: 无法加载模板图片: {template_path}")
                return []
                
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            
            matches = []
            for pt in zip(*locations[::-1]):
                matches.append((pt[0] + template.shape[1]//2, pt[1] + template.shape[0]//2))
            
            return matches
        except Exception as e:
            print(f"模板匹配错误 {template_path}: {e}")
            return []
    
    def find_multiple_templates(self, screen, template_names, threshold=0.7):
        """查找多个模板，返回所有匹配结果"""
        all_matches = []
        for template_name in template_names:
            template_path = os.path.join(self.base_path, "templates", template_name)
            if os.path.exists(template_path):
                matches = self.find_template(screen, template_path, threshold)
                if matches:
                    # 为每个匹配添加模板名称标识
                    for match in matches:
                        all_matches.append((match[0], match[1], template_name))
                    print(f"✅ 使用模板 {template_name} 找到 {len(matches)} 个目标")
            else:
                print(f"⚠️ 模板文件不存在: {template_path}")
        
        return all_matches
    
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
        """检测掉落物品 - 支持模板匹配和颜色检测"""
        all_items = []
        
        # 方法1: 使用物品模板匹配
        item_templates = ["item1.png", "item2.png"]
        template_items = self.find_multiple_templates(screen, item_templates, 0.6)
        
        # 转换格式，只保留坐标
        for item in template_items:
            all_items.append((item[0], item[1]))
            
        if template_items:
            print(f"🎁 通过模板匹配找到 {len(template_items)} 个物品")
        
        # 方法2: 颜色检测作为补充（检测金色物品）
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        
        # 检测金色物品（可根据需要调整）
        lower_gold = np.array([15, 100, 100])
        upper_gold = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_gold, upper_gold)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        color_items = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                x, y, w, h = cv2.boundingRect(contour)
                color_items.append((x + w//2, y + h//2))
        
        if color_items:
            print(f"💰 通过颜色检测找到 {len(color_items)} 个金色物品")
            all_items.extend(color_items)
        
        # 去重：合并距离很近的物品（可能是同一个物品被两种方法都检测到）
        if len(all_items) > 1:
            unique_items = []
            for item in all_items:
                is_duplicate = False
                for existing in unique_items:
                    distance = ((item[0] - existing[0])**2 + (item[1] - existing[1])**2)**0.5
                    if distance < 30:  # 30像素内认为是同一个物品
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_items.append(item)
            return unique_items
        
        return all_items
    
    def detect_doors(self, screen):
        """检测传送门 - 支持多种门的模板"""
        # 支持4种不同的门模板
        door_templates = ["door1.png", "door2.png", "door3.png", "door4.png"]
        door_matches = self.find_multiple_templates(screen, door_templates, 0.7)
        
        if door_matches:
            print(f"🚪 找到 {len(door_matches)} 个传送门")
            # 打印每种门的匹配结果
            door_types = {}
            for door in door_matches:
                door_type = door[2]  # 模板文件名
                if door_type not in door_types:
                    door_types[door_type] = 0
                door_types[door_type] += 1
            
            for door_type, count in door_types.items():
                print(f"   - {door_type}: {count} 个")
        
        # 返回坐标列表（去除模板名称）
        return [(door[0], door[1]) for door in door_matches]
    
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
                    print(f"👹 发现 {len(monsters)} 个怪物，开始攻击...")
                    self.attack_monsters(monsters)
                    continue
                
                # 检测物品
                items = self.detect_items(screen)
                if items:
                    print(f"🎁 发现 {len(items)} 个物品，开始拾取...")
                    self.collect_items(items)
                    continue
                
                # 检测门
                doors = self.detect_doors(screen)
                if doors:
                    print(f"🚪 发现 {len(doors)} 个传送门，前往下一房间...")
                    self.go_to_next_room(doors)
                    continue
                
                # 如果没有怪物、物品和门，检查是否需要重新开始
                # 这里可以添加"再来一次"的检测逻辑
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ 运行错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

if __name__ == "__main__":
    bot = DNFBot()
    bot.main_loop()
