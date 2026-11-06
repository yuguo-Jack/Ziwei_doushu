# 依赖与版本管理

推荐Python 3.12、Node.js 24+和Git。`pyproject.toml`用于可编辑安装与CLI入口；`requirements-core.txt`用于轻量运行，`requirements-runtime.txt`加语义检索，`requirements-dev.txt`加报告验证。Python直接依赖和模型加载关键依赖固定版本；其它传递依赖由pip解析，不能称为整个Python环境逐字节相同。版本改变时同步这些文件，避免开发机与新用户解析到不同组合。

| Python依赖 | 作用 |
|---|---|
| numpy | 向量、同盘紧凑数组 |
| opencc-python-reimplemented | 繁简规范化，原文保持原字形 |
| zstandard | 年度归档与无损案例主题布局 |
| beautifulsoup4 | 古籍网页和报告结构解析 |
| tzdata | 历史IANA时区支持 |
| markdown-it-py | 安全渲染回答和报告Markdown |
| CairoSVG、reportlab、Pillow | PNG、PDF与图像导出；Cairo本体与中文字体另行配置 |
| torch、sentence-transformers、huggingface-hub | 可选固定Qwen嵌入模型下载和本地推理 |
| transformers、tokenizers、safetensors | 固定模型载入、分词和权重读取行为，避免新安装自动切换到未验证组合 |
| PyMuPDF | 开发验证PDF；不是独立聊天模型 |

网页固定React 19.3.0、React DOM 19.3.0与Vite 8.3.6，完整传递依赖由`web/package-lock.json`锁定。排盘使用固定上游`repo/package-lock.json`中的iztro、lunar-javascript、tsx、TypeScript等，源码版本由`config/sources.lock.json`固定。

两个Node项目都使用`npm ci`。安装器禁用安装脚本，所需构建由明确步骤调用；不会执行上游收费站构建。Windows通过Node直接调用npm-cli.js，避免shell处理带空格路径。

GPU并非必需。显式CPU安装使用官方PyTorch CPU索引；GPU用户先选择适配驱动的官方构建，再使用`--device auto`。模型权重是独立本机资料，不进Git或共享可清理缓存。

Codex CLI是单独安装并登录的外部程序。默认使用其可用模型，不把账号令牌写入本项目。配置项和环境变量见`.env.example`及`config/codex-chat.json`。模型调用参数由实际安装CLI支持情况决定，升级后需真实验证问答链路。

各包保留其原许可证，见安装包LICENSE/元数据；本项目不重新授权它们。第三方材料和字体见[NOTICE](../THIRD_PARTY_NOTICES.md)。自动依赖更新只开PR，需通过CI和相关真实回归后再合并。
