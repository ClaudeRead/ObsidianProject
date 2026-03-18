#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的Obsidian讲义生成器启动脚本
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
lecture_generator_dir = os.path.join(project_root, 'lecture_generator')

if lecture_generator_dir not in sys.path:
    sys.path.insert(0, lecture_generator_dir)

# 导入应用
from app import app

if __name__ == '__main__':
    # 获取配置
    from core.path_handler import get_config
    config = get_config()

    print("=" * 60)
    print("Obsidian讲义生成器启动...")
    print("=" * 60)
    print(f"Obsidian仓库路径: {config.get('obsidian_repo')}")
    print(f"输出目录: {config.get('output_dir')}")
    print(f"访问地址: http://127.0.0.1:{config.get('port', 5000)}")
    
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    # 运行应用
    app.run(
        host=config.get('host', '127.0.0.1'),
        port=config.get('port', 5000),
        debug=config.get('debug', False)
    )