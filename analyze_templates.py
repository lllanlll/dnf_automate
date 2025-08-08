#!/usr/bin/env python3
"""
模板质量分析工具
帮助分析和优化模板图片质量
"""

import cv2
import numpy as np
import os
from dnf_bot import DNFBot

def analyze_template_quality():
    """分析模板质量"""
    print("🔬 模板质量分析工具")
    print("=" * 50)
    
    bot = DNFBot()
    templates_dir = os.path.join(bot.base_path, "templates")
    
    templates = ["item1.png", "item2.png", "door1.png", "door2.png", "door3.png", "door4.png"]
    
    for template_name in templates:
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            print(f"❌ {template_name} 不存在")
            continue
        
        template = cv2.imread(template_path)
        if template is None:
            print(f"❌ {template_name} 无法加载")
            continue
            
        print(f"\n📊 分析 {template_name}:")
        
        # 1. 基本信息
        h, w, c = template.shape
        print(f"   尺寸: {w}x{h} 像素")
        print(f"   文件大小: {os.path.getsize(template_path)} 字节")
        
        # 2. 图像质量分析
        gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # 计算对比度 (标准差)
        contrast = np.std(gray)
        print(f"   对比度: {contrast:.2f} (>30为好)")
        
        # 计算清晰度 (拉普拉斯变换的方差)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = np.var(laplacian)
        print(f"   清晰度: {sharpness:.2f} (>100为好)")
        
        # 计算亮度分布
        mean_brightness = np.mean(gray)
        print(f"   平均亮度: {mean_brightness:.2f} (50-200为好)")
        
        # 3. 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w) * 100
        print(f"   边缘密度: {edge_density:.2f}% (5-20%为好)")
        
        # 4. 颜色分析
        dominant_colors = analyze_dominant_colors(template)
        print(f"   主要颜色数量: {len(dominant_colors)}")
        
        # 5. 给出建议
        give_template_suggestions(template_name, contrast, sharpness, mean_brightness, edge_density)

def analyze_dominant_colors(image, k=5):
    """分析图像中的主要颜色"""
    data = image.reshape((-1, 3))
    data = np.float32(data)
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    return centers

def give_template_suggestions(name, contrast, sharpness, brightness, edge_density):
    """给出模板优化建议"""
    suggestions = []
    
    if contrast < 30:
        suggestions.append("对比度较低，建议增强对比度")
    
    if sharpness < 100:
        suggestions.append("清晰度不足，建议使用更清晰的图片")
    
    if brightness < 50 or brightness > 200:
        suggestions.append("亮度异常，建议调整到正常范围")
    
    if edge_density < 5:
        suggestions.append("边缘特征太少，建议选择更有特征的区域")
    elif edge_density > 20:
        suggestions.append("边缘过于复杂，建议简化模板")
    
    if suggestions:
        print(f"   💡 建议:")
        for suggestion in suggestions:
            print(f"      - {suggestion}")
    else:
        print(f"   ✅ 模板质量良好")

def create_optimal_template_guide():
    """创建最佳模板制作指南"""
    guide = """
🎯 制作高质量模板的指南

1. 模板尺寸建议：
   - 物品模板: 40x40 到 100x100 像素
   - 门模板: 80x80 到 150x150 像素
   - 避免过大或过小的模板

2. 模板内容要求：
   - 包含独特的视觉特征
   - 避免包含过多背景
   - 确保模板边界清晰
   - 选择有明显边缘和纹理的区域

3. 图像质量要求：
   - 高对比度 (标准差 > 30)
   - 清晰无模糊 (清晰度 > 100)
   - 适中亮度 (50-200)
   - 适量边缘特征 (5-20%)

4. 制作建议：
   - 在游戏中截取原始分辨率图片
   - 精确裁剪，只保留目标物体
   - 避免包含阴影和反光
   - 保存为PNG格式保持质量

5. 测试建议：
   - 在不同光照条件下测试
   - 确保在不同背景下都能识别
   - 调整阈值获得最佳平衡
   - 使用多个样本进行验证
"""
    
    with open("template_optimization_guide.txt", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print(f"\n📖 详细指南已保存到: template_optimization_guide.txt")

if __name__ == "__main__":
    analyze_template_quality()
    create_optimal_template_guide()
