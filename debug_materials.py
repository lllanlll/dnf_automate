#!/usr/bin/env python3
"""
材料检测调试工具
用于调试材料模板匹配问题
"""

import cv2
import numpy as np
import os
from dnf_bot import DNFBot

def debug_material_detection():
    """调试材料检测"""
    print("🔍 材料检测调试工具")
    print("=" * 40)
    
    bot = DNFBot()
    templates_dir = os.path.join(bot.base_path, "templates")
    
    print("正在截取当前屏幕...")
    screen = bot.capture_screen()
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    
    print("\n📊 模板匹配详细分析:")
    
    # 测试不同的阈值
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    
    for template_name in ["item1.png", "item2.png"]:
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            print(f"❌ {template_name} 不存在")
            continue
            
        template = cv2.imread(template_path, 0)
        if template is None:
            print(f"❌ {template_name} 无法加载")
            continue
            
        print(f"\n🎯 {template_name}:")
        print(f"   模板尺寸: {template.shape}")
        
        # 模板匹配
        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        print(f"   最高匹配度: {max_val:.3f}")
        print(f"   最高匹配位置: {max_loc}")
        
        # 测试不同阈值下的匹配数量
        for threshold in thresholds:
            locations = np.where(res >= threshold)
            matches = len(locations[0])
            print(f"   阈值 {threshold}: {matches} 个匹配")
        
        # 显示匹配结果（只打印，不显示窗口）
        print(f"   找到 {len(np.where(res >= 0.3)[0])} 个可能的匹配（阈值0.3）")
        
        # 显示最佳匹配位置的详细信息
        if max_val >= 0.3:
            h, w = template.shape
            print(f"   最佳匹配区域: ({max_loc[0]}, {max_loc[1]}) 到 ({max_loc[0]+w}, {max_loc[1]+h})")
        
        # 保存匹配结果图片（可选）
        display_screen = screen.copy()
        locations = np.where(res >= 0.3)
        for i, (y, x) in enumerate(zip(locations[0], locations[1])):
            if i < 5:  # 只显示前5个匹配
                confidence = res[y, x]
                h, w = template.shape
                cv2.rectangle(display_screen, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_screen, f"{confidence:.2f}", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 保存结果图片到文件
        output_path = f"debug_{template_name}_matches.jpg"
        cv2.imwrite(output_path, display_screen)
        print(f"   匹配结果已保存到: {output_path}")

if __name__ == "__main__":
    debug_material_detection()
