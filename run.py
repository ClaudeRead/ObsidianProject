#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的知识库讲义生成器启动脚本
"""

import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加项目路径
sys.path.insert(0, current_dir)

# 导入应用
try:
    # 尝试直接导入
    import lecture_generator.app
    import lecture_generator.core.path_handler
    app = lecture_generator.app.app
    get_config = lecture_generator.core.path_handler.get_config
except ImportError as e:
    print(f"导入错误: {e}")
    # 尝试另一种导入方式
    try:
        # 切换到lecture_generator目录
        os.chdir(os.path.join(current_dir, 'lecture_generator'))
        sys.path.insert(0, os.getcwd())
        import app
        import core.path_handler
        app = app.app
        get_config = core.path_handler.get_config
    except ImportError as e2:
        print(f"再次导入错误: {e2}")
        print("错误: 无法导入必要的模块")
        sys.exit(1)

if __name__ == '__main__':
    # 获取配置
    config = get_config()

    print("=" * 60)
    print("知识库讲义生成器启动...")
    print("=" * 60)
    print(f"知识库路径: {config.get('knowledge_base')}")
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