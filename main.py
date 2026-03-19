#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库讲义生成器主入口文件
"""

import argparse
import os
import sys
import webbrowser
import threading
import socket
import time
from typing import Optional, Dict, Any

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加lecture_generator到路径
sys.path.insert(0, current_dir)

# 导入必要的模块
try:
    from lecture_generator.app import app
    from lecture_generator.core.path_handler import get_config, update_config, validate_path
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保lecture_generator目录存在且包含必要的模块")
    sys.exit(1)

def _resolve_browser_host(config):
    host = config.get('host', '127.0.0.1')
    if host in {'0.0.0.0', '::'}:
        return '127.0.0.1'
    return host


def _wait_for_server(host, port, timeout_seconds=10.0):
    start = time.time()
    while time.time() - start < timeout_seconds:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                if sock.connect_ex((host, port)) == 0:
                    return True
            except OSError:
                pass
        time.sleep(0.2)
    return False


def open_browser(config):
    """在新线程中打开浏览器

    Args:
        config: 应用配置
    """
    host = _resolve_browser_host(config)
    port = config.get('port', 5000)
    url = f"http://{host}:{port}"
    _wait_for_server(host, port)
    print(f"正在打开浏览器: {url}")

    if sys.platform.startswith('win'):
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            return
        except OSError:
            pass

    webbrowser.open(url, new=1)


def _choose_knowledge_base_gui(initial_dir: Optional[str] = None) -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    try:
        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory(
            title='选择知识库目录',
            initialdir=initial_dir or os.getcwd()
        )
        root.update()
        root.destroy()
        return selected or None
    except Exception:
        return None


def _choose_knowledge_base_cli() -> Optional[str]:
    try:
        value = input('请输入知识库目录路径: ').strip()
        return value or None
    except EOFError:
        return None


def _ensure_knowledge_base(config: Dict[str, Any], cli_path: Optional[str] = None) -> Dict[str, Any]:
    if cli_path:
        config['knowledge_base'] = cli_path

    current_path = config.get('knowledge_base')
    valid, _ = validate_path(current_path, require_md_files=True)
    if valid:
        if cli_path:
            update_config('knowledge_base', current_path)
        return config

    selected = _choose_knowledge_base_gui(initial_dir=current_path)
    if not selected:
        selected = _choose_knowledge_base_cli()

    if not selected:
        print('错误: 未选择有效的知识库路径，程序已退出。')
        sys.exit(1)

    valid, message = validate_path(selected, require_md_files=True)
    if not valid:
        print(f'错误: {message}')
        sys.exit(1)

    update_config('knowledge_base', selected)
    return get_config()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='知识库讲义生成器')
    parser.add_argument('--knowledge-base', dest='knowledge_base', help='知识库路径')
    parser.add_argument('--output-dir', dest='output_dir', help='输出目录')
    return parser.parse_args()

def main():
    """主函数"""
    args = _parse_args()

    # 获取配置
    config = get_config()

    if args.output_dir:
        update_config('output_dir', args.output_dir)
        config = get_config()

    config = _ensure_knowledge_base(config, cli_path=args.knowledge_base)

    # 显示启动信息
    print("=" * 60)
    print("知识库讲义生成器启动...")
    print("=" * 60)
    print(f"知识库路径: {config.get('knowledge_base')}")
    print(f"输出目录: {config.get('output_dir')}")
    print(f"访问地址: http://127.0.0.1:{config.get('port', 5000)}")
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    # 启动浏览器
    browser_thread = threading.Thread(target=open_browser, args=(config,))
    browser_thread.daemon = True
    browser_thread.start()

    # 运行应用
    app.run(
        host=config.get('host', '127.0.0.1'),
        port=config.get('port', 5000),
        debug=config.get('debug', False)
    )

if __name__ == '__main__':
    main()
