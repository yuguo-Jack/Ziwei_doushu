# GeoNames固定城市快照

来源：[GeoNames地理数据库](https://www.geonames.org/)，下载页为[export/dump](https://download.geonames.org/export/dump/)。数据采用[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。原版权/字段说明保存在`readme.txt`和`countryInfo.txt`。

本快照取得于2026-11-05，包含`cities15000.zip`、`readme.txt`、`countryInfo.txt`，本项目没有修改原始压缩包。`tools/collect_geography.py`将城市别名规范化建立本地索引；原GeoNames ID、坐标、国家与IANA时区仍保留。覆盖34,204个城市及244个国家/地区，范围是人口超过15,000或首府，不是所有村镇。

逐文件大小和SHA-256见`config/source-assets.lock.json`。安装优先使用本Git固定快照；手动替换为新下载数据时，应更新清单、重建并核查变化。
