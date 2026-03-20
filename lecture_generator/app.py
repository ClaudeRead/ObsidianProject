 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian 讲义生成器 - 优化版主应用程序
使用模块化架构，符合代码最少化原则
"""

import os
import re
from typing import List, Optional
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort

# 导入核心模块
from core.path_handler import validate_path, get_config, update_config
from core.md_parser import MarkdownParser

# 初始化Flask应用
app = Flask(__name__)

# 初始化模块
md_parser = MarkdownParser(clean_content=True)

def _normalize_include_tags(raw_value: object) -> Optional[List[str]]:
    if not isinstance(raw_value, list):
        return None

    cleaned = []
    seen = set()
    for item in raw_value:
        if not isinstance(item, str):
            continue
        tag = item.strip()
        if not tag or tag in seen:
            continue
        cleaned.append(tag)
        seen.add(tag)

    return cleaned

def _merge_detected_tags(existing: List[str], new_tags: List[str]) -> List[str]:
    seen = set(existing)
    merged = list(existing)
    for tag in new_tags:
        if tag in seen:
            continue
        merged.append(tag)
        seen.add(tag)
    return merged

def _is_within_base_path(base_path, target_path):
    try:
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        return os.path.commonpath([str(base), str(target)]) == str(base)
    except Exception:
        return False

# 确保输出目录存在
def init_output_directory(output_dir):
    """初始化输出目录"""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    return output_dir

# 初始化输出目录
init_output_directory(get_config().get('output_dir'))

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/directory', methods=['GET'])
def get_directory():
    """获取Obsidian仓库的目录结构"""
    try:
        config = get_config()
        knowledge_base_path = config.get('knowledge_base')

        if not os.path.exists(knowledge_base_path):
            return jsonify({
                'success': False,
                'error': f'知识库路径不存在: {knowledge_base_path}'
            }), 404

        # 扫描目录结构
        structure = []
        _scan_directory(knowledge_base_path, '', structure, config)

        return jsonify({
            'success': True,
            'structure': structure,
            'knowledge_base': knowledge_base_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search_files():
    """搜索文件名或内容"""
    data = request.json or {}
    keyword = (data.get('keyword') or '').strip()
    search_type = data.get('type', 'filename')

    if not keyword:
        return jsonify({'success': True, 'results': [], 'count': 0})

    config = get_config()
    knowledge_base_path = config.get('knowledge_base')
    extensions = config.get('markdown_extensions', ['.md', '.markdown'])

    if not knowledge_base_path or not os.path.exists(knowledge_base_path):
        return jsonify({'success': False, 'error': '仓库路径不存在'}), 404

    keyword_lower = keyword.lower()
    results = []

    for root, _, files in os.walk(knowledge_base_path):
        for filename in files:
            if not any(filename.lower().endswith(ext) for ext in extensions):
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, knowledge_base_path).replace('\\', '/')

            if search_type == 'filename':
                if keyword_lower in filename.lower():
                    results.append({'path': rel_path})
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if keyword_lower in content.lower():
                    results.append({'path': rel_path})
            except Exception:
                continue

    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/image/<path:relative_path>', methods=['GET'])
def get_image(relative_path):
    """提供Obsidian仓库内图片访问"""
    from urllib.parse import unquote
    config = get_config()
    knowledge_base_path = config.get('knowledge_base')

    if not knowledge_base_path:
        abort(404, description="图片不存在")

    # 对URL编码的路径进行解码，处理包含空格等特殊字符的情况
    relative_path = unquote(relative_path)
    base_path = Path(knowledge_base_path)
    target_path = Path(knowledge_base_path) / relative_path

    if not _is_within_base_path(base_path, target_path):
        abort(403, description="访问被拒绝")

    if not os.path.isfile(target_path):
        abort(404, description="图片不存在")

    allowed_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.tiff'}
    if os.path.splitext(target_path)[1].lower() not in allowed_exts:
        abort(403, description="不支持的文件类型")

    return send_file(target_path)

def _scan_directory(current_path, relative_path, structure, config):
    """递归扫描目录"""
    try:
        items = sorted(os.listdir(current_path))
    except Exception as e:
        print(f"无法读取目录 {current_path}: {e}")
        return

    for item in items:
        if item.lower() == 'image':
            continue
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
                'children': [],
                'expanded': False
            })

            # 递归扫描子目录
            child_index = len(structure) - 1
            _scan_directory(item_path, relative_item_path, structure[child_index]['children'], config)

        elif any(item.lower().endswith(ext) for ext in config.get('markdown_extensions', ['.md', '.markdown'])):
            # 是Markdown文件
            structure.append({
                'type': 'file',
                'name': item,
                'path': relative_item_path,
                'size': os.path.getsize(item_path)
            })

def _generate_simplified_lecture(files_data, include_toc=False):
    """生成简化版讲义（不显示生成时间、文件列表、来源等元信息）

    Args:
        files_data: 文件数据列表，每个元素应包含 'title' 和 'content'
        include_toc: 是否包含目录

    Returns:
        dict: 生成结果
    """
    if not files_data:
        return {'error': '没有可合并的文件数据'}

    parts = []
    current_section = None

    # 如果包含目录，在顶部添加
    if include_toc and len(files_data) > 1:
        toc_parts = ['## 目录\n']
        for file_data in files_data:
            anchor = file_data['title'].lower().replace(' ', '-').replace('.', '-')
            toc_parts.append(f'- [{file_data["title"]}](#{anchor})')
        toc_parts.append('\n---\n')
        parts = toc_parts + parts

    # 内容部分（直接拼接，不添加额外信息）
    for i, file_data in enumerate(files_data):
        section_name = Path(file_data.get('path', '')).parent.name
        if section_name and section_name != '.' and section_name != current_section:
            parts.append(f'# {section_name}\n\n')
            current_section = section_name

        # 添加标题（使用h1标题作为模块标题）
        # 确保标题格式正确，避免重复
        title = file_data.get('title', '').strip()
        if title:
            # 检查内容是否已经有相同的标题，避免重复
            content_start = file_data['content'].strip()
            if not (content_start.startswith(f'# {title}') or content_start.startswith(f'## {title}')):
                parts.append(f'## {title}\n\n')

        # 添加内容（已经经过清理，不含文件名和路径信息）
        parts.append(file_data['content'])

        # 如果不是最后一个文件，添加分隔符
        if i < len(files_data) - 1:
            parts.append('\n\n---\n\n')

    lecture_content = '\n'.join(parts)

    return {
        'success': True,
        'lecture_content': lecture_content,
        'files_processed': len(files_data),
        'files_skipped': 0,
        'total_files': len(files_data)
    }


def _normalize_image_relative_path(api_image_url):
    """将 /api/image/... 转为相对路径，防止路径穿越"""
    from urllib.parse import unquote

    if not api_image_url.startswith('/api/image/'):
        return None

    raw_path = unquote(api_image_url.replace('/api/image/', '', 1))
    normalized = raw_path.replace('\\', '/').lstrip('/').lstrip('./')

    if normalized.startswith('..') or normalized.startswith('/'):
        return None

    normalized = os.path.normpath(normalized).replace('\\', '/')
    if normalized.startswith('..'):
        return None

    return normalized


def _build_image_data_uri(knowledge_base_path, api_image_url):
    """将 /api/image/... 转为 data URI"""
    import base64
    import mimetypes

    rel_path = _normalize_image_relative_path(api_image_url)
    if not rel_path:
        return None

    source_path = Path(knowledge_base_path) / rel_path
    base_path = Path(knowledge_base_path)

    if not _is_within_base_path(base_path, source_path):
        return None

    if not source_path.is_file():
        return None

    mime_type, _ = mimetypes.guess_type(str(source_path))
    if not mime_type:
        mime_type = 'application/octet-stream'

    try:
        data = source_path.read_bytes()
    except Exception:
        return None

    encoded = base64.b64encode(data).decode('ascii')
    return f'data:{mime_type};base64,{encoded}'

def _convert_markdown_to_html(markdown_content, image_url_transform=None):
    """将Markdown内容转换为HTML

    Args:
        markdown_content: Markdown内容

    Returns:
        str: HTML内容
    """
    try:
        import markdown
        # 创建Markdown转换器
        md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
        html_content = md.convert(markdown_content)
        html_content = _sanitize_html(html_content)

        # 处理图片路径，确保在生成的HTML中也能正确显示
        import re

        def normalize_image_src(src):
            if not image_url_transform:
                return None
            return image_url_transform(src)

        def replace_img_tag(match):
            src = match.group(1)
            new_src = normalize_image_src(src)
            if not new_src:
                return match.group(0)
            return match.group(0).replace(src, new_src)

        def replace_markdown_image(match):
            alt = match.group(1)
            src = match.group(2)
            return f'<img src="{normalize_image_src(src) or src}" alt="{alt}">'

        # 处理img标签（兼容属性顺序）
        html_content = re.sub(r'<img[^>]*\bsrc="([^"]+)"[^>]*>', replace_img_tag, html_content)
        # 处理Markdown格式的图片（兜底）
        html_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_markdown_image, html_content)

        # 包装成完整HTML文档
        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>讲义</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        p {{ margin: 1em 0; }}
        ul, ol {{ padding-left: 2em; }}
        code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f8f8f8; padding: 15px; border-radius: 5px; overflow: auto; }}
        blockquote {{ border-left: 4px solid #3498db; margin: 1em 0; padding-left: 1em; color: #555; }}
        .toc {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .toc ul {{ list-style-type: none; padding-left: 1em; }}
        .toc li {{ margin: 5px 0; }}
        .toc a {{ text-decoration: none; color: #3498db; }}
        .toc a:hover {{ text-decoration: underline; }}
        .section {{ margin-bottom: 40px; }}
        .section-header {{ background: #f0f7ff; padding: 10px 15px; border-left: 4px solid #3498db; margin-bottom: 15px; }}
        .highlight {{ background-color: #fffacd; padding: 2px 4px; }}
        img {{ max-width: 100%; height: auto; margin: 1em 0; border-radius: 5px; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''

        return html_template

    except ImportError:
        # 如果markdown库不可用，使用简单转换
        import re

        # 简单的Markdown转HTML（基础功能）
        html = markdown_content

        # 转换标题
        for i in range(6, 0, -1):
            html = re.sub(rf'^{"#" * i}\s+(.+)$', rf'<h{i}>\1</h{i}>', html, flags=re.MULTILINE)

        # 转换粗体和斜体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # 转换代码
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

        # 处理图片路径
        def normalize_image_src(src):
            if not image_url_transform:
                return None
            return image_url_transform(src)

        def replace_image_path(match):
            alt = match.group(1)
            src = match.group(2)
            return f'<img src="{normalize_image_src(src) or src}" alt="{alt}">'

        # 转换图片
        html = re.sub(r'!\[([^\]]+)\]\(([^)]+)\)', replace_image_path, html)

        # 转换链接
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

        # 转换列表（简化版）
        lines = html.split('\n')
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

        html = '\n'.join(result_lines)
        html = _sanitize_html(html)

        # 包装成完整HTML文档
        simple_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>讲义</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        p {{ margin: 1em 0; }}
        ul {{ padding-left: 2em; }}
        code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
        img {{ max-width: 100%; height: auto; margin: 1em 0; border-radius: 5px; }}
    </style>
</head>
<body>
{html}
</body>
</html>'''

        return simple_html

def _sanitize_html(html_content):
    """最小化清理HTML，移除脚本与危险属性"""
    if not html_content:
        return html_content

    cleaned = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'\son\w+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s(href|src)\s*=\s*(["\'])\s*javascript:[^\2]*\2', '', cleaned, flags=re.IGNORECASE)
    return cleaned

@app.route('/api/lecture/preview', methods=['POST'])
def preview_lecture():
    """预览讲义内容"""
    data = request.json or {}
    file_paths = data.get('file_paths', [])
    show_analysis = data.get('show_analysis', True)
    show_notes = data.get('show_notes', True)
    include_tags = _normalize_include_tags(data.get('include_tags'))

    if not file_paths:
        return jsonify({'success': False, 'error': '未选择任何文件'}), 400

    try:
        config = get_config()
        knowledge_base_path = config.get('knowledge_base')
        files_data = []
        detected_tags = []

        for file_path in file_paths:
            full_path = os.path.join(knowledge_base_path, file_path)

            # 解析文件
            result = md_parser.parse_file(
                full_path,
                show_analysis=show_analysis,
                show_notes=show_notes,
                obsidian_root=knowledge_base_path,
                include_tags=include_tags
            )

            if 'error' not in result:
                detected_tags = _merge_detected_tags(
                    detected_tags,
                    result.get('detected_tags', [])
                )
                files_data.append({
                    'title': result.get('h1_title', os.path.basename(file_path).replace('.md', '')),
                    'path': file_path,
                    'content': result['parsed_content'],
                    'hash': result['content_hash']
                })

        if not files_data:
            return jsonify({'success': False, 'error': '所有选中的文件都无法读取'}), 400

        # 合并内容 - 使用简化模式（不显示元信息）
        concat_result = _generate_simplified_lecture(files_data, include_toc=False)

        if 'error' in concat_result:
            return jsonify({'success': False, 'error': concat_result['error']}), 400

        return jsonify({
            'success': True,
            'preview': concat_result['lecture_content'],
            'files_processed': concat_result['files_processed'],
            'files_skipped': concat_result['files_skipped'],
            'file_count': len(files_data),
            'detected_tags': detected_tags
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lecture/generate', methods=['POST'])
def generate_lecture():
    """生成讲义文件"""
    data = request.json or {}
    file_paths = data.get('file_paths', [])
    show_analysis = data.get('show_analysis', True)
    show_notes = data.get('show_notes', True)
    include_tags = _normalize_include_tags(data.get('include_tags'))
    include_toc = data.get('include_toc', True)
    format = data.get('format', 'html')
    filename_input = data.get('filename', '').strip() if data else ''

    if not file_paths:
        return jsonify({'success': False, 'error': '未选择任何文件'}), 400

    try:
        config = get_config()
        knowledge_base_path = config.get('knowledge_base')
        files_data = []

        for file_path in file_paths:
            full_path = os.path.join(knowledge_base_path, file_path)

            # 解析文件
            result = md_parser.parse_file(
                full_path,
                show_analysis=show_analysis,
                show_notes=show_notes,
                obsidian_root=knowledge_base_path,
                include_tags=include_tags
            )

            if 'error' not in result:
                files_data.append({
                    'title': result.get('h1_title', os.path.basename(file_path).replace('.md', '')),
                    'path': file_path,
                    'content': result['parsed_content'],
                    'hash': result['content_hash']
                })

        if not files_data:
            return jsonify({'success': False, 'error': '所有选中的文件都无法读取'}), 400

        # 合并内容 - 使用简化模式
        concat_result = _generate_simplified_lecture(files_data, include_toc=include_toc)

        if 'error' in concat_result:
            return jsonify({'success': False, 'error': concat_result['error']}), 400

        # 生成文件名
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        safe_filename = ''
        if filename_input:
            base_name = os.path.splitext(os.path.basename(filename_input))[0]
            safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', base_name).strip(' ._')

        if not safe_filename:
            safe_filename = f'lecture_{timestamp}'

        # 保存目录
        output_dir = config.get('output_dir')
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        def image_url_transform(src):
            if not src.startswith('/api/image/'):
                return None
            return _build_image_data_uri(knowledge_base_path, src)

        if format == 'html':
            # 生成HTML内容
            html_content = _convert_markdown_to_html(
                concat_result['lecture_content'],
                image_url_transform=image_url_transform
            )
            filename = f'{safe_filename}.html'
            content_to_save = html_content
        else:
            # Markdown格式
            filename = f'{safe_filename}.md'
            content_to_save = concat_result['lecture_content']

        output_path = os.path.join(output_dir, filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content_to_save)

        return jsonify({
            'success': True,
            'filename': filename,
            'files_included': concat_result['files_processed'],
            'file_count': len(files_data),
            'size': os.path.getsize(output_path)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lecture/download/<path:filename>', methods=['GET'])
def download_lecture(filename):
    """下载生成的讲义文件"""
    config = get_config()
    output_dir = config.get('output_dir')
    file_path = Path(output_dir) / filename

    if not file_path.exists():
        abort(404, description="文件不存在")

    # 安全检查：确保文件在输出目录中
    if not _is_within_base_path(output_dir, file_path):
        abort(403, description="访问被拒绝")

    try:
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        abort(500, description=f"下载失败: {str(e)}")

@app.route('/api/config', methods=['GET'])
def get_config_api():
    """获取配置信息"""
    return jsonify({
        'success': True,
        'config': get_config()
    })

@app.route('/api/config/validate', methods=['POST'])
def validate_config():
    """验证配置路径"""
    try:
        data = request.json
        if not data or 'knowledge_base' not in data:
            return jsonify({'success': False, 'error': '缺少路径参数'}), 400

        is_valid, message = validate_path(data['knowledge_base'])
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': message
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/browse', methods=['POST'])
def browse_config_path():
    """打开系统目录选择对话框"""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        selected = filedialog.askdirectory()
        root.destroy()

        if not selected:
            return jsonify({'success': False, 'error': '已取消选择'}), 400

        return jsonify({'success': True, 'path': selected})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/update', methods=['POST'])
def update_config_api():
    """更新配置信息"""
    try:
        data = request.json
        if not data or 'knowledge_base' not in data:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        # 验证路径
        is_valid, message = validate_path(data['knowledge_base'])
        if not is_valid:
            return jsonify({'success': False, 'error': message}), 400

        # 更新配置
        success = update_config('knowledge_base', data['knowledge_base'])
        if success:
            return jsonify({'success': True, 'message': '配置已更新'})
        else:
            return jsonify({'success': False, 'error': '保存配置失败'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({'success': False, 'error': '资源未找到'}), 404

@app.errorhandler(500)
def server_error(error):
    """处理500错误"""
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    config = get_config()
    print(f"Obsidian讲义生成器（优化版）启动...")
    print(f"Obsidian仓库路径: {config.get('obsidian_repo')}")
    print(f"输出目录: {config.get('output_dir')}")
    print(f"访问地址: http://{config.get('host', '0.0.0.0')}:{config.get('port', 5000)}")
    print(f"按 Ctrl+C 停止服务")

    app.run(
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 5000),
        debug=config.get('debug', False)
    )