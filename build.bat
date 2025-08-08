@echo off
echo 正在安装打包工具...
pip install -r build_requirements.txt

echo 正在打包程序...
pyinstaller --onefile --windowed --name "DNF自动刷图" dnf_bot.py

echo 打包完成！
echo 可执行文件位置: dist/DNF自动刷图.exe
pause
