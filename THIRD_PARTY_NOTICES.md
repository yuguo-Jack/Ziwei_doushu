# 第三方依赖、资料与许可

本项目的MIT许可证只覆盖新增代码与文档。下列代码、资料、字体和模型分别适用其原许可证；安装器会保留来源仓库的许可文件。

| 项目 / 材料 | 固定版本 / 所在位置 | 许可与处理方式 |
|---|---|---|
| [ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu) | a600484a49255039d0725f1ba9e11ca81a948f97；安装到`repo/` | MIT代码；[原许可](licenses/ziwei-doushu-MIT.txt)。其中嵌入课程引文仍受原资料条款约束 |
| [nihai-tianji-corpus](https://github.com/Renhuai123/nihai-tianji-corpus) | 462faa4c70af40b8b87ad82ffa82a5823a485e94 | data/docs为CC BY-NC-SA 4.0，tools为MIT；[上游许可](licenses/tianji-LICENSE.md)。本Git不打包全文，由安装器获取 |
| [nihai-renji-corpus](https://github.com/Renhuai123/nihai-renji-corpus) | fdafae1ea685756a92a59179fdfa2e6a01379100 | 同上；[上游许可](licenses/renji-LICENSE.md)。历史医籍课程与紫微检索分域 |
| [v4.0-13d案例发布](https://github.com/Renhuai123/ziwei-doushu/releases/tag/v4.0-13d) | `data/MANIFEST.json`、`SHA256SUMS.txt`登记77个压缩包 | 发布数据声明CC BY 4.0，嵌入课程引文保留其单独权利；仅提供获取及建库脚本 |
| [维基文库古籍](sources/classics/README.md) | 4个电子页固定oldid；JSON保留出处、锚点与修订 | 古代原作与现代电子整理分别看待；保留维基文库署名、修订和适用条款。导出/切分有记录，不冒称通校刻本 |
| [GeoNames](sources/geonames/README.md) | cities15000、countryInfo及readme固定快照 | CC BY 4.0；小型原始快照随Git分发，保留GeoNames出处与校验 |
| [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3 | 上游模型卡声明Apache-2.0；本Git无权重，按固定revision下载到`models/` |
| [Noto Serif SC](https://github.com/notofonts/noto-cjk)派生Ziwei Display | `web/public/fonts/` | SIL OFL 1.1；改名、静态化和裁切，保留[OFL](web/public/fonts/OFL.txt)及[来源/哈希](web/public/fonts/provenance.json) |
| React / React DOM / Vite | `web/package-lock.json` | 以安装包各自license为准；均不把node_modules提交到Git |
| iztro / lunar-javascript / tsx / TypeScript等 | 固定引擎的`package-lock.json` | 通过固定上游`npm ci`安装，保留各包许可；不是本项目重新授权 |
| Python依赖 | `pyproject.toml`及`requirements-*.txt` | 详见[依赖说明](docs/DEPENDENCIES.zh-CN.md)；安装包各自许可保留 |

课程内容著作权归倪海厦先生及其权利继承人，上游语料是短引文整理而非完整课程逐字稿。可公开取得不等于放弃原有权利。基于这些课程制作和分发衍生资料时，应遵守署名、非商业和相同方式共享要求，参阅[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans)。其它CC BY材料保留署名和修改说明，参阅[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh-hans)。

来源登记、条件、争议及覆盖缺口见[SOURCES.zh-CN.md](SOURCES.zh-CN.md)。固定版本修改需要更新`config/sources.lock.json`或相应快照清单并重新验证，不能把项目代码许可证覆盖到导入的知识文本。
