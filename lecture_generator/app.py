#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian 讲义生成器 - 主应用程序
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS

from config import Config
from obsidian_parser import ObsidianParser
from lecture_generator import LectureGenerator

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS

# 初始化组件
parser = ObsidianParser()
generator = LectureGenerator(parser)

# 确保输出目录存在
Config.init_output_dir()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/directory', methods=['GET'])
def get_directory():
    """获取Obsidian仓库的目录结构"""
    try:
        structure = parser.get_directory_structure()
        return jsonify({
            'success': True,
            'structure': structure,
            'obsidian_path': Config.OBSIDIAN_REPO
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/content', methods=['POST'])
def get_file_content():
    """获取文件内容（带过滤选项）"""
    data = request.json
    file_path = data.get('file_path')
    show_analysis = data.get('show_analysis', True)
    show_notes = data.get('show_notes', True)

    if not file_path:
        return jsonify({'success': False, 'error': '未指定文件路径'}), 400

    try:
        result = parser.read_markdown_file(
            file_path,
            show_analysis=show_analysis,
            show_notes=show_notes
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 404

        return jsonify({
            'success': True,
            'content': result['filtered_content'],
            'file_info': {
                'path': result['file_path'],
                'name': result['file_name'],
                'has_analysis': result['has_analysis'],
                'has_notes': result['has_notes']
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lecture/preview', methods=['POST'])
def preview_lecture():
    """预览讲义内容"""
    data = request.json
    file_paths = data.get('file_paths', [])
    show_analysis = data.get('show_analysis', True)
    show_notes = data.get('show_notes', True)

    if not file_paths:
        return jsonify({'success': False, 'error': '未选择任何文件'}), 400

    try:
        result = generator.preview_lecture(
            file_paths,
            show_analysis=show_analysis,
            show_notes=show_notes
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({
            'success': True,
            'preview': result['content'],
            'sections': result['sections'],
            'file_count': result['file_count']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lecture/generate', methods=['POST'])
def generate_lecture():
    """生成讲义文件"""
    data = request.json
    file_paths = data.get('file_paths', [])
    show_analysis = data.get('show_analysis', True)
    show_notes = data.get('show_notes', True)
    include_toc = data.get('include_toc', True)
    format = data.get('format', 'html')

    if not file_paths:
        return jsonify({'success': False, 'error': '未选择任何文件'}), 400

    try:
        result = generator.generate_lecture(
            file_paths,
            show_analysis=show_analysis,
            show_notes=show_notes,
            include_toc=include_toc,
            format=format
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        return jsonify({
            'success': True,
            'filename': result['filename'],
            'files_included': result['files_included'],
            'file_count': result['file_count'],
            'size': result['size']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lecture/download/<filename>', methods=['GET'])
def download_lecture(filename):
    """下载生成的讲义文件"""
    file_path = os.path.join(Config.OUTPUT_DIR, filename)

    if not os.path.exists(file_path):
        abort(404, description="文件不存在")

    # 安全检查：确保文件在输出目录中
    if not os.path.abspath(file_path).startswith(os.path.abspath(Config.OUTPUT_DIR)):
        abort(403, description="访问被拒绝")

    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        abort(500, description=f"下载失败: {str(e)}")

@app.route('/api/search', methods=['POST'])
def search_files():
    """搜索文件"""
    data = request.json
    keyword = data.get('keyword', '').strip()
    search_type = data.get('type', 'filename')  # 'filename' 或 'content'

    if not keyword:
        return jsonify({'success': False, 'error': '请输入搜索关键词'}), 400

    try:
        results = []

        for root, dirs, files in os.walk(Config.OBSIDIAN_REPO):
            for file in files:
                if not any(file.lower().endswith(ext) for ext in Config.MARKDOWN_EXTENSIONS):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, Config.OBSIDIAN_REPO)

                if search_type == 'filename':
                    # 搜索文件名
                    if keyword.lower() in file.lower():
                        results.append({
                            'path': relative_path,
                            'name': file,
                            'full_path': file_path
                        })
                else:
                    # 搜索文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if keyword.lower() in content.lower():
                                results.append({
                                    'path': relative_path,
                                    'name': file,
                                    'full_path': file_path,
                                    'contains_keyword': True
                                })
                    except:
                        continue

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    return jsonify({
        'success': True,
        'config': {
            'obsidian_path': Config.OBSIDIAN_REPO,
            'output_dir': Config.OUTPUT_DIR,
            'markdown_extensions': Config.MARKDOWN_EXTENSIONS
        }
    })

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({'success': False, 'error': '资源未找到'}), 404

@app.errorhandler(500)
def server_error(error):
    """处理500错误"""
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    print(f"Obsidian讲义生成器启动...")
    print(f"Obsidian仓库路径: {Config.OBSIDIAN_REPO}")
    print(f"输出目录: {Config.OUTPUT_DIR}")
    print(f"访问地址: http://{Config.HOST}:{Config.PORT}")
    print(f"按 Ctrl+C 停止服务")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )