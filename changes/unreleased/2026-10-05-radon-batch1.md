type: refactor
surface: quality
note: 复杂度收敛第一批——import_adapter.parse_ccv3 由 F(46) 拆到 C(20)：抽出条目入册/归层/去重三个小助手，并删除从未被调用的死函数 place；模块行数净减、radon ≥D 99→98
