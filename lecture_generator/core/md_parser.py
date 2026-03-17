#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown解析模块
处理Markdown文件的解析、清理和内容提取
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib


class MarkdownParser:
    """Markdown解析器"""

    def __init__(self, clean_content: bool = True, extract_images: bool = True):
        """初始化解析器

        Args:
            clean_content: 是否清理冗余内容
            extract_images: 是否提取图片信息
        """
        self.clean_content = clean_content
        self.extract_images = extract_images

    def parse_file(self, file_path: str, filename: Optional[str] = None,
                   show_analysis: bool = True, show_notes: bool = True) -> Dict[str, Any]:
        """解析Markdown文件

        Args:
            file_path: 文件路径
            filename: 文件名（如果为None则从路径中提取）
            show_analysis: 是否显示【解析】内容
            show_notes: 是否显示【注意】内容

        Returns:
            dict: 解析结果
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return {'error': f'文件不存在: {file_path}'}

        if filename is None:
            filename = file_path_obj.name

        try:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.parse_content(content, filename, show_analysis, show_notes)

        except Exception as e:
            return {'error': f'读取文件失败: {str(e)}'}

    def parse_content(self, content: str, filename: str,
                      show_analysis: bool = True, show_notes: bool = True) -> Dict[str, Any]:
        """解析Markdown内容

        Args:
            content: Markdown内容
            filename: 文件名（用于标题清理）
            show_analysis: 是否显示【解析】内容
            show_notes: 是否显示【注意】内容

        Returns:
            dict: 解析结果
        """
        original_content = content
        parsed_content = content

        # 清理冗余内容
        if self.clean_content:
            parsed_content = self._clean_content(parsed_content, filename)

        # 根据选项过滤内容
        if not show_analysis:
            parsed_content = self._remove_section(parsed_content, '【解析】')

        if not show_notes:
            parsed_content = self._remove_section(parsed_content, '【注意】')

        # 提取图片信息
        images = []
        if self.extract_images:
            images = self._extract_images(parsed_content)

        # 提取标题
        headings = self._extract_headings(parsed_content)

        # 提取第一个h1标题作为文章标题
        h1_title = self._extract_first_h1_title(parsed_content)
        if not h1_title:
            # 如果没有h1标题，使用文件名（不含扩展名）作为标题
            h1_title = Path(filename).stem

        # 计算内容哈希（用于检测重复）
        content_hash = hashlib.md5(parsed_content.encode('utf-8')).hexdigest()[:8]

        return {
            'original_content': original_content,
            'parsed_content': parsed_content,
            'filename': filename,
            'h1_title': h1_title,
            'has_analysis': '【解析】' in original_content,
            'has_notes': '【注意】' in original_content,
            'images': images,
            'image_count': len(images),
            'headings': headings,
            'heading_count': len(headings),
            'content_hash': content_hash,
            'word_count': len(parsed_content.split()),
            'line_count': len(parsed_content.split('\n'))
        }

    def _extract_first_h1_title(self, content: str) -> Optional[str]:
        """提取第一个h1标题

        Args:
            content: Markdown内容

        Returns:
            str: 第一个h1标题，如果没有则返回None
        """
        # 匹配h1标题：以#开头，后面跟空格，然后是标题文本
        h1_pattern = re.compile(r'^#\s+(.+)$', re.MULTILINE)
        match = h1_pattern.search(content)

        if match:
            title = match.group(1).strip()
            # 移除可能的内联格式标记
            title = re.sub(r'[*_`]', '', title)
            return title

        return None

    def _clean_content(self, content: str, filename: str) -> str:
        """清理Markdown内容，移除冗余信息，保留纯正文

        清理规则：
        1. 保留h1标题（用于讲义模块标题），但如果文件名与h1标题一致，则可能移除重复标题
        2. 处理Obsidian内部链接，移除路径信息，保留显示文本
        3. 移除文件路径、来源等元信息行
        4. 清理多余的空行

        Args:
            content: 原始内容
            filename: 文件名

        Returns:
            str: 清理后的内容
        """
        cleaned = content

        # 提取文件名（不含扩展名）用于后续比较
        filename_stem = Path(filename).stem

        # 1. 检查并处理h1标题
        # 首先提取第一个h1标题
        h1_title = self._extract_first_h1_title(content)

        # 如果h1标题与文件名相同，可能考虑移除或保留
        # 这里我们保留h1标题，因为讲义需要用它作为模块标题

        # 2. 处理Obsidian内部链接（但不处理图片链接）
        # 格式1: [[路径/文件名.md]]
        # 格式2: [[路径/文件名.md|显示文本]]
        # 格式3: [[路径/文件名#标题]]
        # 注意：不匹配以!开头的图片链接
        internal_link_pattern = re.compile(r'(?<!\!)\[\[([^\]]+?\.md)(?:#([^\]]+))?(?:\|([^\]]+))?\]\]')

        def replace_internal_link(match):
            md_file = match.group(1)
            anchor = match.group(2)  # 锚点部分
            display_text = match.group(3) or Path(md_file).stem

            # 构建更干净的链接
            if anchor:
                return f'[{display_text}](#{anchor})'
            else:
                return f'[{display_text}]()'

        cleaned = internal_link_pattern.sub(replace_internal_link, cleaned)

        # 3. 处理标准Markdown链接中的路径
        # 移除Markdown链接中的文件路径信息
        markdown_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+?\.md)\)')

        def clean_markdown_link(match):
            display_text = match.group(1)
            return f'[{display_text}]()'

        cleaned = markdown_link_pattern.sub(clean_markdown_link, cleaned)

        # 4. 移除文件路径元信息行
        path_patterns = [
            # 中文模式
            re.compile(r'^.*(文件(路径|名)?|来源|路径)[：:].*\.md.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*文件.*:.*$', re.MULTILINE | re.IGNORECASE),
            # 英文模式
            re.compile(r'^.*(file(path|name)?|source|path).*:.*\.md.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*filename.*:.*$', re.MULTILINE | re.IGNORECASE),
            # 生成时间、创建时间等
            re.compile(r'^.*(生成|创建|修改)?时间.*[:：].*$', re.MULTILINE),
            re.compile(r'^.*(generated|created|modified).*:.*$', re.MULTILINE | re.IGNORECASE)
        ]

        for pattern in path_patterns:
            cleaned = pattern.sub('', cleaned)

        # 5. 移除空行（连续3个以上换行符）
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)

        # 6. 移除开头和结尾的空白
        cleaned = cleaned.strip()

        # 7. 确保不以空行结尾
        cleaned = re.sub(r'\n+$', '\n', cleaned)

        return cleaned

    def _extract_images(self, content: str) -> List[Dict[str, str]]:
        """从内容中提取图片信息

        Args:
            content: Markdown内容

        Returns:
            list: 图片信息列表
        """
        images = []

        # Obsidian内链格式: ![[图片名.png]]
        obsidian_pattern = re.compile(
            r'!\[\[([^\]]+?\.(?:png|jpg|jpeg|gif|bmp|svg|webp|tiff))(?:\|([^\]]+))?\]\]',
            re.IGNORECASE
        )

        for match in obsidian_pattern.finditer(content):
            images.append({
                'type': 'obsidian',
                'path': match.group(1),
                'alt': match.group(2) or Path(match.group(1)).stem,
                'full_match': match.group(0),
                'line_number': content[:match.start()].count('\n') + 1
            })

        # 标准Markdown格式: ![描述](图片路径.png)
        markdown_pattern = re.compile(
            r'!\[([^\]]*)\]\(([^)]+?\.(?:png|jpg|jpeg|gif|bmp|svg|webp|tiff))\)',
            re.IGNORECASE
        )

        for match in markdown_pattern.finditer(content):
            images.append({
                'type': 'markdown',
                'path': match.group(2),
                'alt': match.group(1) or Path(match.group(2)).stem,
                'full_match': match.group(0),
                'line_number': content[:match.start()].count('\n') + 1
            })

        return images

    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """提取标题信息

        Args:
            content: Markdown内容

        Returns:
            list: 标题信息列表
        """
        headings = []

        # 匹配1-6级标题
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        for match in heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()

            # 生成锚点ID
            anchor = re.sub(r'[^\w\s-]', '', text.lower())
            anchor = re.sub(r'[-\s]+', '-', anchor).strip('-')

            headings.append({
                'level': level,
                'text': text,
                'anchor': anchor,
                'line_number': content[:match.start()].count('\n') + 1
            })

        return headings

    def _remove_section(self, content: str, section_marker: str) -> str:
        """移除指定章节的内容

        Args:
            content: 原始内容
            section_marker: 章节标记

        Returns:
            str: 移除指定章节后的内容
        """
        pattern = re.compile(rf'{re.escape(section_marker)}.*?(?=\n【|$)', re.DOTALL)
        return pattern.sub('', content)

    def get_content_stats(self, content: str) -> Dict[str, int]:
        """获取内容统计信息

        Args:
            content: 文本内容

        Returns:
            dict: 统计信息
        """
        lines = content.split('\n')
        words = content.split()

        return {
            'characters': len(content),
            'words': len(words),
            'lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'sentences': len(re.findall(r'[.!?]+', content)),
            'paragraphs': len(re.split(r'\n\s*\n', content))
        }

    def merge_contents(self, contents: List[Dict[str, Any]], separator: str = '\n\n---\n\n') -> str:
        """合并多个内容

        Args:
            contents: 内容列表，每个元素应包含 'title' 和 'content'
            separator: 内容分隔符

        Returns:
            str: 合并后的内容
        """
        merged_parts = []

        for i, item in enumerate(contents):
            if 'title' in item and 'content' in item:
                # 添加标题
                merged_parts.append(f'## {item["title"]}\n')
                # 添加内容
                merged_parts.append(item['content'])

                # 如果不是最后一个，添加分隔符
                if i < len(contents) - 1:
                    merged_parts.append(separator)

        return '\n'.join(merged_parts)


# 全局解析器实例
_parser_instance = MarkdownParser()

# 便捷函数
def parse_file(file_path, filename=None, show_analysis=True, show_notes=True):
    """解析文件"""
    return _parser_instance.parse_file(file_path, filename, show_analysis, show_notes)

def parse_content(content, filename, show_analysis=True, show_notes=True):
    """解析内容"""
    return _parser_instance.parse_content(content, filename, show_analysis, show_notes)

def merge_contents(contents, separator='\n\n---\n\n'):
    """合并内容"""
    return _parser_instance.merge_contents(contents, separator)