import os

# 基础配置
class Config:
    # Obsidian仓库路径
    OBSIDIAN_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'obsidian_repo')

    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True

    # 讲义生成配置
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

    # 支持的Markdown文件扩展名
    MARKDOWN_EXTENSIONS = ['.md', '.markdown']

    @staticmethod
    def init_output_dir():
        """初始化输出目录"""
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)