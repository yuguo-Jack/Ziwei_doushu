# 原始来源

Git仅保存带归属的小型古籍和GeoNames快照。`config/source-assets.lock.json`保存逐文件SHA-256；快照按原字节提交。

安装器通过`scripts/fetch_sources.py`获取固定提交的引擎、天纪和人纪仓库；完整安装再获取v4年度发布文件。上游目录和大型压缩包被Git忽略。不要把私人资料放入来源目录。

许可见[第三方说明](../THIRD_PARTY_NOTICES.md)，构建见[知识库说明](../docs/KNOWLEDGE_BASE.zh-CN.md)。
