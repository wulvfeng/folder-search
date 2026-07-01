# 🚀 高级文件夹扫描器

一个基于 PyQt5 的高性能文件夹扫描与搜索工具，支持多种匹配模式和智能搜索功能。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特性

- **快速扫描** - 扫描指定路径下的文件夹，支持当前目录和递归扫描
- **智能搜索** - 5种匹配模式：包含、开头、结尾、通配符、正则表达式
- **搜索建议** - 基于历史记录的智能搜索建议
- **结果导出** - 支持导出为 TXT、CSV、JSON 格式
- **历史记录** - 自动保存搜索历史，方便重复使用
- **一键打开** - 双击匹配结果直接打开对应文件夹
- **性能优化** - 缓存机制、延迟保存、多线程扫描


## 🛠️ 技术栈

- **GUI框架**: PyQt5
- **扫描算法**: BFS 广度优先搜索
- **并发处理**: QThread 多线程
- **数据持久化**: JSON 文件存储
- **性能优化**: LRU 缓存、延迟保存

## 📦 安装

### 环境要求

- Python 3.8+
- PyQt5

### 安装步骤

```bash
# 克隆仓库
# 进入项目目录
# 安装依赖
pip install PyQt5

# 运行程序
python main.py
```

## 🚀 使用方法

### 基本使用

1. 输入或选择要扫描的路径
2. 选择扫描模式（当前文件夹/递归扫描）
3. 点击"开始扫描"
4. 在搜索框输入关键词进行过滤
5. 双击匹配结果打开文件夹

### 匹配模式

| 模式 | 说明 | 示例 |
|------|------|------|
| 包含匹配 | 文件夹名包含搜索文本 | `doc` 匹配 `my_documents` |
| 开头匹配 | 以搜索文本开头 | `project` 匹配 `project_alpha` |
| 结尾匹配 | 以搜索文本结尾 | `backup` 匹配 `data_backup` |
| 通配符匹配 | 使用 `*` 和 `?` | `*.tmp` 匹配所有 .tmp 文件夹 |
| 正则表达式 | 高级正则匹配 | `^test` 匹配 test 开头的文件夹 |

### 快捷操作

- **双击左侧列表** → 自动填入搜索框
- **双击右侧结果** → 直接打开文件夹
- **输入时** → 实时显示搜索建议
- **点击导出按钮** → 保存匹配结果

## 📁 项目结构

```
folder-scanner/
├── main.py              # 程序入口
├── utils.py             # 工具函数和配置
├── history.py           # 搜索历史管理
├── scanner.py           # 文件夹扫描器核心
├── gui.py               # GUI界面
├── requirements.txt     # 依赖列表
└── README.md            # 项目说明
```

## ⚙️ 配置说明

配置信息在 `utils.py` 中：

```python
APP_CONFIG = {
    "app_name": "高级文件夹扫描器",
    "version": "3.2",
    "max_history": 100,          # 最大历史记录数
    "history_file": "search_history.json",
    "progress_update_interval": 50,  # 进度更新间隔
}
```

## 🔧 开发说明

### 架构设计

本项目采用模块化架构，职责分离：

- **utils.py** - 全局配置和工具函数
- **history.py** - 历史记录持久化管理
- **scanner.py** - 核心扫描算法和匹配逻辑
- **gui.py** - PyQt5 界面和交互逻辑
- **main.py** - 程序启动入口

### 性能优化

1. **路径解码缓存** - 避免重复解码相同路径
2. **正则表达式缓存** - 编译结果复用
3. **延迟保存** - 使用 Timer 避免频繁 IO
4. **多线程扫描** - 界面不卡顿

### 开发历程

本项目采用 **Vibe Coding + 人工优化** 的方式开发：

> 💡 **Vibe Coding**：通过 AI 辅助快速生成基础代码框架，实现功能原型
>
> 👨‍💻 **人工优化**：人工审查代码，进行架构重构、性能优化和细节打磨

这种协作模式结合了 AI 的高效生成能力和人类的深度思考能力，实现了快速迭代与代码质量的平衡。

## 📝 更新日志

### v3.2 (2026-07-01)
- ✨ 新增模块化架构重构
- ✨ 新增搜索建议功能
- ✨ 新增结果导出功能
- ⚡ 优化缓存机制
- ⚡ 优化延迟保存策略

### v3.1
- ✨ 新增递归扫描模式
- ✨ 新增历史记录功能
- ⚡ 优化扫描性能

### v3.0
- 🎉 初始版本发布
- ✨ 支持5种匹配模式
- ✨ 支持当前目录扫描

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

- GitHub: WLFNB

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [Python](https://www.python.org/) - 编程语言
- [Vibe Coding](https://en.wikipedia.org/wiki/Vibe_coding) - AI 辅助开发理念

---

⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！
