## 5.6 COGNITIVE_LOAD 认知负荷分级表

> 用途：M22 扳机检测步骤⑤、M20 心理状态、M42 反应强度修正。
> 按角色 stress（0-100）分级，load 为修正百分比（接入 `×(1+load/100)`）。

```python
"COGNITIVE_LOAD": {
  "grades": [
    {"grade": "低负荷",   "stress_range": [0, 30],   "load": 0,
     "signs": ["轻松接话","反应快","笑得出","注意力集中"],
     "impulse_desc": "三冲动正常表达"},
    {"grade": "中负荷",   "stress_range": [31, 60],  "load": 30,
     "signs": ["语速加快","小动作变多","容易走神","回答变短"],
     "impulse_desc": "冲动表达略放大，偶尔说错话"},
    {"grade": "高负荷",   "stress_range": [61, 85],  "load": 60,
     "signs": ["答非所问","频繁看时间","呼吸变浅","回避眼神"],
     "impulse_desc": "冲动被放大1.6倍，反应容易过激或短路"},
    {"grade": "过载",     "stress_range": [86, 100], "load": 100,
     "signs": ["崩溃边缘","身体发抖","说话断片","攻击性或彻底沉默"],
     "impulse_desc": "冲动翻倍，可能触发极端行为或宕机"}
  ],
  "grade": "按 character.stress 落入 stress_range → 返回 load 值"
}
```

---

