import os
import json
from pathlib import Path

class Config:
    """配置文件管理类"""

    # 默认配置
    DEFAULT_CONFIG = {
        'obsidian_repo': str(Path(__file__).parent.parent / 'obsidian_repo'),
        'output_dir': str(Path(__file__).parent / 'output'),
        'host': '0.0.0.0',
        'port': 5000,
        'debug': True,
        'markdown_extensions': ['.md', '.markdown']
    }

    # 配置文件路径
    CONFIG_FILE = Path(__file__).parent / 'config.json'

    # 加载配置
    @classmethod
    def load(cls):
        """加载配置文件"""
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls, config):
        """保存配置文件"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    @classmethod
    def update(cls, key, value):
        """更新配置项"""
        config = cls.load()
        config[key] = value
        return cls.save(config)

    # 配置属性（通过属性访问，自动加载）
    @property
    def obsidian_repo(self):
        return self._config['obsidian_repo']

    @property
    def output_dir(self):
        return self._config['output_dir']

    @property
    def host(self):
        return self._config['host']

    @property
    def port(self):
        return self._config['port']

    @property
    def debug(self):
        return self._config['debug']

    @property
    def markdown_extensions(self):
        return self._config['markdown_extensions']

    def __init__(self):
        self._config = self.load()
        self.init_output_dir()

    def init_output_dir(self):
        """初始化输出目录"""
        os.makedirs(self._config['output_dir'], exist_ok=True)

    def validate_obsidian_path(self, path):
        """验证Obsidian路径是否有效"""
        path_obj = Path(path)
        if not path_obj.exists():
            return False, "路径不存在"
        if not path_obj.is_dir():
            return False, "路径不是目录"

        # 检查是否包含markdown文件
        has_md_files = any(
            any(str(file).lower().endswith(ext) for ext in self._config['markdown_extensions'])
            for file in path_obj.rglob('*')
        )

        if not has_md_files:
            return False, "路径中没有找到Markdown文件"

        return True, "路径有效"

# 创建全局配置实例
_config_instance = Config()
OBSIDIAN_REPO = _config_instance.obsidian_repo
OUTPUT_DIR = _config_instance.output_dir
HOST = _config_instance.host
PORT = _config_instance.port
DEBUG = _config_instance.debug
MARKDOWN_EXTENSIONS = _config_instance.markdown_extensions