## 5.2 FEAR_LIBRARY 恐惧模板库（9条）

```python
"FEAR_LIBRARY": {
  "F001": {"name": "害怕失败", "intensity_default": 6,
    "trigger_words": ["考试","比赛","失败","不及格","输","失误","搞砸"],
    "mods": {"escape": 20, "mischief": -10, "sexual": -5}},
  "F002": {"name": "害怕被拒绝", "intensity_default": 7,
    "trigger_words": ["告白","拒绝","讨厌","不喜欢","被甩","冷漠","回避"],
    "mods": {"escape": 18, "sexual": -8, "mischief": -3}},
  "F003": {"name": "害怕被注视", "intensity_default": 5,
    "trigger_words": ["点名","上台","围观","盯着看","万众瞩目","镜头","演讲"],
    "mods": {"escape": 22, "mischief": -8, "sexual": -6}},
  "F004": {"name": "害怕被看穿", "intensity_default": 6,
    "trigger_words": ["试探","秘密","真心话","伪装","看透","内心","把柄"],
    "mods": {"escape": 16, "mischief": 6, "sexual": -4}},
  "F005": {"name": "害怕被抛弃/背叛", "intensity_default": 8,
    "trigger_words": ["离开","抛弃","背叛","丢下","分手","绝交","背叛"],
    "mods": {"escape": 15, "mischief": 8, "sexual": 5}},
  "F006": {"name": "害怕无聊/单调", "intensity_default": 4,
    "trigger_words": ["重复","单调","无聊","日常","等待","安静","一成不变"],
    "mods": {"mischief": 25, "escape": -10, "sexual": 3}},
  "F007": {"name": "害怕身份暴露", "intensity_default": 7,
    "trigger_words": ["身份","真相","调查","黑历史","暴露","扒","揭穿"],
    "mods": {"escape": 20, "sexual": -6, "mischief": 2}},
  "F008": {"name": "害怕人设崩塌", "intensity_default": 6,
    "trigger_words": ["素颜","失态","爆料","人设","丑闻","丢脸","出丑"],
    "mods": {"escape": 18, "sexual": -5, "mischief": -2}},
  "F009": {"name": "害怕被超越/被比下去", "intensity_default": 5,
    "trigger_words": ["比较","排名","超越","落后","被比下去","竞争","输给"],
    "mods": {"escape": 14, "sexual": -8, "mischief": -4}}
}
```

> ★ v0.7.1 恐惧动态脱敏说明：本库 intensity_default 为出厂强度。运行时由 M22.fear_unverified 标记
>   未验证触发 → 下次临时 ×0.5；被验证 → 恢复全强度。与 E02 应激钝化（累计≥3次未逃脱 → 永久-15）分层叠加：
>   先软脱敏（临时减半，可恢复），累计达标后再触发 E02 硬脱敏（永久降低出厂值）；E01 创伤固化则反向加深。

---

