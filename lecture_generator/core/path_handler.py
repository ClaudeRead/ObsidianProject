#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径处理模块
处理Obsidian仓库路径的选择、验证和配置管理
"""

import json
import os
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any


class PathHandler:
    """路径处理器"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化路径处理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = self._resolve_config_path(config_file)
        if getattr(sys, 'frozen', False):
            user_base = Path.home() / '.knowledge_base_lecturer'
            self.default_config = {
                'knowledge_base': str(Path.home() / 'knowledge_base'),
                'output_dir': str(user_base / 'output'),
                'markdown_extensions': ['.md', '.markdown']
            }
        else:
            self.default_config = {
                'knowledge_base': str(Path(__file__).parent.parent.parent / 'knowledge_base'),
                'output_dir': str(Path(__file__).parent.parent / 'output'),
                'markdown_extensions': ['.md', '.markdown']
            }

    def _resolve_config_path(self, config_file: Optional[str]) -> Path:
        if config_file:
            return Path(config_file)

        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).resolve().parent
            local_config = exe_dir / 'config.json'
            if local_config.exists():
                return local_config
            return Path.home() / '.knowledge_base_lecturer' / 'config.json'

        return Path(__file__).parent.parent / 'config.json'

    def _normalize_path(self, path_value: Optional[str]) -> Optional[str]:
        if not path_value:
            return None

        expanded = os.path.expandvars(os.path.expanduser(str(path_value)))
        path_obj = Path(expanded)

        if not path_obj.is_absolute():
            path_obj = (self.config_file.parent / path_obj).resolve()
        else:
            path_obj = path_obj.resolve()

        return str(path_obj)

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件

        Returns:
            dict: 配置字典
        """
        config = self.default_config.copy()

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    config.update(loaded)
            except (json.JSONDecodeError, IOError):
                pass

        env_repo = os.getenv('KNOWLEDGE_BASE')
        env_output = os.getenv('OUTPUT_DIR')
        if env_repo:
            config['knowledge_base'] = env_repo
        if env_output:
            config['output_dir'] = env_output

        config['knowledge_base'] = self._normalize_path(config.get('knowledge_base'))
        config['output_dir'] = self._normalize_path(config.get('output_dir'))

        if config.get('knowledge_base') and not Path(config['knowledge_base']).exists():
            config['knowledge_base'] = self._normalize_path(self.default_config['knowledge_base'])

        if not config.get('output_dir'):
            config['output_dir'] = self._normalize_path(self.default_config['output_dir'])

        return config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件

        Args:
            config: 配置字典

        Returns:
            bool: 保存是否成功
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
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
        if key in {'knowledge_base', 'obsidian_repo', 'output_dir'}:
            value = self._normalize_path(value)
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
        normalized = self._normalize_path(path)
        if not normalized:
            return False, "路径不存在"

        path_obj = Path(normalized)

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

 