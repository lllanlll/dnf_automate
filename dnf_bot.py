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
        
        # 调试功能 - 确保EXE和源码都能正确保存调试文件
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
            print(f"📸 调试截图保存路径: {self.debug_folder}")
        except Exception as e:
            # 如果无法创建，则使用当前工作目录
            self.debug_folder = os.path.join(os.getcwd(), "debug_screenshots")
            if not os.path.exists(self.debug_folder):
                os.makedirs(self.debug_folder)
            print(f"⚠️  调试截图保存到工作目录: {self.debug_folder}")
        
        self.last_debug_time = 0
        self.debug_interval = 10  # 10秒间隔
        
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
    
    def detect_character(self, screen):
        """检测角色位置 - 通过血条/蓝条定位"""
        # 方法1: 检测角色血条 (通常在角色头顶或左上角UI)
        character_pos = self.detect_character_by_hp_bar(screen)
        if character_pos:
            return character_pos
        
        # 方法2: 检测特殊UI元素 (如技能冷却圈等)
        ui_pos = self.detect_character_by_ui(screen)
        if ui_pos:
            return ui_pos
        
        # 方法3: 回退到屏幕中心 (原始方法)
        center_x = self.game_region["width"] // 2
        center_y = self.game_region["height"] // 2
        return (center_x, center_y)
    
    def detect_character_by_hp_bar(self, screen):
        """通过绿色文字检测角色位置（DNF特定方法）"""
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # 检测绿色文字（角色名字或状态文字）
            # DNF中角色附近通常有绿色的文字信息
            lower_green_text = np.array([35, 40, 40])   # 绿色文字下限
            upper_green_text = np.array([85, 255, 255]) # 绿色文字上限
            
            mask = cv2.inRange(hsv, lower_green_text, upper_green_text)
            
            # 形态学操作，连接文字区域
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 寻找合适的绿色文字区域
            best_candidate = None
            best_score = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 1500:  # 文字区域面积范围
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 文字区域特征判断
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # 优先选择较长的文字区域（可能是角色名或状态）
                    if 1.5 < aspect_ratio < 8 and w > 20:  # 文字应该是横向的
                        # 角色位置：文字下方一定距离
                        char_x = x + w // 2
                        char_y = y + h + 40  # 文字下方40像素作为角色中心
                        
                        # 验证位置是否在游戏区域内
                        if (100 < char_x < screen.shape[1] - 100 and 
                            100 < char_y < screen.shape[0] - 100):
                            
                            # 计算得分（面积越大、位置越居中得分越高）
                            center_x = screen.shape[1] // 2
                            center_y = screen.shape[0] // 2
                            distance_from_center = ((char_x - center_x)**2 + (char_y - center_y)**2)**0.5
                            
                            # 得分 = 面积权重 - 距离中心的惩罚
                            score = area * 0.1 - distance_from_center * 0.01
                            
                            if score > best_score:
                                best_score = score
                                best_candidate = (char_x, char_y)
            
            if best_candidate:
                print(f"✅ 通过绿色文字检测到角色位置: {best_candidate}")
                return best_candidate
            
            return None
            
        except Exception as e:
            print(f"绿色文字检测错误: {e}")
            return None
    
    def detect_character_by_ui(self, screen):
        """通过DNF特有的UI元素检测角色位置"""
        try:
            # 方法1: 检测角色周围的绿色特效光圈
            char_pos_1 = self.detect_character_by_green_aura(screen)
            if char_pos_1:
                return char_pos_1
            
            # 方法2: 检测角色移动时的绿色路径指示
            char_pos_2 = self.detect_character_by_movement_indicator(screen)
            if char_pos_2:
                return char_pos_2
            
            # 方法3: 检测角色的绿色装备光效
            char_pos_3 = self.detect_character_by_equipment_glow(screen)
            if char_pos_3:
                return char_pos_3
            
            return None
            
        except Exception as e:
            print(f"UI检测错误: {e}")
            return None
    
    def detect_character_by_green_aura(self, screen):
        """检测角色周围的绿色光圈/特效"""
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # 检测明亮的绿色光效
            lower_aura = np.array([40, 100, 100])
            upper_aura = np.array([80, 255, 255])
            
            mask = cv2.inRange(hsv, lower_aura, upper_aura)
            
            # 寻找圆形或椭圆形的光效
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 3000:  # 光圈面积范围
                    # 检查形状是否接近圆形
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        
                        if circularity > 0.3:  # 接近圆形
                            # 计算中心点
                            M = cv2.moments(contour)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                
                                # 验证位置合理性
                                if (150 < cx < screen.shape[1] - 150 and 
                                    150 < cy < screen.shape[0] - 150):
                                    print(f"✅ 通过绿色光圈检测到角色: ({cx}, {cy})")
                                    return (cx, cy)
            
            return None
            
        except Exception as e:
            print(f"光圈检测错误: {e}")
            return None
    
    def detect_character_by_movement_indicator(self, screen):
        """检测角色移动时的绿色路径指示器"""
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # 检测移动路径的绿色指示
            lower_path = np.array([35, 80, 80])
            upper_path = np.array([85, 255, 255])
            
            mask = cv2.inRange(hsv, lower_path, upper_path)
            
            # 寻找线条状的绿色元素
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            path_points = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 20 < area < 500:  # 路径点面积
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 路径点通常是小的圆形或正方形
                    if 0.5 < w/h < 2.0 and max(w, h) < 30:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        path_points.append((center_x, center_y))
            
            # 如果有多个路径点，找到最密集的区域作为角色位置
            if len(path_points) >= 2:
                # 计算路径点的重心
                avg_x = sum(p[0] for p in path_points) // len(path_points)
                avg_y = sum(p[1] for p in path_points) // len(path_points)
                
                print(f"✅ 通过移动路径检测到角色: ({avg_x}, {avg_y})")
                return (avg_x, avg_y)
            
            return None
            
        except Exception as e:
            print(f"移动指示器检测错误: {e}")
            return None
    
    def detect_character_by_equipment_glow(self, screen):
        """检测角色装备的绿色光效"""
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # 检测装备的绿色光效（通常比较明亮）
            lower_glow = np.array([45, 120, 150])
            upper_glow = np.array([75, 255, 255])
            
            mask = cv2.inRange(hsv, lower_glow, upper_glow)
            
            # 形态学操作，连接附近的光效
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 2000:  # 装备光效面积
                    # 计算重心
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        # 验证位置
                        if (100 < cx < screen.shape[1] - 100 and 
                            100 < cy < screen.shape[0] - 100):
                            print(f"✅ 通过装备光效检测到角色: ({cx}, {cy})")
                            return (cx, cy)
            
            return None
            
        except Exception as e:
            print(f"装备光效检测错误: {e}")
            return None
    
    def get_character_position(self, screen):
        """获取角色当前位置 (缓存优化)"""
        if not hasattr(self, '_last_char_pos'):
            self._last_char_pos = None
            self._char_pos_frame_count = 0
        
        # 每3帧更新一次角色位置 (性能优化)
        self._char_pos_frame_count += 1
        if self._char_pos_frame_count >= 3 or self._last_char_pos is None:
            self._last_char_pos = self.detect_character(screen)
            self._char_pos_frame_count = 0
        
        return self._last_char_pos
    
    def move_to_position(self, target_x, target_y, screen):
        """移动角色到指定位置"""
        # 获取角色当前位置
        char_pos = self.get_character_position(screen)
        char_x, char_y = char_pos
        
        # 计算需要移动的方向
        diff_x = target_x - char_x
        diff_y = target_y - char_y
        
        # 计算距离
        distance = (diff_x**2 + diff_y**2)**0.5
        
        # 如果距离太近，不需要移动
        if distance < self.config.THRESHOLDS["movement_threshold"]:
            return True
        
        print(f"🚶 角色移动: ({char_x}, {char_y}) -> ({target_x}, {target_y}), 距离: {distance:.1f}")
        
        # 根据方向移动 (优先移动距离更大的轴)
        if abs(diff_x) > abs(diff_y):
            if diff_x > 0:
                pyautogui.keyDown('right')
                time.sleep(self.config.DELAYS["movement"])
                pyautogui.keyUp('right')
            else:
                pyautogui.keyDown('left')
                time.sleep(self.config.DELAYS["movement"])
                pyautogui.keyUp('left')
        else:
            if diff_y > 0:
                pyautogui.keyDown('down')
                time.sleep(self.config.DELAYS["movement"])
                pyautogui.keyUp('down')
            else:
                pyautogui.keyDown('up')
                time.sleep(self.config.DELAYS["movement"])
                pyautogui.keyUp('up')
        
        return False
    
    def attack_monsters(self, monsters, screen):
        """攻击怪物"""
        if monsters:
            # 获取角色位置
            char_pos = self.get_character_position(screen)
            char_x, char_y = char_pos
            
            # 找最近的怪物
            closest_monster = min(monsters, 
                key=lambda m: ((m[0] - char_x)**2 + (m[1] - char_y)**2)**0.5)
            
            # 计算距离
            distance = ((closest_monster[0] - char_x)**2 + (closest_monster[1] - char_y)**2)**0.5
            
            # 如果距离较远，先移动过去
            if distance > 100:  # 100像素以外才移动
                moved = self.move_to_position(closest_monster[0], closest_monster[1], screen)
                if not moved:  # 还在移动中
                    return
            
            # 攻击
            print(f"⚔️ 攻击怪物，距离: {distance:.1f}")
            pyautogui.press(self.config.KEYS["attack"])
            time.sleep(self.config.DELAYS["attack"])
    
    def collect_items(self, items, screen):
        """收集物品"""
        for item in items:
            # 移动到物品位置
            moved = self.move_to_position(item[0], item[1], screen)
            if moved:  # 已经到达物品位置
                # 拾取
                print(f"💰 拾取物品")
                pyautogui.press(self.config.KEYS["pickup"])
                time.sleep(self.config.DELAYS["pickup"])
    
    def go_to_next_room(self, doors, screen):
        """前往下一个房间"""
        if doors:
            # 选择第一个门
            door = doors[0]
            
            # 移动到门的位置
            moved = self.move_to_position(door[0], door[1], screen)
            if moved:  # 已经到达门的位置
                # 进门
                print(f"🚪 进入传送门")
                pyautogui.press(self.config.KEYS["enter_door"])
                time.sleep(self.config.DELAYS["door_enter"])
    
    def save_debug_screenshot(self, screen, char_pos, monsters, items, doors):
        """保存调试截图，标注识别结果"""
        debug_screen = screen.copy()
        
        # 绘制角色位置（红色大圆）
        if char_pos:
            cv2.circle(debug_screen, char_pos, 25, (0, 0, 255), 4)
            cv2.putText(debug_screen, "PLAYER", (char_pos[0] - 30, char_pos[1] - 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # 绘制怪物（蓝色圆）
        for i, monster in enumerate(monsters):
            cv2.circle(debug_screen, monster, 18, (255, 0, 0), 3)
            cv2.putText(debug_screen, f"M{i+1}", (monster[0] - 10, monster[1] - 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # 绘制物品（黄色圆）
        for i, item in enumerate(items):
            cv2.circle(debug_screen, item, 12, (0, 255, 255), 2)
            cv2.putText(debug_screen, f"I{i+1}", (item[0] - 8, item[1] - 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        # 绘制传送门（绿色方框）
        for i, door in enumerate(doors):
            cv2.rectangle(debug_screen, (door[0]-20, door[1]-20), (door[0]+20, door[1]+20), (0, 255, 0), 3)
            cv2.putText(debug_screen, f"D{i+1}", (door[0] - 10, door[1] - 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 添加时间戳和统计信息
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(debug_screen, f"Time: {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        if char_pos:
            cv2.putText(debug_screen, f"Player: {char_pos}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            cv2.putText(debug_screen, "Player: NOT FOUND", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        cv2.putText(debug_screen, f"Monsters: {len(monsters)}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(debug_screen, f"Items: {len(items)}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(debug_screen, f"Doors: {len(doors)}", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 保存截图
        filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(self.debug_folder, filename)
        cv2.imwrite(filepath, debug_screen)
        
        print(f"📸 调试截图已保存: {filename}")
        if char_pos:
            print(f"🎯 当前识别的角色位置: {char_pos}")
        else:
            print("❌ 未识别到角色位置")
        print(f"👹 怪物数: {len(monsters)}, 💰 物品数: {len(items)}, 🚪 门数: {len(doors)}")
        print("-" * 60)
    
    def main_loop(self):
        """主循环"""
        print("DNF自动刷图开始运行...")
        print("按 F1 开始/暂停，按 F2 停止")
        print(f"📸 调试截图将每10秒保存到: {self.debug_folder}")
        
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
                
                # 获取角色位置（用于调试）
                char_pos = self.get_character_position(screen)
                
                # 检测怪物
                monsters = self.detect_monsters(screen)
                if monsters:
                    print(f"👹 发现 {len(monsters)} 个怪物，开始攻击...")
                    self.attack_monsters(monsters, screen)
                    continue
                
                # 检测物品
                items = self.detect_items(screen)
                if items:
                    print(f"💰 发现 {len(items)} 个金币，开始拾取...")
                    self.collect_items(items, screen)
                    continue
                
                # 检测门
                doors = self.detect_doors(screen)
                if doors:
                    print(f"🚪 发现 {len(doors)} 个传送门，前往下一房间...")
                    self.go_to_next_room(doors, screen)
                    continue
                
                # 定期保存调试截图（每10秒）
                current_time = time.time()
                if current_time - self.last_debug_time >= self.debug_interval:
                    self.save_debug_screenshot(screen, char_pos, monsters, items, doors)
                    self.last_debug_time = current_time
                
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
