# DNF自动刷图机器人

这是一个基于Python开发的地下城与勇士(DNF)自动刷图工具。

## 功能特性

- 🎯 自动识别并攻击怪物
- 💎 自动拾取掉落物品
- 🚪 自动寻找并进入传送门
- 🎮 支持自定义按键设置
- ⚡ 实时屏幕识别

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保游戏窗口可见
2. 运行程序：
   ```bash
   python dnf_bot.py
   ```
3. 按键控制：
   - **F1**: 开始/暂停
   - **F2**: 停止程序

## 配置说明

### 游戏窗口设置
在 `dnf_bot.py` 中调整 `game_region` 参数：
```python
self.game_region = {"top": 0, "left": 0, "width": 1920, "height": 1080}
```

### 按键设置
```python
self.attack_key = 'a'  # 攻击键
self.pickup_key = 'z'  # 拾取键
```

## 模板图片

需要在 `templates/` 目录下放置以下模板图片：
- `door.png` - 传送门图片

## 注意事项

⚠️ **使用风险提醒**：
- 本工具仅供学习和研究使用
- 使用自动化工具可能违反游戏服务条款
- 请谨慎使用，风险自负

## 后续开发计划

- [ ] AI目标检测优化
- [ ] 路径规划算法
- [ ] OCR文字识别
- [ ] 强化学习策略
- [ ] GUI界面开发

## 技术栈

- OpenCV - 图像处理
- PyAutoGUI - 自动化控制
- NumPy - 数组处理
- PIL/Pillow - 图像处理
- MSS - 快速屏幕截图
- Keyboard - 键盘监听
