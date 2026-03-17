/**
 * Obsidian 讲义生成器 - 主JavaScript文件
 */

class LectureGeneratorApp {
    constructor() {
        this.selectedFiles = new Set();
        this.directoryStructure = null;
        this.isLoading = false;

        // 初始化
        this.initElements();
        this.bindEvents();
        this.loadDirectory();
        this.updateInfoPanel();
    }

    /**
     * 初始化DOM元素
     */
    initElements() {
        // 按钮和交互元素
        this.elements = {
            // 文件树相关
            fileTree: document.getElementById('file-tree'),
            selectedList: document.getElementById('selected-list'),
            selectedCount: document.getElementById('selected-count'),
            infoSelectedCount: document.getElementById('info-selected-count'),

            // 搜索相关
            searchInput: document.getElementById('search-input'),
            searchType: document.getElementById('search-type'),
            searchBtn: document.getElementById('search-btn'),

            // 操作按钮
            refreshBtn: document.getElementById('refresh-btn'),
            collapseAllBtn: document.getElementById('collapse-all-btn'),
            expandAllBtn: document.getElementById('expand-all-btn'),
            clearSelectedBtn: document.getElementById('clear-selected'),

            // 配置选项
            showAnalysis: document.getElementById('show-analysis'),
            showNotes: document.getElementById('show-notes'),
            includeToc: document.getElementById('include-toc'),
            formatRadios: document.querySelectorAll('input[name="format"]'),

            // 预览相关
            previewBtn: document.getElementById('preview-btn'),
            generateBtn: document.getElementById('generate-btn'),
            copyPreviewBtn: document.getElementById('copy-preview'),
            clearPreviewBtn: document.getElementById('clear-preview'),
            previewContent: document.getElementById('preview-content'),

            // 信息面板
            obsidianPath: document.getElementById('obsidian-path'),
            infoDisplayOptions: document.getElementById('info-display-options'),
            infoFormat: document.getElementById('info-format'),

            // 状态和计数
            status: document.getElementById('status'),
            fileCount: document.getElementById('file-count'),

            // 加载指示器
            loadingOverlay: document.getElementById('loading-overlay'),
            loadingMessage: document.getElementById('loading-message'),

            // 消息提示
            messageToast: document.getElementById('message-toast'),

            // 下载对话框
            downloadModal: document.getElementById('download-modal'),
            downloadFilename: document.getElementById('download-filename'),
            downloadFilecount: document.getElementById('download-filecount'),
            downloadBtn: document.getElementById('download-btn'),
            closeModalBtn: document.getElementById('close-modal')
        };
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 搜索功能
        this.elements.searchBtn.addEventListener('click', () => this.searchFiles());
        this.elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchFiles();
        });

        // 文件树操作
        this.elements.refreshBtn.addEventListener('click', () => this.loadDirectory());
        this.elements.collapseAllBtn.addEventListener('click', () => this.collapseAll());
        this.elements.expandAllBtn.addEventListener('click', () => this.expandAll());
        this.elements.clearSelectedBtn.addEventListener('click', () => this.clearSelected());

        // 配置选项变化
        this.elements.showAnalysis.addEventListener('change', () => this.updateInfoPanel());
        this.elements.showNotes.addEventListener('change', () => this.updateInfoPanel());
        this.elements.includeToc.addEventListener('change', () => this.updateInfoPanel());
        this.elements.formatRadios.forEach(radio => {
            radio.addEventListener('change', () => this.updateInfoPanel());
        });

        // 预览和生成功能
        this.elements.previewBtn.addEventListener('click', () => this.previewLecture());
        this.elements.generateBtn.addEventListener('click', () => this.generateLecture());
        this.elements.copyPreviewBtn.addEventListener('click', () => this.copyPreview());
        this.elements.clearPreviewBtn.addEventListener('click', () => this.clearPreview());

        // 下载对话框
        this.elements.downloadBtn.addEventListener('click', () => this.downloadGeneratedFile());
        this.elements.closeModalBtn.addEventListener('click', () => this.hideModal());

        // 点击模态框外部关闭
        this.elements.downloadModal.addEventListener('click', (e) => {
            if (e.target === this.elements.downloadModal) {
                this.hideModal();
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal();
            }
        });
    }

    /**
     * 显示加载指示器
     * @param {string} message - 加载消息
     */
    showLoading(message = '正在处理...') {
        this.isLoading = true;
        this.elements.loadingMessage.textContent = message;
        this.elements.loadingOverlay.style.display = 'flex';
        this.setStatus('处理中...');
    }

    /**
     * 隐藏加载指示器
     */
    hideLoading() {
        this.isLoading = false;
        this.elements.loadingOverlay.style.display = 'none';
        this.setStatus('就绪');
    }

    /**
     * 显示消息提示
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型: 'success', 'error', 'warning'
     * @param {number} duration - 显示时长(毫秒)
     */
    showMessage(message, type = 'info', duration = 3000) {
        const toast = this.elements.messageToast;
        toast.textContent = message;
        toast.className = `toast ${type}`;

        // 显示消息
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // 隐藏消息
        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    /**
     * 设置状态信息
     * @param {string} status - 状态文本
     */
    setStatus(status) {
        this.elements.status.textContent = status;
    }

    /**
     * 更新信息面板
     */
    updateInfoPanel() {
        const showAnalysis = this.elements.showAnalysis.checked;
        const showNotes = this.elements.showNotes.checked;
        const includeToc = this.elements.includeToc.checked;

        // 获取选中的格式
        let selectedFormat = 'HTML';
        this.elements.formatRadios.forEach(radio => {
            if (radio.checked) {
                selectedFormat = radio.value.toUpperCase();
            }
        });

        this.elements.infoSelectedCount.textContent = this.selectedFiles.size;
        this.elements.infoDisplayOptions.textContent =
            `解析: ${showAnalysis ? '是' : '否'}, 注意: ${showNotes ? '是' : '否'}`;
        this.elements.infoFormat.textContent = selectedFormat;
    }

    /**
     * 加载目录结构
     */
    async loadDirectory() {
        this.showLoading('正在加载目录结构...');

        try {
            const response = await fetch('/api/directory');
            const data = await response.json();

            if (data.success) {
                this.directoryStructure = data.structure;
                this.renderDirectoryTree();
                this.updateFileCount(data.structure);
                this.elements.obsidianPath.textContent = data.obsidian_path;
                this.showMessage('目录加载成功', 'success');
            } else {
                this.showMessage(`加载失败: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('加载目录失败:', error);
            this.showMessage('网络错误，请检查服务器连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 更新文件计数
     * @param {Array} structure - 目录结构
     */
    updateFileCount(structure) {
        let fileCount = 0;

        const countFiles = (items) => {
            items.forEach(item => {
                if (item.type === 'file') {
                    fileCount++;
                } else if (item.type === 'directory' && item.children) {
                    countFiles(item.children);
                }
            });
        };

        countFiles(structure);
        this.elements.fileCount.textContent = `文件总数: ${fileCount}`;
    }

    /**
     * 渲染目录树
     */
    renderDirectoryTree() {
        if (!this.directoryStructure) return;

        const treeContainer = this.elements.fileTree;
        treeContainer.innerHTML = '';

        const renderItem = (item, depth = 0, parentElement = treeContainer) => {
            const div = document.createElement('div');
            div.className = 'tree-item';

            if (item.type === 'directory') {
                div.innerHTML = `
                    <div class="tree-header" data-depth="${depth}" data-path="${item.path}">
                        <i class="fas fa-caret-right"></i>
                        <i class="fas fa-folder"></i>
                        <span class="directory-name">${item.name}</span>
                    </div>
                    <div class="tree-children" style="display: none;"></div>
                `;

                // 绑定目录点击事件
                const header = div.querySelector('.tree-header');
                const childrenContainer = div.querySelector('.tree-children');

                header.addEventListener('click', (e) => {
                    const icon = header.querySelector('.fa-caret-right');
                    const children = header.nextElementSibling;

                    if (children.style.display === 'none') {
                        icon.classList.replace('fa-caret-right', 'fa-caret-down');
                        children.style.display = 'block';
                    } else {
                        icon.classList.replace('fa-caret-down', 'fa-caret-right');
                        children.style.display = 'none';
                    }
                });

                parentElement.appendChild(div);

                // 递归渲染子项
                if (item.children && item.children.length > 0) {
                    item.children.forEach(child => {
                        renderItem(child, depth + 1, childrenContainer);
                    });
                }

            } else if (item.type === 'file') {
                const isSelected = this.selectedFiles.has(item.path);
                div.innerHTML = `
                    <div class="file-item" data-path="${item.path}">
                        <input type="checkbox" class="file-checkbox" ${isSelected ? 'checked' : ''}>
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">${item.name}</span>
                    </div>
                `;

                // 绑定文件点击事件
                const fileItem = div.querySelector('.file-item');
                const checkbox = div.querySelector('.file-checkbox');

                fileItem.addEventListener('click', (e) => {
                    // 如果点击的不是复选框，则切换复选框状态
                    if (e.target !== checkbox && !checkbox.contains(e.target)) {
                        checkbox.checked = !checkbox.checked;
                        // 使用更新后的状态
                        this.toggleFileSelection(item.path, item.name, checkbox.checked);
                    }
                });

                checkbox.addEventListener('change', (e) => {
                    // 使用change事件，而不是click事件
                    this.toggleFileSelection(item.path, item.name, checkbox.checked);
                });

                parentElement.appendChild(div);
            }
        };

        // 渲染所有项
        this.directoryStructure.forEach(item => {
            renderItem(item);
        });
    }

    /**
     * 切换文件选择状态
     * @param {string} filePath - 文件路径
     * @param {string} fileName - 文件名
     * @param {boolean} isSelected - 是否选中
     */
    toggleFileSelection(filePath, fileName, isSelected) {
        if (isSelected) {
            this.selectedFiles.add(filePath);
            this.addToSelectedList(filePath, fileName);
        } else {
            this.selectedFiles.delete(filePath);
            this.removeFromSelectedList(filePath);
        }

        this.updateSelectedCount();
        this.updateInfoPanel();
    }

    /**
     * 添加到已选择列表
     * @param {string} filePath - 文件路径
     * @param {string} fileName - 文件名
     */
    addToSelectedList(filePath, fileName) {
        const selectedList = this.elements.selectedList;

        // 移除空消息
        const emptyMessage = selectedList.querySelector('.empty-message');
        if (emptyMessage) {
            emptyMessage.remove();
        }

        // 检查是否已存在
        const existingItem = selectedList.querySelector(`[data-path="${filePath}"]`);
        if (existingItem) return;

        const item = document.createElement('div');
        item.className = 'selected-item';
        item.dataset.path = filePath;
        item.innerHTML = `
            <span>${fileName}</span>
            <i class="fas fa-times" title="移除"></i>
        `;

        // 绑定移除事件
        const removeBtn = item.querySelector('.fa-times');
        removeBtn.addEventListener('click', () => {
            this.toggleFileSelection(filePath, fileName, false);
            // 更新文件树中的复选框状态
            const fileCheckbox = document.querySelector(`.file-item[data-path="${filePath}"] .file-checkbox`);
            if (fileCheckbox) {
                fileCheckbox.checked = false;
            }
        });

        selectedList.appendChild(item);
    }

    /**
     * 从已选择列表移除
     * @param {string} filePath - 文件路径
     */
    removeFromSelectedList(filePath) {
        const item = this.elements.selectedList.querySelector(`[data-path="${filePath}"]`);
        if (item) {
            item.remove();
        }

        // 如果列表为空，显示空消息
        if (this.selectedFiles.size === 0) {
            const emptyMessage = document.createElement('p');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = '暂无选择的文件';
            this.elements.selectedList.appendChild(emptyMessage);
        }
    }

    /**
     * 更新已选择计数
     */
    updateSelectedCount() {
        const count = this.selectedFiles.size;
        this.elements.selectedCount.textContent = count;
        this.elements.infoSelectedCount.textContent = count;
    }

    /**
     * 清空已选择
     */
    clearSelected() {
        // 清除文件树中的复选框状态
        document.querySelectorAll('.file-checkbox:checked').forEach(checkbox => {
            checkbox.checked = false;
        });

        // 清空选择集和列表
        this.selectedFiles.clear();
        this.elements.selectedList.innerHTML = '<p class="empty-message">暂无选择的文件</p>';
        this.updateSelectedCount();
        this.updateInfoPanel();

        this.showMessage('已清空所有选择', 'success');
    }

    /**
     * 折叠所有目录
     */
    collapseAll() {
        document.querySelectorAll('.tree-children').forEach(el => {
            el.style.display = 'none';
        });
        document.querySelectorAll('.fa-caret-down').forEach(icon => {
            icon.classList.replace('fa-caret-down', 'fa-caret-right');
        });
    }

    /**
     * 展开所有目录
     */
    expandAll() {
        document.querySelectorAll('.tree-children').forEach(el => {
            el.style.display = 'block';
        });
        document.querySelectorAll('.fa-caret-right').forEach(icon => {
            icon.classList.replace('fa-caret-right', 'fa-caret-down');
        });
    }

    /**
     * 搜索文件
     */
    async searchFiles() {
        const keyword = this.elements.searchInput.value.trim();
        const searchType = this.elements.searchType.value;

        if (!keyword) {
            this.showMessage('请输入搜索关键词', 'warning');
            return;
        }

        this.showLoading(`正在搜索: ${keyword}`);

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: keyword,
                    type: searchType
                })
            });

            const data = await response.json();

            if (data.success) {
                if (data.results.length > 0) {
                    this.displaySearchResults(data.results, keyword);
                    this.showMessage(`找到 ${data.count} 个匹配项`, 'success');
                } else {
                    this.showMessage('未找到匹配的文件', 'warning');
                }
            } else {
                this.showMessage(`搜索失败: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.showMessage('搜索失败，请检查网络连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 显示搜索结果
     * @param {Array} results - 搜索结果
     * @param {string} keyword - 搜索关键词
     */
    displaySearchResults(results, keyword) {
        const treeContainer = this.elements.fileTree;
        const searchResultsHTML = results.map(result => {
            const pathParts = result.path.split('/');
            const fileName = pathParts.pop();
            const isSelected = this.selectedFiles.has(result.path);

            return `
                <div class="tree-item">
                    <div class="file-item" data-path="${result.path}">
                        <input type="checkbox" class="file-checkbox" ${isSelected ? 'checked' : ''}>
                        <i class="fas fa-file-alt"></i>
                        <span class="file-name">${fileName}</span>
                        <span class="search-highlight">${pathParts.join('/')}</span>
                    </div>
                </div>
            `;
        }).join('');

        treeContainer.innerHTML = `
            <div class="search-results">
                <div class="search-header">
                    <h4>搜索结果: "${keyword}" (${results.length} 个)</h4>
                    <button id="back-to-tree" class="btn btn-small">
                        <i class="fas fa-arrow-left"></i> 返回目录树
                    </button>
                </div>
                <div class="results-list">
                    ${searchResultsHTML}
                </div>
            </div>
        `;

        // 绑定返回按钮事件
        document.getElementById('back-to-tree').addEventListener('click', () => {
            this.renderDirectoryTree();
        });

        // 绑定搜索结果中的文件选择事件
        document.querySelectorAll('.search-results .file-item').forEach(item => {
            const filePath = item.dataset.path;
            const fileName = item.querySelector('.file-name').textContent;
            const checkbox = item.querySelector('.file-checkbox');

            item.addEventListener('click', (e) => {
                if (e.target !== checkbox && !checkbox.contains(e.target)) {
                    checkbox.checked = !checkbox.checked;
                    this.toggleFileSelection(filePath, fileName, checkbox.checked);
                }
            });

            checkbox.addEventListener('change', (e) => {
                this.toggleFileSelection(filePath, fileName, checkbox.checked);
            });
        });
    }

    /**
     * 预览讲义
     */
    async previewLecture() {
        if (this.selectedFiles.size === 0) {
            this.showMessage('请先选择要生成讲义的文件', 'warning');
            return;
        }

        this.showLoading('正在生成预览...');

        try {
            const response = await fetch('/api/lecture/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_paths: Array.from(this.selectedFiles),
                    show_analysis: this.elements.showAnalysis.checked,
                    show_notes: this.elements.showNotes.checked
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayPreview(data.preview);
                this.showMessage(`预览生成成功，包含 ${data.file_count} 个文件`, 'success');
            } else {
                this.showMessage(`预览失败: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('预览失败:', error);
            this.showMessage('预览失败，请检查网络连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 显示预览内容
     * @param {string} content - 预览内容
     */
    displayPreview(content) {
        const previewContent = this.elements.previewContent;

        // 简单地将Markdown转换为HTML（使用内置的转换）
        const htmlContent = marked.parse(content, {
            breaks: true,
            gfm: true,
            headerIds: true
        });

        previewContent.innerHTML = htmlContent;
    }

    /**
     * 清空预览
     */
    clearPreview() {
        this.elements.previewContent.innerHTML = `
            <div class="empty-preview">
                <i class="fas fa-file-alt fa-3x"></i>
                <p>预览将显示在这里</p>
                <p class="small-text">选择文件并点击"预览讲义"按钮</p>
            </div>
        `;
    }

    /**
     * 复制预览内容
     */
    async copyPreview() {
        const previewContent = this.elements.previewContent.textContent;

        if (!previewContent || previewContent.includes('预览将显示在这里')) {
            this.showMessage('没有可复制的内容', 'warning');
            return;
        }

        try {
            await navigator.clipboard.writeText(previewContent);
            this.showMessage('预览内容已复制到剪贴板', 'success');
        } catch (error) {
            console.error('复制失败:', error);
            this.showMessage('复制失败，请手动选择并复制', 'error');
        }
    }

    /**
     * 生成讲义
     */
    async generateLecture() {
        if (this.selectedFiles.size === 0) {
            this.showMessage('请先选择要生成讲义的文件', 'warning');
            return;
        }

        this.showLoading('正在生成讲义...');

        try {
            // 获取选中的格式
            let selectedFormat = 'html';
            this.elements.formatRadios.forEach(radio => {
                if (radio.checked) {
                    selectedFormat = radio.value;
                }
            });

            const response = await fetch('/api/lecture/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_paths: Array.from(this.selectedFiles),
                    show_analysis: this.elements.showAnalysis.checked,
                    show_notes: this.elements.showNotes.checked,
                    include_toc: this.elements.includeToc.checked,
                    format: selectedFormat
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showDownloadModal(data);
                this.showMessage(`讲义生成成功: ${data.filename}`, 'success');
            } else {
                this.showMessage(`生成失败: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('生成失败:', error);
            this.showMessage('生成失败，请检查网络连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 显示下载对话框
     * @param {Object} data - 生成结果数据
     */
    showDownloadModal(data) {
        this.elements.downloadFilename.textContent = data.filename;
        this.elements.downloadFilecount.textContent = `${data.files_included} 个文件`;
        this.currentDownloadFile = data.filename;
        this.elements.downloadModal.style.display = 'flex';
    }

    /**
     * 隐藏模态框
     */
    hideModal() {
        this.elements.downloadModal.style.display = 'none';
    }

    /**
     * 下载生成的文件
     */
    async downloadGeneratedFile() {
        if (!this.currentDownloadFile) return;

        try {
            // 创建下载链接
            const downloadUrl = `/api/lecture/download/${encodeURIComponent(this.currentDownloadFile)}`;

            // 使用新窗口打开下载
            window.open(downloadUrl, '_blank');

            // 也可以使用a标签方式
            /*
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = this.currentDownloadFile;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            */

            this.showMessage('开始下载讲义', 'success');
            this.hideModal();

        } catch (error) {
            console.error('下载失败:', error);
            this.showMessage('下载失败，请重试', 'error');
        }
    }

    /**
     * 获取文件内容（单个）
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} 文件内容
     */
    async getFileContent(filePath) {
        try {
            const response = await fetch('/api/file/content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: filePath,
                    show_analysis: this.elements.showAnalysis.checked,
                    show_notes: this.elements.showNotes.checked
                })
            });

            const data = await response.json();

            if (data.success) {
                return data.content;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('获取文件内容失败:', error);
            throw error;
        }
    }

    /**
     * 获取配置信息
     */
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();

            if (data.success) {
                return data.config;
            }
        } catch (error) {
            console.error('获取配置失败:', error);
        }
        return null;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 初始化Marked库（如果可用）
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: true
        });
    }

    // 创建应用实例
    window.app = new LectureGeneratorApp();
});

// 添加一些CSS样式到搜索结果中
const style = document.createElement('style');
style.textContent = `
    .search-results {
        padding: 10px;
    }

    .search-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #3498db;
    }

    .search-header h4 {
        margin: 0;
        color: #2c3e50;
    }

    .results-list {
        max-height: 400px;
        overflow-y: auto;
    }

    .search-highlight {
        font-size: 0.8em;
        color: #6c757d;
        margin-left: 10px;
        font-style: italic;
    }
`;
document.head.appendChild(style);