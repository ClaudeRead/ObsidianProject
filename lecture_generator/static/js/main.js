/**
 * Obsidian 讲义生成器 - 主 JavaScript 文件
 */

class LectureGeneratorApp {
    constructor() {
        this.selectedFiles = [];
        this.directoryStructure = null;
        this.isLoading = false;
        this.previewTimer = null;
        this.generateOptions = {
            showAnalysis: true,
            showNotes: true,
            includeToc: true,
            format: 'html',
            filename: ''
        };

        // 初始化
        this.initElements();
        this.bindEvents();
        this.loadDirectory();
        this.updateStatusPills();
    }

    iconMarkup(name, className = '') {
        const classAttr = ['icon', className].filter(Boolean).join(' ');
        return `<svg class="${classAttr}"><use href="#${name}"></use></svg>`;
    }

    createIcon(name, className = '') {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', ['icon', className].filter(Boolean).join(' '));
        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', `#${name}`);
        svg.appendChild(use);
        return svg;
    }

    /**
     * 初始化 DOM 元素
     */
    initElements() {
        this.elements = {
            // 文件树相关
            fileTree: document.getElementById('file-tree'),
            selectedList: document.getElementById('selected-list'),
            selectedCount: document.getElementById('selected-count'),
            formatPill: document.getElementById('format-pill'),

            searchInput: document.getElementById('search-input'),
            searchType: document.getElementById('search-type'),
            searchBtn: document.getElementById('search-btn'),

            // 操作按钮
            refreshBtn: document.getElementById('refresh-btn'),
            collapseAllBtn: document.getElementById('collapse-all-btn'),
            expandAllBtn: document.getElementById('expand-all-btn'),
            clearSelectedBtn: document.getElementById('clear-selected'),
            sortSelectedBtn: document.getElementById('sort-selected'),

            // 预览相关
            copyPreviewBtn: document.getElementById('copy-preview'),
            clearPreviewBtn: document.getElementById('clear-preview'),
            previewContent: document.getElementById('preview-content'),

            // 路径选择相关
            currentPath: document.getElementById('current-path'),
            selectPathBtn: document.getElementById('select-path-btn'),
            pathModal: document.getElementById('path-modal'),
            pathInput: document.getElementById('path-input'),
            browsePathBtn: document.getElementById('browse-path-btn'),
            confirmPathBtn: document.getElementById('confirm-path-btn'),
            cancelPathBtns: document.querySelectorAll('.js-cancel-path, .modal-close'),
            pathValidation: document.getElementById('path-validation'),

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
            closeModalBtns: document.querySelectorAll('.js-close-download, .modal-close'),

            // 生成选项对话框
            openGenerateModalBtn: document.getElementById('open-generate-modal'),
            generateModal: document.getElementById('generate-modal'),
            modalShowAnalysis: document.getElementById('modal-show-analysis'),
            modalShowNotes: document.getElementById('modal-show-notes'),
            modalIncludeToc: document.getElementById('modal-include-toc'),
            modalFormat: document.getElementById('modal-format'),
            modalFilename: document.getElementById('modal-filename'),
            cancelGenerateBtns: document.querySelectorAll('.js-cancel-generate, .modal-close'),
            confirmGenerateBtn: document.getElementById('confirm-generate')
        };
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 文件树操作
        this.elements.refreshBtn.addEventListener('click', () => this.loadDirectory());
        this.elements.collapseAllBtn.addEventListener('click', () => this.collapseAll());
        this.elements.expandAllBtn.addEventListener('click', () => this.expandAll());
        this.elements.clearSelectedBtn.addEventListener('click', () => this.clearSelected());
        this.elements.sortSelectedBtn.addEventListener('click', () => this.sortSelected());

        this.elements.searchBtn.addEventListener('click', () => this.searchFiles());
        this.elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchFiles();
        });

        // 路径选择功能
        this.elements.selectPathBtn.addEventListener('click', () => this.showPathSelector());
        this.elements.browsePathBtn.addEventListener('click', () => this.browseFolder());
        this.elements.confirmPathBtn.addEventListener('click', () => this.confirmPathSelection());
        this.elements.cancelPathBtns.forEach((btn) => {
            btn.addEventListener('click', () => this.hidePathModal());
        });

        // 路径输入验证
        this.elements.pathInput.addEventListener('input', () => this.validatePathInput());

        // 生成选项对话框
        this.elements.openGenerateModalBtn.addEventListener('click', () => this.showGenerateModal());
        this.elements.cancelGenerateBtns.forEach((btn) => {
            btn.addEventListener('click', () => this.hideGenerateModal());
        });
        this.elements.confirmGenerateBtn.addEventListener('click', () => this.confirmGenerate());
        this.elements.copyPreviewBtn.addEventListener('click', () => this.copyPreview());
        this.elements.clearPreviewBtn.addEventListener('click', () => this.clearPreview());

        // 下载对话框
        this.elements.downloadBtn.addEventListener('click', () => this.downloadGeneratedFile());
        this.elements.closeModalBtns.forEach((btn) => {
            btn.addEventListener('click', () => this.hideModal());
        });

        // 点击模态框外部关闭
        this.elements.downloadModal.addEventListener('click', (e) => {
            if (e.target === this.elements.downloadModal) {
                this.hideModal();
            }
        });

        this.elements.generateModal.addEventListener('click', (e) => {
            if (e.target === this.elements.generateModal) {
                this.hideGenerateModal();
            }
        });

        // ESC 键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal();
                this.hideGenerateModal();
            }
        });
    }

    /**
     * 显示加载指示器
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
     */
    showMessage(message, type = 'info', duration = 3000) {
        const toast = this.elements.messageToast;
        toast.textContent = message;
        toast.className = `toast ${type}`;

        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    /**
     * 设置状态信息
     */
    setStatus(status) {
        this.elements.status.textContent = status;
    }

    /**
     * 更新信息面板
     */
    updateStatusPills() {
        this.elements.selectedCount.textContent = this.selectedFiles.length;
        this.elements.formatPill.textContent = this.generateOptions.format.toUpperCase();
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
                this.showMessage('目录加载成功', 'success');
            } else {
                this.showMessage(`加载失败：${data.error}`, 'error');
            }
        } catch (error) {
            console.error('加载目录失败:', error);
            this.showMessage('网络错误，请检查服务器连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async searchFiles() {
        const keyword = this.elements.searchInput.value.trim();
        const searchType = this.elements.searchType.value;

        if (!keyword) {
            this.renderDirectoryTree();
            return;
        }

        this.showLoading(`正在搜索：${keyword}`);

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ keyword, type: searchType })
            });

            const data = await response.json();

            if (data.success) {
                this.displaySearchResults(data.results, keyword);
            } else {
                this.showMessage(`搜索失败：${data.error}`, 'error');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.showMessage('搜索失败，请检查网络连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(results, keyword) {
        const treeContainer = this.elements.fileTree;

        if (!results || results.length === 0) {
            treeContainer.innerHTML = '<p class="empty-message">未找到匹配的文件</p>';
            return;
        }

        const searchResultsHTML = results.map(result => {
            const pathParts = result.path.split('/');
            const fileName = pathParts.pop();
            const isSelected = this.isSelected(result.path);

            return `
                <div class="file-item" data-path="${result.path}">
                    <input type="checkbox" class="file-checkbox" ${isSelected ? 'checked' : ''}>
                    ${this.iconMarkup('icon-file')}
                    <span class="file-name">${fileName}</span>
                    <span class="file-path">${pathParts.join('/')}</span>
                </div>
            `;
        }).join('');

        treeContainer.innerHTML = `
            <div class="search-results">
                <div class="search-header">
                    <h4>搜索结果："${keyword}" (${results.length})</h4>
                    <button class="btn btn-secondary btn-small" id="back-to-tree">返回</button>
                </div>
                <div class="results-list">
                    ${searchResultsHTML}
                </div>
            </div>
        `;

        document.getElementById('back-to-tree').addEventListener('click', () => {
            this.renderDirectoryTree();
        });

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

            checkbox.addEventListener('change', () => {
                this.toggleFileSelection(filePath, fileName, checkbox.checked);
            });
        });
    }

    /**
     * 更新文件计数
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
        this.elements.fileCount.textContent = `文件总数：${fileCount}`;
    }

    /**
     * 渲染目录树 - 修复折叠/展开问题
     */
    renderDirectoryTree() {
        if (!this.directoryStructure) return;

        const treeContainer = this.elements.fileTree;
        treeContainer.innerHTML = '';

        const renderItem = (item, depth = 0, parentElement = treeContainer) => {
            const div = document.createElement('div');
            div.className = 'tree-item';

            if (item.type === 'directory') {
                // 创建目录头部
                const header = document.createElement('div');
                header.className = 'tree-header';
                
                const icon = this.createIcon('icon-caret-right', 'icon-fill icon-caret');
                const iconUse = icon.querySelector('use');
                
                const folderIcon = this.createIcon('icon-folder');
                folderIcon.style.marginRight = '8px';
                folderIcon.style.color = '#f39c12';
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = item.name;
                
                header.appendChild(icon);
                header.appendChild(folderIcon);
                header.appendChild(nameSpan);
                
                // 创建子容器
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'tree-children';
                childrenContainer.style.display = 'none'; // 默认折叠
                
                div.appendChild(header);
                div.appendChild(childrenContainer);
                
                // 绑定点击事件 - 修复折叠/展开
                header.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isExpanded = childrenContainer.style.display === 'block';
                    
                    if (isExpanded) {
                        // 折叠
                        childrenContainer.style.display = 'none';
                        if (iconUse) {
                            iconUse.setAttribute('href', '#icon-caret-right');
                        }
                    } else {
                        // 展开
                        childrenContainer.style.display = 'block';
                        if (iconUse) {
                            iconUse.setAttribute('href', '#icon-caret-down');
                        }
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
                const isSelected = this.isSelected(item.path);
                
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.dataset.path = item.path;
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'file-checkbox';
                checkbox.checked = isSelected;
                
                const fileIcon = this.createIcon('icon-file');
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'file-name';
                nameSpan.textContent = item.name;
                
                fileItem.appendChild(checkbox);
                fileItem.appendChild(fileIcon);
                fileItem.appendChild(nameSpan);
                
                div.appendChild(fileItem);

                // 绑定文件点击事件
                fileItem.addEventListener('click', (e) => {
                    if (e.target !== checkbox && !checkbox.contains(e.target)) {
                        checkbox.checked = !checkbox.checked;
                        this.toggleFileSelection(item.path, item.name, checkbox.checked);
                    }
                });

                checkbox.addEventListener('change', (e) => {
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
     */
    toggleFileSelection(filePath, fileName, isSelected) {
        if (isSelected) {
            if (!this.isSelected(filePath)) {
                this.selectedFiles.push({ path: filePath, name: fileName });
            }
        } else {
            this.selectedFiles = this.selectedFiles.filter(item => item.path !== filePath);
        }

        this.renderSelectedList();
        this.updateStatusPills();
        this.schedulePreview();
    }

    /**
     * 渲染已选择列表
     */
    renderSelectedList() {
        const selectedList = this.elements.selectedList;
        selectedList.innerHTML = '';

        if (this.selectedFiles.length === 0) {
            const emptyMessage = document.createElement('p');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = '暂无选择的文件';
            selectedList.appendChild(emptyMessage);
            return;
        }

        this.selectedFiles.forEach((item, index) => {
            const row = document.createElement('div');
            row.className = 'selected-item';
            row.dataset.path = item.path;
            row.innerHTML = `
                ${this.iconMarkup('icon-file')}
                <span>${item.name}</span>
                <div class="order-controls">
                    <button class="order-btn" data-action="up">▲</button>
                    <button class="order-btn" data-action="down">▼</button>
                    <span class="remove-btn">${this.iconMarkup('icon-close')}</span>
                </div>
            `;

            row.querySelector('.order-btn[data-action="up"]').addEventListener('click', () => {
                this.moveSelectedItem(index, index - 1);
            });
            
            row.querySelector('.order-btn[data-action="down"]').addEventListener('click', () => {
                this.moveSelectedItem(index, index + 1);
            });
            
            row.querySelector('.remove-btn').addEventListener('click', () => {
                this.removeSelectedItem(item.path);
            });

            selectedList.appendChild(row);
        });
    }

    isSelected(filePath) {
        return this.selectedFiles.some(item => item.path === filePath);
    }

    moveSelectedItem(fromIndex, toIndex) {
        if (toIndex < 0 || toIndex >= this.selectedFiles.length) {
            return;
        }

        const updated = [...this.selectedFiles];
        const [moved] = updated.splice(fromIndex, 1);
        updated.splice(toIndex, 0, moved);
        this.selectedFiles = updated;
        this.renderSelectedList();
        this.schedulePreview();
    }

    removeSelectedItem(filePath) {
        this.selectedFiles = this.selectedFiles.filter(item => item.path !== filePath);
        const fileCheckbox = document.querySelector(`.file-item[data-path="${filePath}"] .file-checkbox`);
        if (fileCheckbox) {
            fileCheckbox.checked = false;
        }
        this.renderSelectedList();
        this.updateStatusPills();
        this.schedulePreview();
    }

    sortSelected() {
        this.selectedFiles = [...this.selectedFiles].sort((a, b) => a.name.localeCompare(b.name));
        this.renderSelectedList();
        this.schedulePreview();
    }

    schedulePreview() {
        if (this.previewTimer) {
            clearTimeout(this.previewTimer);
        }

        if (this.selectedFiles.length === 0) {
            this.clearPreview();
            return;
        }

        this.previewTimer = setTimeout(() => {
            this.previewLecture(true);
        }, 500);
    }

    showGenerateModal() {
        this.elements.modalShowAnalysis.checked = this.generateOptions.showAnalysis;
        this.elements.modalShowNotes.checked = this.generateOptions.showNotes;
        this.elements.modalIncludeToc.checked = this.generateOptions.includeToc;
        this.elements.modalFormat.value = this.generateOptions.format;
        this.elements.modalFilename.value = this.generateOptions.filename || '';
        this.elements.generateModal.style.display = 'flex';
    }

    hideGenerateModal() {
        this.elements.generateModal.style.display = 'none';
    }

    confirmGenerate() {
        this.generateOptions = {
            showAnalysis: this.elements.modalShowAnalysis.checked,
            showNotes: this.elements.modalShowNotes.checked,
            includeToc: this.elements.modalIncludeToc.checked,
            format: this.elements.modalFormat.value,
            filename: this.elements.modalFilename.value.trim()
        };
        this.updateStatusPills();
        this.hideGenerateModal();
        this.generateLecture();
    }

    /**
     * 清空已选择
     */
    clearSelected() {
        document.querySelectorAll('.file-checkbox:checked').forEach(checkbox => {
            checkbox.checked = false;
        });

        this.selectedFiles = [];
        this.renderSelectedList();
        this.updateStatusPills();
        this.clearPreview();

        this.showMessage('已清空所有选择', 'success');
    }

    /**
     * 预览讲义 - 添加章节导航
     */
    async previewLecture(silent = false) {
        if (this.selectedFiles.length === 0) {
            this.clearPreview();
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
                    file_paths: this.selectedFiles.map(item => item.path),
                    show_analysis: this.generateOptions.showAnalysis,
                    show_notes: this.generateOptions.showNotes
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayPreview(data.preview);
                if (!silent) {
                    this.showMessage(`预览更新成功，包含 ${data.file_count} 个文件`, 'success');
                }
            } else {
                this.showMessage(`预览失败：${data.error}`, 'error');
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
     */
    displayPreview(content) {
        const previewContent = this.elements.previewContent;

        // 使用 marked 库转换 Markdown 为 HTML
        if (typeof marked !== 'undefined') {
            const htmlContent = marked.parse(content, {
                breaks: true,
                gfm: true,
                headerIds: true
            });
            if (typeof DOMPurify !== 'undefined') {
                previewContent.innerHTML = DOMPurify.sanitize(htmlContent);
            } else {
                previewContent.textContent = content;
            }
        } else {
            previewContent.textContent = content;
        }
    }

    /**
     * 清空预览
     */
    clearPreview() {
        this.elements.previewContent.innerHTML = `
            <div class="empty-preview">
                ${this.iconMarkup('icon-file', 'icon-lg icon-muted')}
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
        if (this.selectedFiles.length === 0) {
            this.showMessage('请先选择要生成讲义的文件', 'warning');
            return;
        }

        this.showLoading('正在生成讲义...');

        try {
            const response = await fetch('/api/lecture/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_paths: this.selectedFiles.map(item => item.path),
                    show_analysis: this.generateOptions.showAnalysis,
                    show_notes: this.generateOptions.showNotes,
                    include_toc: this.generateOptions.includeToc,
                    format: this.generateOptions.format,
                    filename: this.generateOptions.filename
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showDownloadModal(data);
                this.showMessage(`讲义生成成功：${data.filename}`, 'success');
            } else {
                this.showMessage(`生成失败：${data.error}`, 'error');
            }
        } catch (error) {
            console.error('生成失败:', error);
            this.showMessage('生成失败，请检查网络连接', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showDownloadModal(data) {
        this.elements.downloadFilename.textContent = data.filename;
        this.elements.downloadFilecount.textContent = `${data.files_included} 个文件`;
        this.currentDownloadFile = data.filename;
        this.elements.downloadModal.style.display = 'flex';
    }

    hideModal() {
        this.elements.downloadModal.style.display = 'none';
    }

    async downloadGeneratedFile() {
        if (!this.currentDownloadFile) return;

        try {
            const downloadUrl = `/api/lecture/download/${encodeURIComponent(this.currentDownloadFile)}`;
            window.open(downloadUrl, '_blank');
            this.showMessage('开始下载讲义', 'success');
            this.hideModal();
        } catch (error) {
            console.error('下载失败:', error);
            this.showMessage('下载失败，请重试', 'error');
        }
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();

            if (data.success) {
                this.elements.currentPath.textContent = data.config.knowledge_base;
                return data.config;
            }
        } catch (error) {
            console.error('获取配置失败:', error);
        }
        return null;
    }

    showPathSelector() {
        this.loadConfig().then(config => {
            if (config) {
                this.elements.pathInput.value = config.knowledge_base;
                this.elements.pathInput.readOnly = false;
                this.validatePathInput();
            }
        });
        this.elements.pathModal.style.display = 'flex';
    }

    hidePathModal() {
        // 确保模态框能正确关闭
        if (this.elements.pathModal) {
            this.elements.pathModal.style.display = 'none';
            this.elements.pathValidation.textContent = '';
            this.elements.confirmPathBtn.disabled = true;
        }
    }

    async browseFolder() {
        try {
            const response = await fetch('/api/config/browse', { method: 'POST' });
            const data = await response.json();

            if (data.success && data.path) {
                this.elements.pathInput.value = data.path;
                this.validatePathInput();
                return;
            }

            if (data.error && data.error !== '已取消选择') {
                this.showMessage(`选择失败：${data.error}`, 'error');
            }
        } catch (error) {
            console.error('浏览目录失败:', error);
            this.showMessage('浏览失败，请手动输入路径', 'error');
        }
    }

    /**
     * 验证路径输入
     */
    async validatePathInput() {
        const path = this.elements.pathInput.value.trim();
        const validationDiv = this.elements.pathValidation;
        const confirmBtn = this.elements.confirmPathBtn;

        if (!path) {
            validationDiv.textContent = '';
            validationDiv.className = 'validation-message';
            confirmBtn.disabled = true;
            return;
        }

        try {
            const response = await fetch('/api/config/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ knowledge_base: path })
            });

            const data = await response.json();

            if (data.success) {
                if (data.is_valid) {
                    validationDiv.textContent = '✓ ' + data.message;
                    validationDiv.className = 'validation-message valid';
                    confirmBtn.disabled = false;
                } else {
                    validationDiv.textContent = '✗ ' + data.message;
                    validationDiv.className = 'validation-message invalid';
                    confirmBtn.disabled = true;
                }
            } else {
                validationDiv.textContent = '验证失败：' + data.error;
                validationDiv.className = 'validation-message invalid';
                confirmBtn.disabled = true;
            }
        } catch (error) {
            console.error('验证路径失败:', error);
            validationDiv.textContent = '网络错误，请重试';
            validationDiv.className = 'validation-message invalid';
            confirmBtn.disabled = true;
        }
    }

    /**
     * 确认路径选择
     */
    async confirmPathSelection() {
        const path = this.elements.pathInput.value.trim();
        this.showLoading('正在更新配置...');

        try {
            const response = await fetch('/api/config/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ knowledge_base: path })
            });

            const data = await response.json();

            if (data.success) {
                this.showMessage('配置已更新', 'success');
                this.hidePathModal();
                this.loadDirectory();
                this.selectedFiles = [];
                this.renderSelectedList();
                this.updateStatusPills();
                this.clearPreview();
            } else {
                this.showMessage(`更新失败：${data.error}`, 'error');
            }
        } catch (error) {
            console.error('更新配置失败:', error);
            this.showMessage('网络错误，请重试', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 折叠所有目录
     */
    collapseAll() {
        const allChildren = this.elements.fileTree.querySelectorAll('.tree-children');
        const allIcons = this.elements.fileTree.querySelectorAll('.icon-caret use');
        
        allChildren.forEach(children => {
            children.style.display = 'none';
        });
        
        allIcons.forEach(icon => {
            icon.setAttribute('href', '#icon-caret-right');
        });
    }

    /**
     * 展开所有目录
     */
    expandAll() {
        const allChildren = this.elements.fileTree.querySelectorAll('.tree-children');
        const allIcons = this.elements.fileTree.querySelectorAll('.icon-caret use');
        
        allChildren.forEach(children => {
            children.style.display = 'block';
        });
        
        allIcons.forEach(icon => {
            icon.setAttribute('href', '#icon-caret-down');
        });
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: true
        });
    }

    window.app = new LectureGeneratorApp();
});