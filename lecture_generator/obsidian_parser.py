import os
import re
from pathlib import Path
from config import Config

class ObsidianParser:
    """Obsidian内容解析器"""

    def __init__(self, obsidian_path=None):
        """初始化解析器

        Args:
            obsidian_path: Obsidian仓库路径，如果为None则使用配置中的路径
        """
        self.obsidian_path = Path(obsidian_path) if obsidian_path else Path(Config.OBSIDIAN_REPO)

    def get_directory_structure(self):
        """获取Obsidian仓库的目录结构

        Returns:
            list: 目录结构列表，每个元素包含路径、名称、类型等信息
        """
        structure = []
        self._scan_directory(self.obsidian_path, Path(''), structure)
        return structure

    def _scan_directory(self, current_path, relative_path, structure):
        """递归扫描目录

        Args:
            current_path: 当前扫描的绝对路径
            relative_path: 相对于Obsidian仓库的相对路径
            structure: 存储结果的列表
        """
        try:
            items = sorted(os.listdir(current_path))
        except Exception as e:
            print(f"无法读取目录 {current_path}: {e}")
            return

        for item in items:
            item_path = current_path / item
            relative_item_path = relative_path / item

            # 忽略隐藏文件
            if item.startswith('.'):
                continue

            if item_path.is_dir():
                # 是目录
                structure.append({
                    'type': 'directory',
                    'name': item,
                    'path': str(relative_item_path),
                    'full_path': str(item_path),
                    'children': [],
                    'expanded': False  # 默认折叠
                })

                # 递归扫描子目录
                child_index = len(structure) - 1
                self._scan_directory(item_path, relative_item_path, structure[child_index]['children'])

            elif any(item.lower().endswith(ext) for ext in Config.MARKDOWN_EXTENSIONS):
                # 是Markdown文件
                structure.append({
                    'type': 'file',
                    'name': item,
                    'path': str(relative_item_path),
                    'full_path': str(item_path),
                    'size': item_path.stat().st_size
                })

    def read_markdown_file(self, file_path, show_analysis=True, show_notes=True,
                          clean_content=True, extract_images=True):
        """读取Markdown文件内容，并根据选项过滤内容

        Args:
            file_path: 相对于Obsidian仓库的文件路径
            show_analysis: 是否显示【解析】内容
            show_notes: 是否显示【注意】内容
            clean_content: 是否清理冗余内容（移除与文件名一致的标题、路径文本等）
            extract_images: 是否提取图片信息

        Returns:
            dict: 包含文件信息和过滤后内容的字典
        """
        full_path = self.obsidian_path / file_path

        if not full_path.exists():
            return {'error': f'文件不存在: {file_path}'}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取原始内容
            original_content = content

            # 清理冗余内容
            if clean_content:
                content = self._clean_markdown_content(content, full_path.name)

            # 根据选项过滤内容
            if not show_analysis:
                content = self._remove_section(content, '【解析】')

            if not show_notes:
                content = self._remove_section(content, '【注意】')

            # 提取图片信息
            images = []
            if extract_images:
                images = self._extract_images(content)

            return {
                'file_path': str(file_path),
                'file_name': full_path.name,
                'original_content': original_content,
                'filtered_content': content,
                'has_analysis': '【解析】' in original_content,
                'has_notes': '【注意】' in original_content,
                'images': images,
                'image_count': len(images)
            }

        except Exception as e:
            return {'error': f'读取文件失败: {str(e)}'}

    def _clean_markdown_content(self, content, filename):
        """清理Markdown内容，移除冗余信息

        1. 移除与文件名一致的一级标题
        2. 剔除路径相关文本（Obsidian内部链接仅保留内容）
        3. 移除文件名、文件路径等元信息

        Args:
            content: 原始内容
            filename: 文件名（用于识别匹配的标题）

        Returns:
            str: 清理后的内容
        """
        # 移除文件扩展名获取基础文件名
        base_filename = Path(filename).stem

        # 1. 移除与文件名一致的一级标题
        # 匹配 "# 文件名" 或 "# 文件名\n"
        title_pattern = re.compile(rf'^#\s*{re.escape(base_filename)}\s*$\n?', re.MULTILINE)
        content = title_pattern.sub('', content)

        # 2. 处理Obsidian内部链接，移除路径信息
        # 匹配 [[路径/文件名.md]] 或 [[路径/文件名.md|显示文本]]
        internal_link_pattern = re.compile(r'\[\[([^\]]+?\.md)(?:\|([^\]]+))?\]\]')

        def replace_internal_link(match):
            md_file = match.group(1)
            display_text = match.group(2) or Path(md_file).stem
            return f'[{display_text}]({md_file})'

        content = internal_link_pattern.sub(replace_internal_link, content)

        # 3. 移除可能出现的文件路径元信息行
        # 匹配包含路径的行，如 "路径: xxx/xxx.md" 或 "文件路径: ..."
        path_patterns = [
            re.compile(r'^.*[路径|path|file].*:.*\.md.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*filename.*:.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*文件.*:.*$', re.MULTILINE)
        ]

        for pattern in path_patterns:
            content = pattern.sub('', content)

        # 清理多余的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        return content.strip()

    def _extract_images(self, content):
        """从内容中提取图片信息

        支持两种格式：
        1. Obsidian内链格式: ![[图片名.png]]
        2. 标准Markdown格式: ![描述](图片路径.png)

        Args:
            content: Markdown内容

        Returns:
            list: 图片信息列表
        """
        images = []

        # 匹配Obsidian内链格式
        obsidian_pattern = re.compile(r'!\[\[([^\]]+?\.(?:png|jpg|jpeg|gif|bmp|svg|webp))\]\]', re.IGNORECASE)
        for match in obsidian_pattern.finditer(content):
            images.append({
                'type': 'obsidian',
                'path': match.group(1),
                'alt': Path(match.group(1)).stem,
                'full_match': match.group(0)
            })

        # 匹配标准Markdown格式
        markdown_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+?\.(?:png|jpg|jpeg|gif|bmp|svg|webp))\)', re.IGNORECASE)
        for match in markdown_pattern.finditer(content):
            images.append({
                'type': 'markdown',
                'path': match.group(2),
                'alt': match.group(1) or Path(match.group(2)).stem,
                'full_match': match.group(0)
            })

        return images

    def _remove_section(self, content, section_marker):
        """移除指定章节的内容

        Args:
            content: 原始文本内容
            section_marker: 章节标记，如'【解析】'或'【注意】'

        Returns:
            str: 移除指定章节后的内容
        """
        pattern = re.compile(rf'{re.escape(section_marker)}.*?(?=\n【|$)', re.DOTALL)
        return pattern.sub('', content)

    def get_file_content(self, file_path):
        """获取文件的原始内容（不进行过滤）

        Args:
            file_path: 相对于Obsidian仓库的文件路径

        Returns:
            str: 文件原始内容
        """
        full_path = self.obsidian_path / file_path

        if not full_path.exists():
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

        for root, dirs, files in os.walk(str(self.obsidian_path)):
            for file in files:
                # 检查扩展名
                if not any(file.lower().endswith(ext) for ext in extensions):
                    continue

                # 检查模式
                if pattern and not re.search(pattern, file, re.IGNORECASE):
                    continue

                # 构建相对路径
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.obsidian_path)
                matched_files.append(str(relative_path))

        return sorted(matched_files)

    def validate_path(self, path):
        """验证路径是否存在且有效

        Args:
            path: 要验证的路径

        Returns:
            tuple: (是否有效, 错误信息)
        """
        path_obj = Path(path)
        if not path_obj.exists():
            return False, "路径不存在"
        if not path_obj.is_dir():
            return False, "路径不是目录"
        return True, "路径有效"