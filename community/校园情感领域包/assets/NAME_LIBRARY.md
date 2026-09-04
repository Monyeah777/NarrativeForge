## 5.14 NAME_LIBRARY 开局命名库（20条，v0.7.4）
> 用途：开局确定主角名字。双风格：日式（贴合日式高中背景）/ 中式（写实自然系）。
> **核心原则：中式名字只收「重名率中等」**——
> 重名率过高（烂大街爆款，如 梓萱/子涵/浩然/欣怡 等 2010s 热名组合）→ 无辨识度，不收；
> 重名率过低/近零（网文编造感，如 冷宸/墨渊/傲天/浅浅 等）→ 不真实，不收；
> 重名率中等（常见姓氏 + 常见名，组合不烂大街）→ 真实自然且有辨识度，收。
### 5.14.1 命名规则与重名热度质检（cn 库专用）
| 等级 | 判据 | 处理 |
|---|---|---|
| high | 2010s 新生儿爆款组合（梓/涵/轩/宇/欣/怡/诺/浩/然/宇航/梓萱/雨桐/明轩/欣怡/子涵 等） | 不入库 |
| medium | 常见姓氏 + 常见名，组合非爆款（如 陈默/林远/叶青/苏雨） | ✅ 收录 |
| low | 生僻字 / 网文风组合（冷/宸/墨/渊/傲/尊/帝/冥/夜/殇/浅浅/依依 等） | 不入库 |
> 规则：1. cn 条目须 dup_grade=medium 才可注册（asset_register 校验失败拒绝）；2. 玩家自定名命中 high/low 仅提示不阻止（尊重玩家自由）。
### 5.14.2 日式名库（jp，10条）——常见姓氏+常见名，贴合日式高中背景
```python
"NAME_LIBRARY": {
  # ---- 日式（jp）：常见姓 + 常见名 ----
  "JP001": {"style": "jp", "full_name": "佐藤遥", "surname": "佐藤", "given_name": "遥", "gender": "male", "tags": ["常见姓", "清爽"]},
  "JP002": {"style": "jp", "full_name": "铃木翔太", "surname": "铃木", "given_name": "翔太", "gender": "male", "tags": ["常见姓", "元气"]},
  "JP003": {"style": "jp", "full_name": "高桥悠真", "surname": "高桥", "given_name": "悠真", "gender": "male", "tags": ["常见姓", "沉静"]},
  "JP004": {"style": "jp", "full_name": "田中健", "surname": "田中", "given_name": "健", "gender": "male", "tags": ["常见姓", "朴素"]},
  "JP005": {"style": "jp", "full_name": "中村凑", "surname": "中村", "given_name": "凑", "gender": "male", "tags": ["常见姓", "内敛"]},
  "JP006": {"style": "jp", "full_name": "渡边美咲", "surname": "渡边", "given_name": "美咲", "gender": "female", "tags": ["常见姓", "温柔"]},
  "JP007": {"style": "jp", "full_name": "伊藤结衣", "surname": "伊藤", "given_name": "结衣", "gender": "female", "tags": ["常见姓", "文静"]},
  "JP008": {"style": "jp", "full_name": "山本葵", "surname": "山本", "given_name": "葵", "gender": "female", "tags": ["常见姓", "清爽"]},
  "JP009": {"style": "jp", "full_name": "小林阳菜", "surname": "小林", "given_name": "阳菜", "gender": "female", "tags": ["常见姓", "明亮"]},
  "JP010": {"style": "jp", "full_name": "加藤诗织", "surname": "加藤", "given_name": "诗织", "gender": "female", "tags": ["常见姓", "文艺"]},
  # ---- 中式（cn）：重名率中等，写实自然系（已过 5.14.1 非网文质检） ----
  "CN001": {"style": "cn", "full_name": "陈默", "surname": "陈", "given_name": "默", "gender": "male", "dup_grade": "medium", "tags": ["重名中等", "安静", "生活感"]},
  "CN002": {"style": "cn", "full_name": "林远", "surname": "林", "given_name": "远", "gender": "male", "dup_grade": "medium", "tags": ["重名中等", "开阔"]},
  "CN003": {"style": "cn", "full_name": "周川", "surname": "周", "given_name": "川", "gender": "male", "dup_grade": "medium", "tags": ["重名中等", "利落"]},
  "CN004": {"style": "cn", "full_name": "孙宁", "surname": "孙", "given_name": "宁", "gender": "male", "dup_grade": "medium", "tags": ["重名中等", "稳重"]},
  "CN005": {"style": "cn", "full_name": "黄毅", "surname": "黄", "given_name": "毅", "gender": "male", "dup_grade": "medium", "tags": ["重名中等", "踏实"]},
  "CN006": {"style": "cn", "full_name": "叶青", "surname": "叶", "given_name": "青", "gender": "female", "dup_grade": "medium", "tags": ["重名中等", "清秀"]},
  "CN007": {"style": "cn", "full_name": "苏雨", "surname": "苏", "given_name": "雨", "gender": "female", "dup_grade": "medium", "tags": ["重名中等", "清新"]},
  "CN008": {"style": "cn", "full_name": "周悦", "surname": "周", "given_name": "悦", "gender": "female", "dup_grade": "medium", "tags": ["重名中等", "温和"]},
  "CN009": {"style": "cn", "full_name": "方静", "surname": "方", "given_name": "静", "gender": "female", "dup_grade": "medium", "tags": ["重名中等", "朴素"]},
  "CN010": {"style": "cn", "full_name": "李舒", "surname": "李", "given_name": "舒", "gender": "female", "dup_grade": "medium", "tags": ["重名中等", "温柔"]}
}
```
---
