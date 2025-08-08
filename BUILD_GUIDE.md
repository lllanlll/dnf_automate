# DNF自动刷图工具 - 打包说明

## 打包方法

### 方法一：自动打包（推荐）

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   pip install -r build_requirements.txt
   ```

2. **运行打包脚本**：
   ```bash
   # Windows
   build.bat
   
   # 或者手动运行
   pyinstaller --onefile --console --name "DNF自动刷图" dnf_bot.py
   ```

3. **打包结果**：
   - 可执行文件位置: `dist/DNF自动刷图.exe`
   - 文件大小约: 50-100MB

### 方法二：使用spec文件（高级）

```bash
pyinstaller dnf_bot.spec
```

### 方法三：使用auto-py-to-exe（GUI界面）

1. 安装工具：
   ```bash
   pip install auto-py-to-exe
   ```

2. 启动GUI：
   ```bash
   auto-py-to-exe
   ```

3. 配置选项：
   - **Script Location**: 选择 `dnf_bot.py`
   - **Onefile**: 选择 "One File"
   - **Console Window**: 选择 "Console Based"
   - **Additional Files**: 添加 `templates` 文件夹

## 打包后的目录结构

```
📁 发布包/
├── 📄 DNF自动刷图.exe     # 主程序
├── 📁 templates/          # 模板文件夹
│   └── 📄 door.png       # 门的模板图片
└── 📄 使用说明.txt        # 使用说明
```

## 打包注意事项

### 1. 依赖问题
- 某些系统可能缺少 Visual C++ 运行库
- 建议在目标系统上测试运行

### 2. 文件路径
- 已修改代码支持打包后的路径查找
- templates文件夹会自动包含在exe中

### 3. 杀毒软件
- 可能被杀毒软件误报
- 建议添加信任或暂时关闭实时保护

### 4. 性能优化
- 打包后启动可能较慢（首次运行）
- 可以使用 `--exclude-module` 排除不需要的模块

## 高级打包选项

```bash
# 优化版本（更小体积）
pyinstaller --onefile --console \
    --exclude-module matplotlib \
    --exclude-module pandas \
    --exclude-module scipy \
    --name "DNF自动刷图" \
    dnf_bot.py

# 无控制台版本（静默运行）
pyinstaller --onefile --windowed \
    --name "DNF自动刷图" \
    dnf_bot.py

# 添加图标
pyinstaller --onefile --console \
    --icon=icon.ico \
    --name "DNF自动刷图" \
    dnf_bot.py
```

## 分发说明

分发给其他用户时需要包含：
1. `DNF自动刷图.exe` - 主程序
2. `templates/` 文件夹 - 包含door.png等模板
3. 使用说明文档

## 常见问题

**Q: exe文件太大怎么办？**
A: 可以使用UPX压缩器压缩，或者排除不必要的模块

**Q: 在其他电脑上无法运行？**
A: 检查目标系统是否安装了Visual C++ 2015-2022运行库

**Q: 杀毒软件报毒？**
A: 这是误报，可以添加到白名单或使用代码签名证书
