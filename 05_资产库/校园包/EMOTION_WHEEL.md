## 5.4 EMOTION_WHEEL 情绪状态机（8基础情绪）

> 用途：M20 心理状态、M22 情绪修正（步骤⑥）、M42 表面反应、M70 梦境素材。
> 每情绪含：impulse_mods（对三冲动的修正，接入 compute_impulses）、
> surface_signals（供 M42 取用）、transitions（状态转移规则）。

```python
"EMOTION_WHEEL": {
  "joy": {"name": "喜悦", "tone": "positive",
    "impulse_mods": {"sexual": +6, "mischief": +4, "escape": -4},
    "surface_signals": ["眉眼弯弯","语气上扬","哼小调","主动搭话","步伐轻快"],
    "transitions": {"joy→surprise": "突然的惊喜/惊吓", "joy→trust": "分享好消息被倾听"}},
  "trust": {"name": "信任", "tone": "positive",
    "impulse_mods": {"sexual": +5, "mischief": -2, "escape": -6},
    "surface_signals": ["放松肩膀","愿意靠近","分享秘密","降低音量","眼神柔和"],
    "transitions": {"trust→joy": "对方回应期待", "trust→anger": "信任被辜负"}},
  "fear": {"name": "恐惧", "tone": "negative",
    "impulse_mods": {"sexual": -8, "mischief": -6, "escape": +20},
    "surface_signals": ["瞳孔微缩","手攥紧","后退半步","声音发紧","频繁确认四周"],
    "transitions": {"fear→surprise": "威胁解除的反差", "fear→sadness": "恐惧事件坐实"}},
  "surprise": {"name": "惊讶", "tone": "neutral",
    "impulse_mods": {"sexual": +2, "mischief": +8, "escape": +5},
    "surface_signals": ["瞪眼","倒吸气","愣住两秒","脱口而出","身体后仰"],
    "transitions": {"surprise→joy": "惊喜是好的", "surprise→anger": "惊吓是恶意"}},
  "sadness": {"name": "悲伤", "tone": "negative",
    "impulse_mods": {"sexual": -10, "mischief": -8, "escape": +12},
    "surface_signals": ["垂眼","沉默变长","鼻音变重","整理动作变慢","避谈话题"],
    "transitions": {"sadness→anger": "悲伤转为迁怒", "sadness→trust": "被安慰后倾诉"}},
  "disgust": {"name": "厌恶", "tone": "negative",
    "impulse_mods": {"sexual": -12, "mischief": +10, "escape": +6},
    "surface_signals": ["皱眉","别过视线","指尖弹开","撇嘴","拉开距离"],
    "transitions": {"disgust→anger": "厌恶升级为敌意"}},
  "anger": {"name": "愤怒", "tone": "negative",
    "impulse_mods": {"sexual": -4, "mischief": +12, "escape": -3},
    "surface_signals": ["握拳","音量拔高","下颌绷紧","语速加快","眼神带刺"],
    "transitions": {"anger→sadness": "愤怒无力化", "anger→disgust": "愤怒转冷"}},
  "anticipation": {"name": "期待", "tone": "positive",
    "impulse_mods": {"sexual": +8, "mischief": +6, "escape": -2},
    "surface_signals": ["反复看时间","提前准备","搓手","忍不住确认","眼睛发亮"],
    "transitions": {"anticipation→joy": "期待实现", "anticipation→sadness": "期待落空"}}
}
```

---

