## 5.3 BIG5_INFER 大五剖面推断表

> 用途：M21 人格演变、M22 出厂设置。当角色没有显式大五数值时，
> 由行为证据 + 画像标签**增量推断**五维剖面（0-100），并归一化。
> 接口：`asset_match("BIG5_INFER", {"behaviors": [...], "tags": [...]})` → 推断剖面。

```python
"BIG5_INFER": {
  "from_behavior": {   # 行为证据 → 五维增减（累计后 clamp 0-100）
    "主动举手发言":     {"extraversion": +8,  "neuroticism": -3},
    "独自角落看书":     {"extraversion": -6,  "openness": +4},
    "反驳老师/顶嘴":    {"agreeableness": -8, "extraversion": +4},
    "帮同学值日":       {"agreeableness": +7, "conscientiousness": +3},
    "考前通宵复习":     {"conscientiousness": +8, "neuroticism": +5},
    "临考刷手机":       {"conscientiousness": -6, "extraversion": +3},
    "运动会报名":       {"extraversion": +7, "neuroticism": -4},
    "见生人躲开":       {"extraversion": -8, "neuroticism": +6},
    "给朋友出头打架":   {"agreeableness": -6, "extraversion": +6, "neuroticism": +4},
    "养小动物/植物":    {"agreeableness": +6, "openness": +3},
    "画同人/写小说":    {"openness": +8, "conscientiousness": -3},
    "按部就班做笔记":   {"conscientiousness": +8, "openness": -4},
    "突发奇想翘课去看海": {"openness": +9, "conscientiousness": -8},
    "躲在天台一个人发呆": {"extraversion": -7, "neuroticism": +5, "openness": +3},
    "网上匿名热心答疑":  {"agreeableness": +5, "extraversion": -2},
    "打游戏上头骂人":   {"agreeableness": -5, "neuroticism": +6},
    "收集别人黑料":     {"agreeableness": -8, "conscientiousness": -3},
    "默默记下所有人生日": {"agreeableness": +7, "conscientiousness": +5}
  },
  "from_tags": {       # 画像标签 → 默认大五倾向（叠加于基线50）
    "病娇":     {"neuroticism": +25, "extraversion": +5,  "conscientiousness": -5},
    "傲娇":     {"neuroticism": +10, "extraversion": +4,  "agreeableness": -5},
    "天然呆":   {"neuroticism": -8,  "openness": +5,      "conscientiousness": -5},
    "腹黑":     {"agreeableness": -12, "neuroticism": +8, "conscientiousness": +4},
    "优等生":   {"conscientiousness": +15, "neuroticism": +6, "extraversion": -3},
    "运动系":   {"extraversion": +14, "neuroticism": -6,  "conscientiousness": +5},
    "阴沉":     {"extraversion": -15, "neuroticism": +14, "openness": +4},
    "中二":     {"openness": +12, "conscientiousness": -8, "extraversion": +4},
    "温柔":     {"agreeableness": +14, "neuroticism": -5, "extraversion": +2},
    "冷酷":     {"agreeableness": -10, "extraversion": -8, "neuroticism": -4},
    "现充":     {"extraversion": +15, "conscientiousness": +3, "openness": +2},
    "宅":       {"extraversion": -10, "openness": +6,      "conscientiousness": -2},
    "领袖型":   {"extraversion": +10, "conscientiousness": +8, "agreeableness": -2},
    "隐忍型":   {"neuroticism": +10, "agreeableness": +8, "extraversion": -8},
    "随性型":   {"conscientiousness": -12, "openness": +6, "neuroticism": -5}
  },
  "label_map": {       # 五维分数 → 描述标签（供 M21 演变后输出/可视化）
    "neuroticism":  {"high": "焦虑敏感", "mid": "情绪平稳", "low": "钝感镇定"},
    "extraversion": {"high": "外向活跃", "mid": "内外兼有", "low": "内向独处"},
    "openness":     {"high": "好奇开放", "mid": "常规偏好", "low": "守旧务实"},
    "agreeableness": {"high": "友善利他", "mid": "就事论事", "low": "强硬自我"},
    "conscientiousness": {"high": "自律严谨", "mid": "适度随性", "low": "随性散漫"}
  },
  "infer": "profile = 50基线 + Σ(from_behavior[行为]) + Σ(from_tags[标签]) → clamp(0,100) → 按label_map标注档位"
}
```

---

