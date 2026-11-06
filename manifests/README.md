# 本机生成的校验与覆盖清单

这些JSON由下载和构建生成，反映本机实际安装范围，不作为已完成安装的模板提交。固定输入位于`config/`和`data/MANIFEST.json`。

模型清单由安装器从`config/`初始化，下载器验证后更新。`runtime/installation.json`说明安装模式和语义检索选择；`doctor`按已选模式核验，未安装的可选模块明确标为未安装。
