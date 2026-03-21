# 知识库讲义生成器

一个简单而强大的Web应用程序，用于从任何知识库（包含Markdown文件的目录）生成自定义讲义。用户只需维护知识库，就可以在Web界面上根据大纲选取内容，控制是否显示【解析】或【注意】中的内容，最后生成属于自己的讲义。

## 🎯 项目特点

- **前后端统一**：使用Python Flask框架，前后端一体化
- **配置简单**：开箱即用，只需配置知识库路径
- **用户体验优秀**：直观的Web界面，实时预览功能
- **开发维护简单**：清晰的代码结构，易于扩展

## ✨ 核心功能

### 📁 文件管理
- 可视化浏览知识库目录结构
- 支持文件夹展开/折叠
- 文件多选和批量操作

### 🔍 内容控制
- 控制是否显示【解析】内容
- 控制是否显示【注意】内容
- 实时内容过滤和预览

### 📄 讲义生成
- 支持HTML和Markdown格式输出
- 可自定义是否包含目录
- 实时预览和即时下载


## 🚀 快速开始

### 方法二：手动安装

1. **安装依赖**
   ```bash
   pip install -r lecture_generator/requirements.txt
   ```

2. **检查配置**
   - `lecture_generator/config.json` 使用相对路径，可在 Windows / Linux / macOS 通用
   - 你也可以用环境变量覆盖：`KNOWLEDGE_BASE` 和 `OUTPUT_DIR`

3. **启动应用**
   ```bash
   python run.py
   ```
   
4. **访问界面**
   打开浏览器访问：http://localhost:5000

## 📋 使用流程

1. **选择文件**：在左侧文件树中勾选需要的文件
2. **配置选项**：设置是否显示【解析】/【注意】内容，选择输出格式
3. **预览内容**：点击"预览讲义"查看效果
4. **生成下载**：点击"生成讲义"并下载文件

## 🗂️ 项目结构

```
main.py                   # 主入口文件
run.py                    # 启动脚本
run_linux.sh              # Linux启动脚本
lecture_generator/
├── app.py                 # 主应用程序（Flask）
├── config.json            # 配置文件
├── requirements.txt       # Python依赖
├── core/                  # 核心模块
│   ├── md_parser.py        # Markdown解析
│   └── path_handler.py     # 配置与路径处理
├── templates/             # HTML模板
│   └── index.html         # 主界面
├── static/                # 静态资源
│   ├── css/
│   │   ├── style.css      # 样式表
│   │   └── all.min.css    # Font Awesome 图标
│   └── js/
│       ├── main.js        # 前端逻辑
│       ├── marked.min.js  # Markdown解析
│       └── purify.min.js  # HTML净化
└── output/                # 生成的讲义
```

## ⚙️ 技术栈

- **后端**：Python 3.6+，Flask框架
- **前端**：HTML5，CSS3，JavaScript
- **依赖**：
   - Flask：Web框架
   - Flask-CORS：跨域支持
   - markdown：Markdown解析

## 🔧 配置说明

主要配置在 `lecture_generator/config.json` 文件中：

```json
{
   "knowledge_base": "../knowledge_base",
   "output_dir": "./output",
   "markdown_extensions": [".md", ".markdown"]
}

可选环境变量覆盖：

- `KNOWLEDGE_BASE`：知识库绝对路径或相对路径
- `OUTPUT_DIR`：输出目录绝对路径或相对路径
```

## 🐛 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r lecture_generator/requirements.txt
   ```

2. **端口被占用**
   修改启动命令中的端口或在 `config.json` 中添加 `port`

3. **无法找到知识库**
   检查 `config.json` 中的 `knowledge_base` 是否正确，或使用 `KNOWLEDGE_BASE` 环境变量覆盖

4. **中文字符乱码**
   确保知识库文件使用UTF-8编码保存

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证。

## 🙏 致谢

感谢所有使用和贡献此项目的用户！

---

**开始使用吧！打开您的知识库，生成专属讲义！** 🎉

*让知识整理变得更简单，让学习变得更高效*
