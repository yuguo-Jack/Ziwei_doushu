# 本机生成的校验与覆盖清单

这些JSON由下载和构建生成，反映本机实际安装范围，不作为已完成安装的模板提交。固定输入位于`config/`和`data/MANIFEST.json`。

下载器从`config/`读取固定模型和校验值，验证完成后生成本机模型清单；这里不决定下次下载版本。`runtime/installation.json`说明安装模式和语义检索选择；`doctor`按已选范围核验，`doctor --experience`再实际检查完整功能、网页、技能和Codex接口/登录。
