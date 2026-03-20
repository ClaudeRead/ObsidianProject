#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown解析模块
"""

import hashlib
import re
from urllib.parse import quote
from pathlib import Path
from typing import Dict, Optional, List


class MarkdownParser:
    """Markdown解析器"""

    def __init__(self, clean_content: bool = True, obsidian_root: Optional[str] = None):
        self.clean_content = clean_content
        self.obsidian_root = Path(obsidian_root).resolve() if obsidian_root else None

    def parse_file(self, file_path: str, filename: Optional[str] = None,
                   show_analysis: bool = True, show_notes: bool = True,
                   obsidian_root: Optional[str] = None,
                   include_tags: Optional[List[str]] = None) -> Dict[str, object]:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return {'error': f'文件不存在: {file_path}'}

        if filename is None:
            filename = file_path_obj.name

        # 获取文件所在目录
        file_dir = str(file_path_obj.parent)

        try:
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.parse_content(
                content,
                filename,
                file_dir,
                show_analysis,
                show_notes,
                obsidian_root=obsidian_root,
                include_tags=include_tags
            )

        except Exception as e:
            return {'error': f'读取文件失败: {str(e)}'}

    def parse_content(self, content: str, filename: str, file_dir: str,
                      show_analysis: bool = True, show_notes: bool = True,
                      obsidian_root: Optional[str] = None,
                      include_tags: Optional[List[str]] = None) -> Dict[str, object]:
        parsed_content = content

        if self.clean_content:
            parsed_content = self._clean_content(parsed_content, filename, file_dir, obsidian_root)

        detected_tags = self.extract_section_tags(parsed_content)

        if include_tags is not None:
            include_set = set(include_tags)
            for tag in detected_tags:
                if tag not in include_set:
                    parsed_content = self._remove_section(parsed_content, tag)
        else:
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
            'content_hash': content_hash,
            'detected_tags': detected_tags
        }

    def extract_section_tags(self, content: str) -> List[str]:
        if not content:
            return []

        tag_pattern = re.compile(r'【[^】\n]+】')
        matches = tag_pattern.findall(content)

        seen = set()
        tags = []
        for tag in matches:
            if tag in seen:
                continue
            tags.append(tag)
            seen.add(tag)

        return tags

    def _extract_first_h1_title(self, content: str) -> Optional[str]:
        h1_pattern = re.compile(r'^#\s+(.+)$', re.MULTILINE)
        match = h1_pattern.search(content)

        if match:
            title = match.group(1).strip()
            return re.sub(r'[*_`]', '', title)

        return None

    def _clean_content(self, content: str, filename: str, file_dir: str,
                       obsidian_root: Optional[str] = None) -> str:
        cleaned = content

        cleaned = self._rewrite_obsidian_images(cleaned, file_dir, obsidian_root)
        cleaned = self._rewrite_markdown_images(cleaned, file_dir, obsidian_root)

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

    def _normalize_image_path(self, image_path: str) -> str:
        normalized = image_path.replace('\\', '/').lstrip('./')
        normalized = normalized.lstrip('/')
        return normalized

    def _image_url(self, image_path: str) -> str:
        normalized = self._normalize_image_path(image_path)
        return f'/api/image/{quote(normalized, safe="/")}'

    def _resolve_obsidian_root(self, file_dir: str, obsidian_root: Optional[str]) -> Optional[Path]:
        if obsidian_root:
            root = Path(obsidian_root)
            if root.exists():
                return root.resolve()

        if self.obsidian_root and self.obsidian_root.exists():
            return self.obsidian_root

        # Fallback: detect Obsidian vault by .obsidian folder
        current = Path(file_dir).resolve()
        for parent in [current] + list(current.parents):
            if (parent / '.obsidian').exists():
                return parent

        return None

    def _relative_to_root(self, image_path: Path, obsidian_root: Optional[Path]) -> Optional[str]:
        if not obsidian_root:
            return None
        try:
            return image_path.resolve().relative_to(obsidian_root.resolve()).as_posix()
        except ValueError:
            return None

    def _rewrite_obsidian_images(self, content: str, file_dir: str,
                                 obsidian_root: Optional[str]) -> str:
        pattern = re.compile(r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

        def replace_image(match):
            path = match.group(1).strip()
            alt = match.group(2) or Path(path).stem
            image_path = Path(file_dir) / path
            root = self._resolve_obsidian_root(file_dir, obsidian_root)
            normalized_path = self._relative_to_root(image_path, root)
            if not normalized_path:
                normalized_path = str(image_path).replace('\\', '/')
            return f'![{alt}]({self._image_url(normalized_path)})'

        return pattern.sub(replace_image, content)

    def _rewrite_markdown_images(self, content: str, file_dir: str,
                                 obsidian_root: Optional[str]) -> str:
        pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

        def replace_image(match):
            alt_text = match.group(1)
            url = match.group(2).strip()

            if re.match(r'^[a-zA-Z]+:', url) or url.startswith('/'):
                return match.group(0)

            image_path = Path(file_dir) / url
            root = self._resolve_obsidian_root(file_dir, obsidian_root)
            normalized_path = self._relative_to_root(image_path, root)
            if not normalized_path:
                normalized_path = str(image_path).replace('\\', '/')
            return f'![{alt_text}]({self._image_url(normalized_path)})'

        return pattern.sub(replace_image, content)

    def _remove_section(self, content: str, section_marker: str) -> str:
        pattern = re.compile(rf'{re.escape(section_marker)}.*?(?=\n【|$)', re.DOTALL)
        return pattern.sub('', content)
