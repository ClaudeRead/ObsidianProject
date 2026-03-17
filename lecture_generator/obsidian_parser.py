import os
import re
from config import Config

class ObsidianParser:
    """Obsidian内容解析器"""

    def __init__(self, obsidian_path=None):
        """初始化解析器

        Args:
            obsidian_path: Obsidian仓库路径，如果为None则使用配置中的路径
        """
        self.obsidian_path = obsidian_path or Config.OBSIDIAN_REPO

    def get_directory_structure(self):
        """获取Obsidian仓库的目录结构

        Returns:
            list: 目录结构列表，每个元素包含路径、名称、类型等信息
        """
        structure = []
        self._scan_directory(self.obsidian_path, '', structure)
        return structure

    def _scan_directory(self, current_path, relative_path, structure):
        """递归扫描目录

        Args:
            current_path: 当前扫描的绝对路径
            relative_path: 相对于Obsidian仓库的相对路径
            structure: 存储结果的列表
        """
        try:
            items = os.listdir(current_path)
        except Exception as e:
            print(f"无法读取目录 {current_path}: {e}")
            return

        for item in sorted(items):
            item_path = os.path.join(current_path, item)
            relative_item_path = os.path.join(relative_path, item) if relative_path else item

            # 忽略隐藏文件
            if item.startswith('.'):
                continue

            if os.path.isdir(item_path):
                # 是目录
                structure.append({
                    'type': 'directory',
                    'name': item,
                    'path': relative_item_path,
                    'full_path': item_path,
                    'children': []
                })

                # 递归扫描子目录
                child_index = len(structure) - 1
                self._scan_directory(item_path, relative_item_path, structure[child_index]['children'])

            elif any(item.lower().endswith(ext) for ext in Config.MARKDOWN_EXTENSIONS):
                # 是Markdown文件
                structure.append({
                    'type': 'file',
                    'name': item,
                    'path': relative_item_path,
                    'full_path': item_path,
                    'size': os.path.getsize(item_path)
                })

    def read_markdown_file(self, file_path, show_analysis=True, show_notes=True):
        """读取Markdown文件内容，并根据选项过滤内容

        Args:
            file_path: 相对于Obsidian仓库的文件路径
            show_analysis: 是否显示【解析】内容
            show_notes: 是否显示【注意】内容

        Returns:
            dict: 包含文件信息和过滤后内容的字典
        """
        full_path = os.path.join(self.obsidian_path, file_path)

        if not os.path.exists(full_path):
            return {'error': f'文件不存在: {file_path}'}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取原始内容
            original_content = content

            # 根据选项过滤内容
            if not show_analysis:
                # 移除【解析】内容
                content = self._remove_section(content, '【解析】')

            if not show_notes:
                # 移除【注意】内容
                content = self._remove_section(content, '【注意】')

            return {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'original_content': original_content,
                'filtered_content': content,
                'has_analysis': '【解析】' in original_content,
                'has_notes': '【注意】' in original_content
            }

        except Exception as e:
            return {'error': f'读取文件失败: {str(e)}'}

    def _remove_section(self, content, section_marker):
        """移除指定章节的内容

        Args:
            content: 原始文本内容
            section_marker: 章节标记，如'【解析】'或'【注意】'

        Returns:
            str: 移除指定章节后的内容
        """
        # 使用正则表达式匹配章节标记及其后面的内容，直到下一个章节标记或文件结束
        pattern = re.compile(rf'{re.escape(section_marker)}.*?(?=\n【|$)', re.DOTALL)
        return pattern.sub('', content)

    def get_file_content(self, file_path):
        """获取文件的原始内容（不进行过滤）

        Args:
            file_path: 相对于Obsidian仓库的文件路径

        Returns:
            str: 文件原始内容
        """
        full_path = os.path.join(self.obsidian_path, file_path)

        if not os.path.exists(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败 {full_path}: {e}")
            return None

    def scan_files_by_pattern(self, pattern=None, extensions=None):
        """扫描匹配特定模式的文件

        Args:
            pattern: 文件名模式（支持正则表达式）
            extensions: 文件扩展名列表

        Returns:
            list: 匹配的文件路径列表
        """
        if extensions is None:
            extensions = Config.MARKDOWN_EXTENSIONS

        matched_files = []

        for root, dirs, files in os.walk(self.obsidian_path):
            for file in files:
                # 检查扩展名
                if not any(file.lower().endswith(ext) for ext in extensions):
                    continue

                # 检查模式
                if pattern and not re.search(pattern, file):
                    continue

                # 构建相对路径
                relative_path = os.path.relpath(os.path.join(root, file), self.obsidian_path)
                matched_files.append(relative_path)

        return sorted(matched_files)