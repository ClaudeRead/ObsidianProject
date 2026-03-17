#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容合并模块
处理多个Markdown文件的合并、去重和格式优化
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
import hashlib


class ContentConcatenator:
    """内容合并器"""

    def __init__(self, remove_duplicates: bool = True, optimize_format: bool = True):
        """初始化合并器

        Args:
            remove_duplicates: 是否移除重复内容
            optimize_format: 是否优化格式
        """
        self.remove_duplicates = remove_duplicates
        self.optimize_format = optimize_format
        self.seen_hashes: Set[str] = set()

    def concatenate_files(self, files_data: List[Dict[str, Any]],
                          include_toc: bool = True, title: Optional[str] = None) -> Dict[str, Any]:
        """合并多个文件内容

        Args:
            files_data: 文件数据列表，每个元素应包含 'title', 'content', 'path' 等信息
            include_toc: 是否包含目录
            title: 合并后的文档标题

        Returns:
            dict: 合并结果
        """
        if not files_data:
            return {'error': '没有可合并的文件数据'}

        # 重置已见哈希集合
        self.seen_hashes.clear()

        # 处理每个文件的内容
        processed_files = []
        skipped_files = []

        for file_data in files_data:
            processed = self._process_file_content(file_data)

            if processed.get('skipped', False):
                skipped_files.append(processed)
            else:
                processed_files.append(processed)

        if not processed_files:
            return {'error': '所有文件内容都被跳过（可能全部为重复内容）'}

        # 生成合并后的内容
        concatenated = self._generate_concatenated_content(processed_files, include_toc, title)

        return {
            'success': True,
            'concatenated_content': concatenated,
            'files_processed': len(processed_files),
            'files_skipped': len(skipped_files),
            'total_files': len(files_data),
            'processed_files': processed_files,
            'skipped_files': skipped_files,
            'generated_at': datetime.now().isoformat()
        }

    def _process_file_content(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文件内容

        Args:
            file_data: 文件数据

        Returns:
            dict: 处理后的文件数据
        """
        # 提取必要字段
        title = file_data.get('title', '未命名')
        content = file_data.get('content', '')
        path = file_data.get('path', '')
        file_hash = file_data.get('hash')

        # 计算内容哈希（如果未提供）
        if file_hash is None:
            file_hash = self._calculate_content_hash(content)

        # 检查重复内容
        if self.remove_duplicates and file_hash in self.seen_hashes:
            return {
                'title': title,
                'path': path,
                'hash': file_hash,
                'skipped': True,
                'reason': '重复内容'
            }

        # 添加到已见哈希集合
        self.seen_hashes.add(file_hash)

        # 清理和优化内容
        cleaned_content = self._clean_and_optimize_content(content, title)

        # 获取内容统计
        stats = self._get_content_stats(cleaned_content)

        return {
            'title': title,
            'path': path,
            'content': cleaned_content,
            'hash': file_hash,
            'skipped': False,
            'stats': stats,
            'processed_at': datetime.now().isoformat()
        }

    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值

        Args:
            content: 文本内容

        Returns:
            str: 哈希值
        """
        # 移除空白字符和标点，只保留主要内容
        normalized = re.sub(r'\s+', ' ', content.lower())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:12]

    def _clean_and_optimize_content(self, content: str, title: str) -> str:
        """清理和优化内容

        Args:
            content: 原始内容
            title: 标题

        Returns:
            str: 清理后的内容
        """
        if not self.optimize_format:
            return content

        cleaned = content

        # 1. 移除多余的标题层级（如果内容以与文件标题相同的标题开始）
        # 避免出现 ## 标题 接着又是 ## 标题的情况
        title_pattern = re.compile(rf'^##\s*{re.escape(title)}\s*$\n?', re.MULTILINE)
        if title_pattern.search(cleaned):
            # 找到第一个匹配的标题并移除
            cleaned = title_pattern.sub('', cleaned, 1)

        # 2. 标准化换行符
        cleaned = re.sub(r'\r\n', '\n', cleaned)
        cleaned = re.sub(r'\r', '\n', cleaned)

        # 3. 标准化段落分隔
        # 将多个空行减少为两个空行
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n\n', cleaned)

        # 4. 修复常见的格式问题
        # 修复列表项后的多余空行
        cleaned = re.sub(r'(-\s+.+?)\n\n+', r'\1\n', cleaned)

        # 5. 标准化代码块
        # 确保代码块有正确的缩进
        cleaned = re.sub(r'```\s*\n', '```\n', cleaned)
        cleaned = re.sub(r'\n\s*```', '\n```', cleaned)

        # 6. 移除前导和尾随空白
        cleaned = cleaned.strip()

        return cleaned

    def _get_content_stats(self, content: str) -> Dict[str, int]:
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
            'headings': len(re.findall(r'^#+\s+.+$', content, re.MULTILINE)),
            'lists': len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE)),
            'code_blocks': len(re.findall(r'^```', content, re.MULTILINE))
        }

    def _generate_concatenated_content(self, processed_files: List[Dict[str, Any]],
                                       include_toc: bool, title: Optional[str]) -> str:
        """生成合并后的内容

        Args:
            processed_files: 处理后的文件数据
            include_toc: 是否包含目录
            title: 文档标题

        Returns:
            str: 合并后的内容
        """
        parts = []

        # 文档标题
        doc_title = title or f"合并文档 ({datetime.now().strftime('%Y-%m-%d')})"
        parts.append(f'# {doc_title}\n')

        # 元信息
        parts.append(f'*生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}*')
        parts.append(f'*包含文件: {len(processed_files)} 个*\n')

        # 文件列表
        parts.append('## 文件列表\n')
        for i, file_data in enumerate(processed_files, 1):
            parts.append(f'{i}. **{file_data["title"]}** - {file_data["path"]}')

        parts.append('\n---\n')

        # 目录
        if include_toc and len(processed_files) > 1:
            parts.append('## 目录\n')
            for i, file_data in enumerate(processed_files, 1):
                anchor = file_data['title'].lower().replace(' ', '-')
                parts.append(f'{i}. [{file_data["title"]}](#{anchor})')
            parts.append('\n---\n')

        # 内容部分
        for i, file_data in enumerate(processed_files, 1):
            # 文件标题
            parts.append(f'## {file_data["title"]}\n')
            parts.append(f'*来源: {file_data["path"]}*\n')

            # 文件内容
            parts.append(file_data['content'])

            # 如果不是最后一个文件，添加分隔符
            if i < len(processed_files):
                parts.append('\n---\n\n')

        # 页脚
        parts.append('\n---\n')
        parts.append(f'*文档生成完成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')
        parts.append(f'*总计 {len(processed_files)} 个文件，{sum(f["stats"]["words"] for f in processed_files)} 字*')

        return '\n'.join(parts)

    def generate_html_content(self, concatenated_content: str, style: Optional[str] = None) -> str:
        """生成HTML格式的内容

        Args:
            concatenated_content: 合并后的Markdown内容
            style: 自定义CSS样式

        Returns:
            str: HTML内容
        """
        if style is None:
            style = '''
            <style>
                body {
                    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #2c3e50;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }
                h1 { border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { border-bottom: 1px solid #ddd; padding-bottom: 5px; }
                p { margin: 1em 0; }
                ul, ol { padding-left: 2em; }
                code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
                pre { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow: auto; }
                blockquote { border-left: 4px solid #3498db; margin: 1em 0; padding-left: 1em; color: #555; }
                .toc { background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .toc ul { list-style-type: none; padding-left: 1em; }
                .toc li { margin: 5px 0; }
                .toc a { text-decoration: none; color: #3498db; }
                .toc a:hover { text-decoration: underline; }
                .section { margin-bottom: 40px; }
                .section-header { background: #f0f7ff; padding: 10px 15px; border-left: 4px solid #3498db; margin-bottom: 15px; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #777; font-size: 0.9em; }
                .highlight { background-color: #fffacd; padding: 2px 4px; }
            </style>
            '''

        # 简单的Markdown转HTML（在实际应用中应使用markdown库）
        html_content = concatenated_content

        # 转换标题
        for i in range(6, 0, -1):
            html_content = re.sub(rf'^{"#" * i}\s+(.+)$', rf'<h{i}>\1</h{i}>', html_content, flags=re.MULTILINE)

        # 转换粗体和斜体
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)

        # 转换代码
        html_content = re.sub(r'`(.+?)`', r'<code>\1</code>', html_content)

        # 转换列表（简化版）
        lines = html_content.split('\n')
        in_list = False
        result_lines = []

        for line in lines:
            if line.startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)

        if in_list:
            result_lines.append('</ul>')

        html_content = '\n'.join(result_lines)

        # 包装HTML
        full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{doc_title if 'doc_title' in locals() else '合并文档'}</title>
    {style}
</head>
<body>
{html_content}
</body>
</html>'''

        return full_html


# 全局合并器实例
_concatenator_instance = ContentConcatenator()

# 便捷函数
def concatenate_files(files_data, include_toc=True, title=None):
    """合并文件"""
    return _concatenator_instance.concatenate_files(files_data, include_toc, title)

def generate_html_content(concatenated_content, style=None):
    """生成HTML内容"""
    return _concatenator_instance.generate_html_content(concatenated_content, style)