#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径处理模块
处理Obsidian仓库路径的选择、验证和配置管理
"""

import os
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any


class PathHandler:
    """路径处理器"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化路径处理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = Path(config_file) if config_file else Path(__file__).parent.parent / 'config.json'
        self.default_config = {
            'obsidian_repo': str(Path(__file__).parent.parent.parent / 'obsidian_repo'),
            'output_dir': str(Path(__file__).parent.parent / 'output'),
            'markdown_extensions': ['.md', '.markdown']
        }

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件

        Returns:
            dict: 配置字典
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self.default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件

        Args:
            config: 配置字典

        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def update_config(self, key: str, value: Any) -> bool:
        """更新配置项

        Args:
            key: 配置键
            value: 配置值

        Returns:
            bool: 更新是否成功
        """
        config = self.load_config()
        config[key] = value
        return self.save_config(config)

    def validate_path(self, path: str, require_md_files: bool = True) -> Tuple[bool, str]:
        """验证路径是否有效

        Args:
            path: 要验证的路径
            require_md_files: 是否要求包含Markdown文件

        Returns:
            tuple: (是否有效, 错误信息)
        """
        path_obj = Path(path)

        # 检查路径是否存在
        if not path_obj.exists():
            return False, "路径不存在"

        # 检查是否是目录
        if not path_obj.is_dir():
            return False, "路径不是目录"

        # 如果需要，检查是否包含Markdown文件
        if require_md_files:
            config = self.load_config()
            extensions = config.get('markdown_extensions', self.default_config['markdown_extensions'])

            has_md_files = False
            for ext in extensions:
                if any(path_obj.rglob(f'*{ext}')):
                    has_md_files = True
                    break

            if not has_md_files:
                return False, f"路径中没有找到Markdown文件（支持扩展: {', '.join(extensions)}）"

        return True, "路径有效"

    def get_markdown_files(self, directory: str, recursive: bool = True) -> list:
        """获取目录中的Markdown文件列表

        Args:
            directory: 目录路径
            recursive: 是否递归搜索

        Returns:
            list: Markdown文件路径列表（相对路径）
        """
        directory_path = Path(directory)
        config = self.load_config()
        extensions = config.get('markdown_extensions', self.default_config['markdown_extensions'])

        files = []

        if recursive:
            search_method = directory_path.rglob
        else:
            search_method = directory_path.glob

        for ext in extensions:
            for file_path in search_method(f'*{ext}'):
                if file_path.is_file():
                    # 获取相对于指定目录的相对路径
                    try:
                        rel_path = file_path.relative_to(directory_path)
                        files.append(str(rel_path))
                    except ValueError:
                        # 如果文件不在指定目录下，跳过
                        continue

        return sorted(files)

    def init_output_directory(self, output_dir: Optional[str] = None) -> str:
        """初始化输出目录

        Args:
            output_dir: 输出目录路径，如果为None则使用配置中的路径

        Returns:
            str: 输出目录路径
        """
        if output_dir is None:
            config = self.load_config()
            output_dir = config.get('output_dir', self.default_config['output_dir'])

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return str(output_path)

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            dict: 文件信息
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            return {'error': '文件不存在'}

        if not path_obj.is_file():
            return {'error': '不是文件'}

        try:
            stat = path_obj.stat()
            return {
                'path': str(path_obj),
                'name': path_obj.name,
                'stem': path_obj.stem,
                'suffix': path_obj.suffix,
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime
            }
        except Exception as e:
            return {'error': f'获取文件信息失败: {str(e)}'}


# 全局路径处理器实例
_path_handler_instance = PathHandler()

# 便捷函数
def get_config():
    """获取配置"""
    return _path_handler_instance.load_config()

def update_config(key, value):
    """更新配置"""
    return _path_handler_instance.update_config(key, value)

def validate_path(path, require_md_files=True):
    """验证路径"""
    return _path_handler_instance.validate_path(path, require_md_files)

def get_markdown_files(directory, recursive=True):
    """获取Markdown文件列表"""
    return _path_handler_instance.get_markdown_files(directory, recursive)

def init_output_directory(output_dir=None):
    """初始化输出目录"""
    return _path_handler_instance.init_output_directory(output_dir)