#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown解析模块
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, Optional


class MarkdownParser:
    """Markdown解析器"""

    def __init__(self, clean_content: bool = True):
        self.clean_content = clean_content

    def parse_file(self, file_path: str, filename: Optional[str] = None,
                   show_analysis: bool = True, show_notes: bool = True) -> Dict[str, str]:
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
                      show_analysis: bool = True, show_notes: bool = True) -> Dict[str, str]:
        parsed_content = content

        if self.clean_content:
            parsed_content = self._clean_content(parsed_content, filename)

        if not show_analysis:
            parsed_content = self._remove_section(parsed_content, '【解析】')

        if not show_notes:
            parsed_content = self._remove_section(parsed_content, '【注意】')

        h1_title = self._extract_first_h1_title(parsed_content)
        if not h1_title:
            h1_title = Path(filename).stem

        content_hash = hashlib.md5(parsed_content.encode('utf-8')).hexdigest()[:8]

        return {
            'parsed_content': parsed_content,
            'h1_title': h1_title,
            'content_hash': content_hash
        }

    def _extract_first_h1_title(self, content: str) -> Optional[str]:
        h1_pattern = re.compile(r'^#\s+(.+)$', re.MULTILINE)
        match = h1_pattern.search(content)

        if match:
            title = match.group(1).strip()
            return re.sub(r'[*_`]', '', title)

        return None

    def _clean_content(self, content: str, filename: str) -> str:
        cleaned = content

        internal_link_pattern = re.compile(r'(?<!\!)\[\[([^\]]+?\.md)(?:#([^\]]+))?(?:\|([^\]]+))?\]\]')

        def replace_internal_link(match):
            md_file = match.group(1)
            anchor = match.group(2)
            display_text = match.group(3) or Path(md_file).stem

            if anchor:
                return f'[{display_text}](#{anchor})'
            return f'[{display_text}]()'

        cleaned = internal_link_pattern.sub(replace_internal_link, cleaned)

        markdown_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+?\.md)\)')

        def clean_markdown_link(match):
            display_text = match.group(1)
            return f'[{display_text}]()'

        cleaned = markdown_link_pattern.sub(clean_markdown_link, cleaned)

        path_patterns = [
            re.compile(r'^.*(文件(路径|名)?|来源|路径)[：:].*\.md.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*文件.*:.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*(file(path|name)?|source|path).*:.*\.md.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*filename.*:.*$', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^.*(生成|创建|修改)?时间.*[:：].*$', re.MULTILINE),
            re.compile(r'^.*(generated|created|modified).*:.*$', re.MULTILINE | re.IGNORECASE)
        ]

        for pattern in path_patterns:
            cleaned = pattern.sub('', cleaned)

        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = cleaned.strip()
        cleaned = re.sub(r'\n+$', '\n', cleaned)

        return cleaned

    def _remove_section(self, content: str, section_marker: str) -> str:
        pattern = re.compile(rf'{re.escape(section_marker)}.*?(?=\n【|$)', re.DOTALL)
        return pattern.sub('', content)
