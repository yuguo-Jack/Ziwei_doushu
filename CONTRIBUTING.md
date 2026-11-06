# 参与开发

先读[架构](docs/ARCHITECTURE.zh-CN.md)与[维护开发](docs/DEVELOPMENT.zh-CN.md)。Windows为完整验证环境；其它平台修改需附运行记录。

1. 从main新建分支；保留固定上游，不直接修改`repo/`。
2. 计算、检索、CLI/技能与网页使用同一工具层，新增网页能力同时提供直接调用入口。
3. 新知识必须带URL、固定版本、许可、原文定位、条件及未知项，不用模型文字补成古籍。
4. 运行`python -X utf8 tools/test_codex_review.py`、`python -X utf8 -m unittest discover -s tests -v`及网页构建；涉及数据或计算时再运行对应真实构建/回归。
5. 提交前运行`python -X utf8 scripts/check_release.py`。不得提交真实出生资料、账号文件、数据库、模型、日志或导出。

更新依赖时一并维护requirements、pyproject及npm lock；更新数据版本时修改固定清单，重建受影响部分并记录差异。PR说明具体触发问题、修改后的行为、验证和保留限制。自动依赖更新也需通过检查，不自动合并。
