import os
import time
import markdown
from datetime import datetime
from config import Config

class LectureGenerator:
    """讲义生成器"""

    def __init__(self, parser):
        """初始化生成器

        Args:
            parser: ObsidianParser实例
        """
        self.parser = parser
        Config.init_output_dir()

    def generate_lecture(self, file_paths, show_analysis=True, show_notes=True,
                         include_toc=True, format='html'):
        """生成讲义

        Args:
            file_paths: 要包含的文件路径列表
            show_analysis: 是否显示【解析】内容
            show_notes: 是否显示【注意】内容
            include_toc: 是否包含目录
            format: 输出格式，支持 'html', 'md'

        Returns:
            dict: 包含生成结果信息的字典
        """
        if not file_paths:
            return {'error': '未选择任何文件'}

        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'lecture_{timestamp}'

        # 读取并处理文件内容
        sections = []
        total_files = 0

        for file_path in file_paths:
            result = self.parser.read_markdown_file(
                file_path,
                show_analysis=show_analysis,
                show_notes=show_notes
            )

            if 'error' in result:
                continue

            sections.append({
                'title': result['file_name'].replace('.md', ''),
                'path': file_path,
                'content': result['filtered_content']
            })
            total_files += 1

        if total_files == 0:
            return {'error': '所有选中的文件都无法读取'}

        # 根据格式生成内容
        if format == 'html':
            content = self._generate_html(sections, include_toc)
            file_extension = '.html'
        else:  # markdown
            content = self._generate_markdown(sections, include_toc)
            file_extension = '.md'

        # 保存文件
        output_path = os.path.join(Config.OUTPUT_DIR, output_filename + file_extension)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'success': True,
                'filename': output_filename + file_extension,
                'path': output_path,
                'files_included': total_files,
                'file_count': len(file_paths),
                'size': os.path.getsize(output_path)
            }

        except Exception as e:
            return {'error': f'保存文件失败: {str(e)}'}

    def _generate_html(self, sections, include_toc):
        """生成HTML格式的讲义

        Args:
            sections: 章节列表
            include_toc: 是否包含目录

        Returns:
            str: HTML内容
        """
        html_parts = []

        # HTML头部
        html_parts.append('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>生成的讲义</title>
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
</head>
<body>
''')

        # 标题
        html_parts.append(f'''<h1>讲义</h1>
    <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
    <p>包含章节: {len(sections)} 个</p>
''')

        # 目录
        if include_toc and len(sections) > 1:
            html_parts.append('<div class="toc">')
            html_parts.append('<h2>目录</h2>')
            html_parts.append('<ul>')
            for i, section in enumerate(sections):
                html_parts.append(f'<li><a href="#section-{i}">{section["title"]}</a></li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')

        # 内容部分
        for i, section in enumerate(sections):
            html_parts.append(f'<div class="section">')
            html_parts.append(f'<div class="section-header" id="section-{i}">')
            html_parts.append(f'<h2>{section["title"]}</h2>')
            html_parts.append(f'<p><small>路径: {section["path"]}</small></p>')
            html_parts.append('</div>')

            # 转换Markdown为HTML
            md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
            html_content = md.convert(section['content'])
            html_parts.append(html_content)

            html_parts.append('</div>')

        # 页脚
        html_parts.append(f'''<div class="footer">
        <p>讲义生成完成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>包含 {len(sections)} 个章节</p>
    </div>
</body>
</html>''')

        return '\n'.join(html_parts)

    def _generate_markdown(self, sections, include_toc):
        """生成Markdown格式的讲义

        Args:
            sections: 章节列表
            include_toc: 是否包含目录

        Returns:
            str: Markdown内容
        """
        md_parts = []

        # 标题
        md_parts.append(f'# 讲义\n')
        md_parts.append(f'生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}\n')
        md_parts.append(f'包含章节: {len(sections)} 个\n')

        # 目录
        if include_toc and len(sections) > 1:
            md_parts.append('## 目录\n')
            for i, section in enumerate(sections):
                md_parts.append(f'{i+1}. [{section["title"]}](#{section["title"].replace(" ", "-").lower()})\n')

        # 内容部分
        for section in sections:
            md_parts.append(f'\n---\n\n')
            md_parts.append(f'## {section["title"]}\n')
            md_parts.append(f'*路径: {section["path"]}*\n\n')
            md_parts.append(section['content'])

        # 页脚
        md_parts.append(f'\n---\n\n')
        md_parts.append(f'*讲义生成完成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')
        md_parts.append(f'*包含 {len(sections)} 个章节*')

        return '\n'.join(md_parts)

    def preview_lecture(self, file_paths, show_analysis=True, show_notes=True):
        """预览讲义内容

        Args:
            file_paths: 要包含的文件路径列表
            show_analysis: 是否显示【解析】内容
            show_notes: 是否显示【注意】内容

        Returns:
            dict: 包含预览内容的字典
        """
        if not file_paths:
            return {'error': '未选择任何文件'}

        # 读取并处理文件内容
        sections = []
        total_files = 0

        for file_path in file_paths:
            result = self.parser.read_markdown_file(
                file_path,
                show_analysis=show_analysis,
                show_notes=show_notes
            )

            if 'error' in result:
                continue

            sections.append({
                'title': result['file_name'].replace('.md', ''),
                'path': file_path,
                'content': result['filtered_content'],
                'has_analysis': result['has_analysis'],
                'has_notes': result['has_notes']
            })
            total_files += 1

        if total_files == 0:
            return {'error': '所有选中的文件都无法读取'}

        # 生成预览
        preview_content = self._generate_markdown(sections, include_toc=False)

        return {
            'success': True,
            'sections': sections,
            'content': preview_content,
            'file_count': len(sections),
            'total_files': total_files
        }