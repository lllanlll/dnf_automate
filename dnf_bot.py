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

class DNFBot:
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
        """改进的多模板匹配，提高精确度"""
        all_matches = []
        
        for template_name in template_names:
            template_path = os.path.join(self.base_path, "templates", template_name)
            if not os.path.exists(template_path):
                print(f"警告: 模板文件不存在: {template_path}")
                continue
            
            matches = self.find_template_improved(screen, template_path, threshold)
            if matches:
                print(f"✅ 使用模板 {template_name} 找到 {len(matches)} 个目标")
                all_matches.extend(matches)
        
        # 去重：移除距离过近的重复检测
        if len(all_matches) > 1:
            unique_matches = self.remove_duplicate_matches(all_matches)
            return unique_matches
        
        return all_matches
    
    def find_template_improved(self, screen, template_path, threshold=0.7):
        """改进的单模板匹配"""
        try:
            # 加载模板（彩色）
            template = cv2.imread(template_path)
            if template is None:
                print(f"警告: 无法加载模板图片: {template_path}")
                return []
            
            # 获取模板尺寸
            h, w = template.shape[:2]
            
            # 方法1: 彩色模板匹配
            color_matches = self.match_color_template(screen, template, threshold)
            
            # 方法2: 灰度模板匹配（作为备用）
            gray_matches = self.match_gray_template(screen, template, threshold)
            
            # 合并结果，优先使用彩色匹配
            all_matches = color_matches if color_matches else gray_matches
            
            # 验证匹配质量
            validated_matches = []
            for match in all_matches:
                x, y, confidence = match
                if self.validate_match_region(screen, template, x, y):
                    validated_matches.append((x + w//2, y + h//2, confidence))
            
            return validated_matches
            
        except Exception as e:
            print(f"模板匹配出错: {e}")
            return []
    
    def match_color_template(self, screen, template, threshold):
        """彩色模板匹配"""
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= threshold)
        
        matches = []
        for y, x in zip(locations[0], locations[1]):
            confidence = res[y, x]
            matches.append((x, y, confidence))
        
        return matches
    
    def match_gray_template(self, screen, template, threshold):
        """灰度模板匹配"""
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        res = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= threshold)
        
        matches = []
        for y, x in zip(locations[0], locations[1]):
            confidence = res[y, x]
            matches.append((x, y, confidence))
        
        return matches
    
    def validate_match_region(self, screen, template, x, y):
        """验证匹配区域的质量"""
        try:
            h, w = template.shape[:2]
            
            # 检查边界
            if x + w > screen.shape[1] or y + h > screen.shape[0]:
                return False
            
            # 提取匹配区域
            region = screen[y:y+h, x:x+w]
            
            # 计算区域的特征（可以添加更多验证逻辑）
            # 例如：检查区域的亮度、对比度等
            mean_brightness = np.mean(region)
            
            # 简单验证：排除过暗或过亮的区域
            if mean_brightness < 10 or mean_brightness > 245:
                return False
            
            return True
            
        except Exception:
            return False
    
    def remove_duplicate_matches(self, matches):
        """移除重复的匹配结果"""
        if not matches:
            return []
        
        # 按confidence排序，保留最佳匹配
        sorted_matches = sorted(matches, key=lambda x: x[2] if len(x) > 2 else 0, reverse=True)
        
        unique_matches = []
        min_distance = self.config.THRESHOLDS["duplicate_distance"]
        
        for match in sorted_matches:
            x, y = match[0], match[1]
            is_duplicate = False
            
            for unique_match in unique_matches:
                ux, uy = unique_match[0], unique_match[1]
                distance = np.sqrt((x - ux)**2 + (y - uy)**2)
                
                if distance < min_distance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_matches.append(match)
        
        return unique_matches
    
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
        """检测掉落物品 - 目前仅检测金币"""
        # 只检测金币（通过颜色检测）
        coins = self.detect_coins(screen)
        return coins
    
    def detect_materials(self, screen):
        """检测材料物品 - 使用模板匹配"""
        materials = []
        
        # 使用物品模板匹配
        item_templates = ["item1.png", "item2.png"]
        template_items = self.find_multiple_templates(screen, item_templates, 
                                                     self.config.THRESHOLDS["item_template"])
        
        # 转换格式，只保留坐标
        for item in template_items:
            materials.append((item[0], item[1]))
            
        if materials:
            print(f"🎁 检测到 {len(materials)} 个材料")
        
        return materials
    
    def detect_coins(self, screen):
        """检测金币 - 使用颜色检测"""
        coins = []
        
        # 颜色检测金币（黄色/金色）
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        
        # 检测金币颜色范围
        lower_gold = np.array(self.config.COLORS["gold_coins"]["lower"])
        upper_gold = np.array(self.config.COLORS["gold_coins"]["upper"])
        mask = cv2.inRange(hsv, lower_gold, upper_gold)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.config.THRESHOLDS["item_area"]:
                x, y, w, h = cv2.boundingRect(contour)
                coins.append((x + w//2, y + h//2))
        
        if coins:
            print(f"💰 检测到 {len(coins)} 个金币")
        
        return coins
    
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
