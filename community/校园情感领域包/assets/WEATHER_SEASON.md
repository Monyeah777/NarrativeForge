## 5.8 WEATHER_SEASON 天气季节事件表

> 用途：M10 世界推进（每日天气/季节状态）、M30 事件生产（天气季节事件池）、
> M80 输出（场景氛围）。weather_sensitive≥60 的地点受天气影响显著。

```python
"WEATHER_SEASON": {
  "weathers": [
    {"type": "晴", "weight": 30, "mood_mod": {"joy": +10}, "effects": ["户外事件权重×1.3", "天台/操场/河堤人流上升"]},
    {"type": "多云", "weight": 25, "mood_mod": {}, "effects": ["中性天气，无加成"]},
    {"type": "雨", "weight": 20, "mood_mod": {"sadness": +5, "trust": +3},
     "effects": ["户外地点事件权重×0.3", "室内地点×1.3", "共伞/避雨偶遇概率上升", "雨天专属事件解锁"]},
    {"type": "暴雨", "weight": 5, "mood_mod": {"fear": +8, "sadness": +5},
     "effects": ["户外事件禁用", "迟到/停课事件", "停电", "被困室内"]},
    {"type": "雪", "weight": 5, "mood_mod": {"joy": +8, "surprise": +5},
     "effects": ["户外事件权重×0.7", "打雪仗/堆雪人事件", "交通延迟"]},
    {"type": "台风", "weight": 3, "mood_mod": {"fear": +15, "surprise": +10},
     "effects": ["临时停课", "断电", "避难场景", "灾害应急事件"]},
    {"type": "梅雨", "weight": 8, "mood_mod": {"sadness": +5, "disgust": +3},
     "effects": ["连续降雨状态", "心情普遍低落", "室内社交事件权重×1.2"]},
    {"type": "高温", "weight": 4, "mood_mod": {"anger": +6, "disgust": +4},
     "effects": ["中暑事件", "空调争夺", "情绪易怒", "户外活动缩短"]}
  ],
  "seasons": [
    {"season": "春", "month_range": [3, 5], "events": ["樱花观赏","开学典礼","社团招新","换座位","春假结束"],
     "mood_mod": {"joy": +5}, "location_boost": {"L004天台": +10, "L023中庭": +15, "L026神社": +10, "L029河堤": +10}},
    {"season": "夏", "month_range": [6, 8], "events": ["泳池开放","烟火大会","文化祭准备","夏日祭","海边/合宿","中暑事件","暑假"],
     "mood_mod": {"surprise": +5, "anger": +3}, "location_boost": {"L007泳池": +20, "L029河堤": +15, "L028便利店": +8}},
    {"season": "秋", "month_range": [9, 11], "events": ["学园祭","体育祭","红叶观赏","文化祭后夜祭","期中考","换季"],
     "mood_mod": {"anticipation": +5}, "location_boost": {"L006体育馆": +15, "L021礼堂": +15, "L024后山": +10}},
    {"season": "冬", "month_range": [12, 2], "events": ["圣诞","新年参拜","初詣","情人节","毕业季","滑雪合宿","期末考"],
     "mood_mod": {"trust": +5, "sadness": +3}, "location_boost": {"L026神社": +20, "L028便利店": +10, "L008图书馆": +10}}
  ],
  "combo": "每日 roll：先按 weight 出天气 → 按当前月落入 season → 事件池 = 天气effects事件 + 季节events事件 → 地点权重按 weather_sensitive×weather影响 + season_boost 调整 → M30 抽取"
}
```

---

