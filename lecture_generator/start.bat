@echo off
echo Obsidian 讲义生成器 - 启动脚本
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6或更高版本
    pause
    exit /b 1
)

REM 检查是否在虚拟环境中
echo 正在检查依赖...
pip list | findstr "Flask" >nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
)

REM 运行应用
echo 启动Obsidian讲义生成器...
echo Obsidian仓库路径: obsidian_repo
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.

python app.py