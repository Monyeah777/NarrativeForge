namespace Nf.Engine;

/// <summary>
/// check32 四件子扫描器（world_slots / instruction_step_audit / payload_registry / payload_consumer）的
/// **金标向量**——每条 = (合成/真仓输入文件集, **真源导出的 (issues, stats)**)，机械导出（导出件
/// <c>_aux_golden.cs.txt</c> 留档）。真仓那四条 = 真材料（引擎在真仓上跑出的结果须与真源逐字段一致）；
/// 合成那十条 = 覆盖各判据的 FAIL 分支与边界（缺件 / 非法 kind / 未锚定路径段 / 未知子命令 /
/// 缺脚本 / 缺路径 / 死注册 / 漏登）。
/// </summary>
public static class AuxGolden
{
    /// <summary>`probes/_fixtures/_aux_golden.json`（四件 check32 子扫描器的输入文件集 + 真源导出期望）。机械导出。</summary>
    public const string GoldenJson = @"[
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""arrays"": 3,
    ""slots"": 10
   }
  },
  ""files"": {},
  ""name"": ""world_slots"",
  ""scanner"": ""world_slots""
 },
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""docs"": 5,
    ""steps"": 9
   }
  },
  ""files"": {},
  ""name"": ""instruction_step_audit"",
  ""scanner"": ""instruction_step_audit""
 },
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""declared"": 442,
    ""pending"": 1,
    ""registered"": 443,
    ""used"": 443
   }
  },
  ""files"": {},
  ""name"": ""payload_registry"",
  ""scanner"": ""payload_registry""
 },
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""consumer_map"": {
     ""a01_report_conflict"": [
      ""大语言模型:M01""
     ],
     ""a01_report_ready"": [
      ""大语言模型:M01""
     ],
     ""a01_spec_conflict"": [
      ""大语言模型:M02""
     ],
     ""a01_spec_ready"": [
      ""大语言模型:M02""
     ],
     ""a02_report_conflict"": [
      ""多模态大模型:M01""
     ],
     ""a02_report_ready"": [
      ""多模态大模型:M01""
     ],
     ""a02_spec_conflict"": [
      ""多模态大模型:M02""
     ],
     ""a02_spec_ready"": [
      ""多模态大模型:M02""
     ],
     ""a03_report_conflict"": [
      ""视觉模型:M01""
     ],
     ""a03_report_ready"": [
      ""视觉模型:M01""
     ],
     ""a03_spec_conflict"": [
      ""视觉模型:M02""
     ],
     ""a03_spec_ready"": [
      ""视觉模型:M02""
     ],
     ""a04_report_conflict"": [
      ""语音识别与合成:M01""
     ],
     ""a04_report_ready"": [
      ""语音识别与合成:M01""
     ],
     ""a04_spec_conflict"": [
      ""语音识别与合成:M02""
     ],
     ""a04_spec_ready"": [
      ""语音识别与合成:M02""
     ],
     ""a05_report_conflict"": [
      ""音频与音乐生成:M01""
     ],
     ""a05_report_ready"": [
      ""音频与音乐生成:M01""
     ],
     ""a05_spec_conflict"": [
      ""音频与音乐生成:M02""
     ],
     ""a05_spec_ready"": [
      ""音频与音乐生成:M02""
     ],
     ""a06_report_conflict"": [
      ""视频生成与理解:M01""
     ],
     ""a06_report_ready"": [
      ""视频生成与理解:M01""
     ],
     ""a06_spec_conflict"": [
      ""视频生成与理解:M02""
     ],
     ""a06_spec_ready"": [
      ""视频生成与理解:M02""
     ],
     ""a07_report_conflict"": [
      ""图像生成与编辑:M01""
     ],
     ""a07_report_ready"": [
      ""图像生成与编辑:M01""
     ],
     ""a07_spec_conflict"": [
      ""图像生成与编辑:M02""
     ],
     ""a07_spec_ready"": [
      ""图像生成与编辑:M02""
     ],
     ""a08_report_conflict"": [
      ""三维与世界模型:M01""
     ],
     ""a08_report_ready"": [
      ""三维与世界模型:M01""
     ],
     ""a08_spec_conflict"": [
      ""三维与世界模型:M02""
     ],
     ""a08_spec_ready"": [
      ""三维与世界模型:M02""
     ],
     ""a09_report_conflict"": [
      ""代码大模型:M01""
     ],
     ""a09_report_ready"": [
      ""代码大模型:M01""
     ],
     ""a09_spec_conflict"": [
      ""代码大模型:M02""
     ],
     ""a09_spec_ready"": [
      ""代码大模型:M02""
     ],
     ""a10_report_conflict"": [
      ""数学与形式化推理:M01""
     ],
     ""a10_report_ready"": [
      ""数学与形式化推理:M01""
     ],
     ""a10_spec_conflict"": [
      ""数学与形式化推理:M02""
     ],
     ""a10_spec_ready"": [
      ""数学与形式化推理:M02""
     ],
     ""a11_report_conflict"": [
      ""嵌入与检索表示:M01""
     ],
     ""a11_report_ready"": [
      ""嵌入与检索表示:M01""
     ],
     ""a11_spec_conflict"": [
      ""嵌入与检索表示:M02""
     ],
     ""a11_spec_ready"": [
      ""嵌入与检索表示:M02""
     ],
     ""a12_report_conflict"": [
      ""强化学习与决策:M01""
     ],
     ""a12_report_ready"": [
      ""强化学习与决策:M01""
     ],
     ""a12_spec_conflict"": [
      ""强化学习与决策:M02""
     ],
     ""a12_spec_ready"": [
      ""强化学习与决策:M02""
     ],
     ""a13_report_conflict"": [
      ""具身智能与机器人:M01""
     ],
     ""a13_report_ready"": [
      ""具身智能与机器人:M01""
     ],
     ""a13_spec_conflict"": [
      ""具身智能与机器人:M02""
     ],
     ""a13_spec_ready"": [
      ""具身智能与机器人:M02""
     ],
     ""a14_report_conflict"": [
      ""端侧与边缘小模型:M01""
     ],
     ""a14_report_ready"": [
      ""端侧与边缘小模型:M01""
     ],
     ""a14_spec_conflict"": [
      ""端侧与边缘小模型:M02""
     ],
     ""a14_spec_ready"": [
      ""端侧与边缘小模型:M02""
     ],
     ""b01_report_conflict"": [
      ""文本生成与创作:M01""
     ],
     ""b01_report_ready"": [
      ""文本生成与创作:M01""
     ],
     ""b01_spec_conflict"": [
      ""文本生成与创作:M02""
     ],
     ""b01_spec_ready"": [
      ""文本生成与创作:M02""
     ],
     ""b02_report_conflict"": [
      ""摘要与信息压缩:M01""
     ],
     ""b02_report_ready"": [
      ""摘要与信息压缩:M01""
     ],
     ""b02_spec_conflict"": [
      ""摘要与信息压缩:M02""
     ],
     ""b02_spec_ready"": [
      ""摘要与信息压缩:M02""
     ],
     ""b03_report_conflict"": [
      ""机器翻译与本地化:M01""
     ],
     ""b03_report_ready"": [
      ""机器翻译与本地化:M01""
     ],
     ""b03_spec_conflict"": [
      ""机器翻译与本地化:M02""
     ],
     ""b03_spec_ready"": [
      ""机器翻译与本地化:M02""
     ],
     ""b04_report_conflict"": [
      ""分类与情感分析:M01""
     ],
     ""b04_report_ready"": [
      ""分类与情感分析:M01""
     ],
     ""b04_spec_conflict"": [
      ""分类与情感分析:M02""
     ],
     ""b04_spec_ready"": [
      ""分类与情感分析:M02""
     ],
     ""b05_report_conflict"": [
      ""信息抽取与结构化:M01""
     ],
     ""b05_report_ready"": [
      ""信息抽取与结构化:M01""
     ],
     ""b05_spec_conflict"": [
      ""信息抽取与结构化:M02""
     ],
     ""b05_spec_ready"": [
      ""信息抽取与结构化:M02""
     ],
     ""b06_report_conflict"": [
      ""知识问答与检索增强:M01""
     ],
     ""b06_report_ready"": [
      ""知识问答与检索增强:M01""
     ],
     ""b06_spec_conflict"": [
      ""知识问答与检索增强:M02""
     ],
     ""b06_spec_ready"": [
      ""知识问答与检索增强:M02""
     ],
     ""b07_report_conflict"": [
      ""多轮对话与角色扮演:M01""
     ],
     ""b07_report_ready"": [
      ""多轮对话与角色扮演:M01""
     ],
     ""b07_spec_conflict"": [
      ""多轮对话与角色扮演:M02""
     ],
     ""b07_spec_ready"": [
      ""多轮对话与角色扮演:M02""
     ],
     ""b08_report_conflict"": [
      ""代码生成与补全:M01""
     ],
     ""b08_report_ready"": [
      ""代码生成与补全:M01""
     ],
     ""b08_spec_conflict"": [
      ""代码生成与补全:M02""
     ],
     ""b08_spec_ready"": [
      ""代码生成与补全:M02""
     ],
     ""b09_report_conflict"": [
      ""代码审查与缺陷检测:M01""
     ],
     ""b09_report_ready"": [
      ""代码审查与缺陷检测:M01""
     ],
     ""b09_spec_conflict"": [
      ""代码审查与缺陷检测:M02""
     ],
     ""b09_spec_ready"": [
      ""代码审查与缺陷检测:M02""
     ],
     ""b10_report_conflict"": [
      ""测试与用例生成:M01""
     ],
     ""b10_report_ready"": [
      ""测试与用例生成:M01""
     ],
     ""b10_spec_conflict"": [
      ""测试与用例生成:M02""
     ],
     ""b10_spec_ready"": [
      ""测试与用例生成:M02""
     ],
     ""b11_report_conflict"": [
      ""数据分析与表格理解:M01""
     ],
     ""b11_report_ready"": [
      ""数据分析与表格理解:M01""
     ],
     ""b11_spec_conflict"": [
      ""数据分析与表格理解:M02""
     ],
     ""b11_spec_ready"": [
      ""数据分析与表格理解:M02""
     ],
     ""b12_report_conflict"": [
      ""文档解析与版面理解:M01""
     ],
     ""b12_report_ready"": [
      ""文档解析与版面理解:M01""
     ],
     ""b12_spec_conflict"": [
      ""文档解析与版面理解:M02""
     ],
     ""b12_spec_ready"": [
      ""文档解析与版面理解:M02""
     ],
     ""b13_report_conflict"": [
      ""语音转写与会议记录:M01""
     ],
     ""b13_report_ready"": [
      ""语音转写与会议记录:M01""
     ],
     ""b13_spec_conflict"": [
      ""语音转写与会议记录:M02""
     ],
     ""b13_spec_ready"": [
      ""语音转写与会议记录:M02""
     ],
     ""b14_report_conflict"": [
      ""语音合成与配音:M01""
     ],
     ""b14_report_ready"": [
      ""语音合成与配音:M01""
     ],
     ""b14_spec_conflict"": [
      ""语音合成与配音:M02""
     ],
     ""b14_spec_ready"": [
      ""语音合成与配音:M02""
     ],
     ""b15_report_conflict"": [
      ""图像生成与视觉设计:M01""
     ],
     ""b15_report_ready"": [
      ""图像生成与视觉设计:M01""
     ],
     ""b15_spec_conflict"": [
      ""图像生成与视觉设计:M02""
     ],
     ""b15_spec_ready"": [
      ""图像生成与视觉设计:M02""
     ],
     ""b16_report_conflict"": [
      ""视频生成与自动剪辑:M01""
     ],
     ""b16_report_ready"": [
      ""视频生成与自动剪辑:M01""
     ],
     ""b16_spec_conflict"": [
      ""视频生成与自动剪辑:M02""
     ],
     ""b16_spec_ready"": [
      ""视频生成与自动剪辑:M02""
     ],
     ""b17_report_conflict"": [
      ""推荐排序与广告:M01""
     ],
     ""b17_report_ready"": [
      ""推荐排序与广告:M01""
     ],
     ""b17_spec_conflict"": [
      ""推荐排序与广告:M02""
     ],
     ""b17_spec_ready"": [
      ""推荐排序与广告:M02""
     ],
     ""b18_report_conflict"": [
      ""预测异常与风险:M01""
     ],
     ""b18_report_ready"": [
      ""预测异常与风险:M01""
     ],
     ""b18_spec_conflict"": [
      ""预测异常与风险:M02""
     ],
     ""b18_spec_ready"": [
      ""预测异常与风险:M02""
     ],
     ""backtest_spec_conflict"": [],
     ""backtest_spec_ready"": [],
     ""beat_tick"": [
      ""M95""
     ],
     ""c01_report_conflict"": [
      ""数据采集与清洗:M01""
     ],
     ""c01_report_ready"": [
      ""数据采集与清洗:M01""
     ],
     ""c01_spec_conflict"": [
      ""数据采集与清洗:M02""
     ],
     ""c01_spec_ready"": [
      ""数据采集与清洗:M02""
     ],
     ""c02_report_conflict"": [
      ""数据标注与标注质量:M01""
     ],
     ""c02_report_ready"": [
      ""数据标注与标注质量:M01""
     ],
     ""c02_spec_conflict"": [
      ""数据标注与标注质量:M02""
     ],
     ""c02_spec_ready"": [
      ""数据标注与标注质量:M02""
     ],
     ""c03_report_conflict"": [
      ""合成数据生成:M01""
     ],
     ""c03_report_ready"": [
      ""合成数据生成:M01""
     ],
     ""c03_spec_conflict"": [
      ""合成数据生成:M02""
     ],
     ""c03_spec_ready"": [
      ""合成数据生成:M02""
     ],
     ""c04_report_conflict"": [
      ""预训练与继续预训练:M01""
     ],
     ""c04_report_ready"": [
      ""预训练与继续预训练:M01""
     ],
     ""c04_spec_conflict"": [
      ""预训练与继续预训练:M02""
     ],
     ""c04_spec_ready"": [
      ""预训练与继续预训练:M02""
     ],
     ""c05_report_conflict"": [
      ""监督微调:M01""
     ],
     ""c05_report_ready"": [
      ""监督微调:M01""
     ],
     ""c05_spec_conflict"": [
      ""监督微调:M02""
     ],
     ""c05_spec_ready"": [
      ""监督微调:M02""
     ],
     ""c06_report_conflict"": [
      ""参数高效微调:M01""
     ],
     ""c06_report_ready"": [
      ""参数高效微调:M01""
     ],
     ""c06_spec_conflict"": [
      ""参数高效微调:M02""
     ],
     ""c06_spec_ready"": [
      ""参数高效微调:M02""
     ],
     ""c07_report_conflict"": [
      ""对齐与偏好优化:M01""
     ],
     ""c07_report_ready"": [
      ""对齐与偏好优化:M01""
     ],
     ""c07_spec_conflict"": [
      ""对齐与偏好优化:M02""
     ],
     ""c07_spec_ready"": [
      ""对齐与偏好优化:M02""
     ],
     ""c08_report_conflict"": [
      ""评测基准与排行榜:M01""
     ],
     ""c08_report_ready"": [
      ""评测基准与排行榜:M01""
     ],
     ""c08_spec_conflict"": [
      ""评测基准与排行榜:M02""
     ],
     ""c08_spec_ready"": [
      ""评测基准与排行榜:M02""
     ],
     ""c09_report_conflict"": [
      ""红队越狱与安全测试:M01""
     ],
     ""c09_report_ready"": [
      ""红队越狱与安全测试:M01""
     ],
     ""c09_spec_conflict"": [
      ""红队越狱与安全测试:M02""
     ],
     ""c09_spec_ready"": [
      ""红队越狱与安全测试:M02""
     ],
     ""c10_report_conflict"": [
      ""推理优化与加速:M01""
     ],
     ""c10_report_ready"": [
      ""推理优化与加速:M01""
     ],
     ""c10_spec_conflict"": [
      ""推理优化与加速:M02""
     ],
     ""c10_spec_ready"": [
      ""推理优化与加速:M02""
     ],
     ""c11_report_conflict"": [
      ""推理服务与部署:M01""
     ],
     ""c11_report_ready"": [
      ""推理服务与部署:M01""
     ],
     ""c11_spec_conflict"": [
      ""推理服务与部署:M02""
     ],
     ""c11_spec_ready"": [
      ""推理服务与部署:M02""
     ],
     ""c12_report_conflict"": [
      ""上下文工程与长上下文:M01""
     ],
     ""c12_report_ready"": [
      ""上下文工程与长上下文:M01""
     ],
     ""c12_spec_conflict"": [
      ""上下文工程与长上下文:M02""
     ],
     ""c12_spec_ready"": [
      ""上下文工程与长上下文:M02""
     ],
     ""c13_report_conflict"": [
      ""提示工程与提示模板:M01""
     ],
     ""c13_report_ready"": [
      ""提示工程与提示模板:M01""
     ],
     ""c13_spec_conflict"": [
      ""提示工程与提示模板:M02""
     ],
     ""c13_spec_ready"": [
      ""提示工程与提示模板:M02""
     ],
     ""c14_report_conflict"": [
      ""记忆体与个性化:M01""
     ],
     ""c14_report_ready"": [
      ""记忆体与个性化:M01""
     ],
     ""c14_spec_conflict"": [
      ""记忆体与个性化:M02""
     ],
     ""c14_spec_ready"": [
      ""记忆体与个性化:M02""
     ],
     ""c15_report_conflict"": [
      ""向量库与检索管线:M01""
     ],
     ""c15_report_ready"": [
      ""向量库与检索管线:M01""
     ],
     ""c15_spec_conflict"": [
      ""向量库与检索管线:M02""
     ],
     ""c15_spec_ready"": [
      ""向量库与检索管线:M02""
     ],
     ""c16_report_conflict"": [
      ""智能体框架与工具调用:M01""
     ],
     ""c16_report_ready"": [
      ""智能体框架与工具调用:M01""
     ],
     ""c16_spec_conflict"": [
      ""智能体框架与工具调用:M02""
     ],
     ""c16_spec_ready"": [
      ""智能体框架与工具调用:M02""
     ],
     ""c17_report_conflict"": [
      ""多智能体协同:M01""
     ],
     ""c17_report_ready"": [
      ""多智能体协同:M01""
     ],
     ""c17_spec_conflict"": [
      ""多智能体协同:M02""
     ],
     ""c17_spec_ready"": [
      ""多智能体协同:M02""
     ],
     ""c18_report_conflict"": [
      ""可观测性成本与可靠性:M01""
     ],
     ""c18_report_ready"": [
      ""可观测性成本与可靠性:M01""
     ],
     ""c18_spec_conflict"": [
      ""可观测性成本与可靠性:M02""
     ],
     ""c18_spec_ready"": [
      ""可观测性成本与可靠性:M02""
     ],
     ""campus_anonymous_gift"": [],
     ""campus_gift_intent"": [],
     ""chaos_event"": [
      ""M06"",
      ""M10"",
      ""事件:M22""
     ],
     ""combat_result"": [
      ""M01"",
      ""M03"",
      ""M06"",
      ""M10""
     ],
     ""concept_closure_ready"": [
      ""AI系统:M26""
     ],
     ""confession_event"": [
      ""M55"",
      ""M91""
     ],
     ""d01_report_conflict"": [
      ""AI医疗健康:M01""
     ],
     ""d01_report_ready"": [
      ""AI医疗健康:M01""
     ],
     ""d01_spec_conflict"": [
      ""AI医疗健康:M02""
     ],
     ""d01_spec_ready"": [
      ""AI医疗健康:M02""
     ],
     ""d02_report_conflict"": [
      ""AI制药与生物:M01""
     ],
     ""d02_report_ready"": [
      ""AI制药与生物:M01""
     ],
     ""d02_spec_conflict"": [
      ""AI制药与生物:M02""
     ],
     ""d02_spec_ready"": [
      ""AI制药与生物:M02""
     ],
     ""d03_report_conflict"": [
      ""AI法律与合规:M01""
     ],
     ""d03_report_ready"": [
      ""AI法律与合规:M01""
     ],
     ""d03_spec_conflict"": [
      ""AI法律与合规:M02""
     ],
     ""d03_spec_ready"": [
      ""AI法律与合规:M02""
     ],
     ""d04_report_conflict"": [
      ""AI金融投研与风控:M01""
     ],
     ""d04_report_ready"": [
      ""AI金融投研与风控:M01""
     ],
     ""d04_spec_conflict"": [
      ""AI金融投研与风控:M02""
     ],
     ""d04_spec_ready"": [
      ""AI金融投研与风控:M02""
     ],
     ""d05_report_conflict"": [
      ""AI保险:M01""
     ],
     ""d05_report_ready"": [
      ""AI保险:M01""
     ],
     ""d05_spec_conflict"": [
      ""AI保险:M02""
     ],
     ""d05_spec_ready"": [
      ""AI保险:M02""
     ],
     ""d06_report_conflict"": [
      ""AI教育:M01""
     ],
     ""d06_report_ready"": [
      ""AI教育:M01""
     ],
     ""d06_spec_conflict"": [
      ""AI教育:M02""
     ],
     ""d06_spec_ready"": [
      ""AI教育:M02""
     ],
     ""d07_report_conflict"": [
      ""AI政务与公共事务:M01""
     ],
     ""d07_report_ready"": [
      ""AI政务与公共事务:M01""
     ],
     ""d07_spec_conflict"": [
      ""AI政务与公共事务:M02""
     ],
     ""d07_spec_ready"": [
      ""AI政务与公共事务:M02""
     ],
     ""d08_report_conflict"": [
      ""AI制造业:M01""
     ],
     ""d08_report_ready"": [
      ""AI制造业:M01""
     ],
     ""d08_spec_conflict"": [
      ""AI制造业:M02""
     ],
     ""d08_spec_ready"": [
      ""AI制造业:M02""
     ],
     ""d09_report_conflict"": [
      ""AI能源与电力:M01""
     ],
     ""d09_report_ready"": [
      ""AI能源与电力:M01""
     ],
     ""d09_spec_conflict"": [
      ""AI能源与电力:M02""
     ],
     ""d09_spec_ready"": [
      ""AI能源与电力:M02""
     ],
     ""d10_report_conflict"": [
      ""AI农业:M01""
     ],
     ""d10_report_ready"": [
      ""AI农业:M01""
     ],
     ""d10_spec_conflict"": [
      ""AI农业:M02""
     ],
     ""d10_spec_ready"": [
      ""AI农业:M02""
     ],
     ""d11_report_conflict"": [
      ""零售与电商:M01""
     ],
     ""d11_report_ready"": [
      ""零售与电商:M01""
     ],
     ""d11_spec_conflict"": [
      ""零售与电商:M02""
     ],
     ""d11_spec_ready"": [
      ""零售与电商:M02""
     ],
     ""d12_report_conflict"": [
      ""物流与供应链:M01""
     ],
     ""d12_report_ready"": [
      ""物流与供应链:M01""
     ],
     ""d12_spec_conflict"": [
      ""物流与供应链:M02""
     ],
     ""d12_spec_ready"": [
      ""物流与供应链:M02""
     ],
     ""d13_report_conflict"": [
      ""交通与出行:M01""
     ],
     ""d13_report_ready"": [
      ""交通与出行:M01""
     ],
     ""d13_spec_conflict"": [
      ""交通与出行:M02""
     ],
     ""d13_spec_ready"": [
      ""交通与出行:M02""
     ],
     ""d14_report_conflict"": [
      ""AI人力资源与招聘:M01""
     ],
     ""d14_report_ready"": [
      ""AI人力资源与招聘:M01""
     ],
     ""d14_spec_conflict"": [
      ""AI人力资源与招聘:M02""
     ],
     ""d14_spec_ready"": [
      ""AI人力资源与招聘:M02""
     ],
     ""d15_report_conflict"": [
      ""建筑与房地产:M01""
     ],
     ""d15_report_ready"": [
      ""建筑与房地产:M01""
     ],
     ""d15_spec_conflict"": [
      ""建筑与房地产:M02""
     ],
     ""d15_spec_ready"": [
      ""建筑与房地产:M02""
     ],
     ""d16_report_conflict"": [
      ""AI食品与餐饮:M01""
     ],
     ""d16_report_ready"": [
      ""AI食品与餐饮:M01""
     ],
     ""d16_spec_conflict"": [
      ""AI食品与餐饮:M02""
     ],
     ""d16_spec_ready"": [
      ""AI食品与餐饮:M02""
     ],
     ""d17_report_conflict"": [
      ""传媒与新闻:M01""
     ],
     ""d17_report_ready"": [
      ""传媒与新闻:M01""
     ],
     ""d17_spec_conflict"": [
      ""传媒与新闻:M02""
     ],
     ""d17_spec_ready"": [
      ""传媒与新闻:M02""
     ],
     ""d18_report_conflict"": [
      ""游戏与互动娱乐:M01""
     ],
     ""d18_report_ready"": [
      ""游戏与互动娱乐:M01""
     ],
     ""d18_spec_conflict"": [
      ""游戏与互动娱乐:M02""
     ],
     ""d18_spec_ready"": [
      ""游戏与互动娱乐:M02""
     ],
     ""d19_report_conflict"": [
      ""文旅与酒店:M01""
     ],
     ""d19_report_ready"": [
      ""文旅与酒店:M01""
     ],
     ""d19_spec_conflict"": [
      ""文旅与酒店:M02""
     ],
     ""d19_spec_ready"": [
      ""文旅与酒店:M02""
     ],
     ""d20_report_conflict"": [
      ""科研与实验:M01""
     ],
     ""d20_report_ready"": [
      ""科研与实验:M01""
     ],
     ""d20_spec_conflict"": [
      ""科研与实验:M02""
     ],
     ""d20_spec_ready"": [
      ""科研与实验:M02""
     ],
     ""death_trigger"": [
      ""事件:M22""
     ],
     ""decision_brief"": [
      ""M96""
     ],
     ""doc_delta_committed"": [
      ""M98""
     ],
     ""doc_structure_ready"": [
      ""M97"",
      ""M98""
     ],
     ""e01_report_conflict"": [
      ""提示工程与指令设计:M01""
     ],
     ""e01_report_ready"": [
      ""提示工程与指令设计:M01""
     ],
     ""e01_spec_conflict"": [
      ""提示工程与指令设计:M02""
     ],
     ""e01_spec_ready"": [
      ""提示工程与指令设计:M02""
     ],
     ""e02_report_conflict"": [
      ""角色扮演与角色卡:M01""
     ],
     ""e02_report_ready"": [
      ""角色扮演与角色卡:M01""
     ],
     ""e02_spec_conflict"": [
      ""角色扮演与角色卡:M02""
     ],
     ""e02_spec_ready"": [
      ""角色扮演与角色卡:M02""
     ],
     ""e03_report_conflict"": [
      ""世界书与设定库:M01""
     ],
     ""e03_report_ready"": [
      ""世界书与设定库:M01""
     ],
     ""e03_spec_conflict"": [
      ""世界书与设定库:M02""
     ],
     ""e03_spec_ready"": [
      ""世界书与设定库:M02""
     ],
     ""e04_report_conflict"": [
      ""长文本与小说创作:M01""
     ],
     ""e04_report_ready"": [
      ""长文本与小说创作:M01""
     ],
     ""e04_spec_conflict"": [
      ""长文本与小说创作:M02""
     ],
     ""e04_spec_ready"": [
      ""长文本与小说创作:M02""
     ],
     ""e05_report_conflict"": [
      ""内容改写与风格迁移:M01""
     ],
     ""e05_report_ready"": [
      ""内容改写与风格迁移:M01""
     ],
     ""e05_spec_conflict"": [
      ""内容改写与风格迁移:M02""
     ],
     ""e05_spec_ready"": [
      ""内容改写与风格迁移:M02""
     ],
     ""e06_report_conflict"": [
      ""多语翻译与本地化:M01""
     ],
     ""e06_report_ready"": [
      ""多语翻译与本地化:M01""
     ],
     ""e06_spec_conflict"": [
      ""多语翻译与本地化:M02""
     ],
     ""e06_spec_ready"": [
      ""多语翻译与本地化:M02""
     ],
     ""e07_report_conflict"": [
      ""图像生成与视觉创作:M01""
     ],
     ""e07_report_ready"": [
      ""图像生成与视觉创作:M01""
     ],
     ""e07_spec_conflict"": [
      ""图像生成与视觉创作:M02""
     ],
     ""e07_spec_ready"": [
      ""图像生成与视觉创作:M02""
     ],
     ""e08_report_conflict"": [
      ""视频生成与剪辑:M01""
     ],
     ""e08_report_ready"": [
      ""视频生成与剪辑:M01""
     ],
     ""e08_spec_conflict"": [
      ""视频生成与剪辑:M02""
     ],
     ""e08_spec_ready"": [
      ""视频生成与剪辑:M02""
     ],
     ""e09_report_conflict"": [
      ""音频音乐与语音:M01""
     ],
     ""e09_report_ready"": [
      ""音频音乐与语音:M01""
     ],
     ""e09_spec_conflict"": [
      ""音频音乐与语音:M02""
     ],
     ""e09_spec_ready"": [
      ""音频音乐与语音:M02""
     ],
     ""e10_report_conflict"": [
      ""编辑校对与出版:M01""
     ],
     ""e10_report_ready"": [
      ""编辑校对与出版:M01""
     ],
     ""e10_spec_conflict"": [
      ""编辑校对与出版:M02""
     ],
     ""e10_spec_ready"": [
      ""编辑校对与出版:M02""
     ],
     ""e11_report_conflict"": [
      ""知识管理与检索增强:M01""
     ],
     ""e11_report_ready"": [
      ""知识管理与检索增强:M01""
     ],
     ""e11_spec_conflict"": [
      ""知识管理与检索增强:M02""
     ],
     ""e11_spec_ready"": [
      ""知识管理与检索增强:M02""
     ],
     ""e12_report_conflict"": [
      ""智能体与工作流编排:M01""
     ],
     ""e12_report_ready"": [
      ""智能体与工作流编排:M01""
     ],
     ""e12_spec_conflict"": [
      ""智能体与工作流编排:M02""
     ],
     ""e12_spec_ready"": [
      ""智能体与工作流编排:M02""
     ],
     ""e13_report_conflict"": [
      ""代码与软件工程:M01""
     ],
     ""e13_report_ready"": [
      ""代码与软件工程:M01""
     ],
     ""e13_spec_conflict"": [
      ""代码与软件工程:M02""
     ],
     ""e13_spec_ready"": [
      ""代码与软件工程:M02""
     ],
     ""e14_report_conflict"": [
      ""数据分析与决策支持:M01""
     ],
     ""e14_report_ready"": [
      ""数据分析与决策支持:M01""
     ],
     ""e14_spec_conflict"": [
      ""数据分析与决策支持:M02""
     ],
     ""e14_spec_ready"": [
      ""数据分析与决策支持:M02""
     ],
     ""e15_report_conflict"": [
      ""企业培训与组织学习:M01""
     ],
     ""e15_report_ready"": [
      ""企业培训与组织学习:M01""
     ],
     ""e15_spec_conflict"": [
      ""企业培训与组织学习:M02""
     ],
     ""e15_spec_ready"": [
      ""企业培训与组织学习:M02""
     ],
     ""e16_report_conflict"": [
      ""个人助理与日常生活:M01""
     ],
     ""e16_report_ready"": [
      ""个人助理与日常生活:M01""
     ],
     ""e16_spec_conflict"": [
      ""个人助理与日常生活:M02""
     ],
     ""e16_spec_ready"": [
      ""个人助理与日常生活:M02""
     ],
     ""e17_report_conflict"": [
      ""搜索与信息聚合:M01""
     ],
     ""e17_report_ready"": [
      ""搜索与信息聚合:M01""
     ],
     ""e17_spec_conflict"": [
      ""搜索与信息聚合:M02""
     ],
     ""e17_spec_ready"": [
      ""搜索与信息聚合:M02""
     ],
     ""e18_report_conflict"": [
      ""对话与客服:M01""
     ],
     ""e18_report_ready"": [
      ""对话与客服:M01""
     ],
     ""e18_spec_conflict"": [
      ""对话与客服:M02""
     ],
     ""e18_spec_ready"": [
      ""对话与客服:M02""
     ],
     ""e19_report_conflict"": [
      ""内容分发与社区运营:M01""
     ],
     ""e19_report_ready"": [
      ""内容分发与社区运营:M01""
     ],
     ""e19_spec_conflict"": [
      ""内容分发与社区运营:M02""
     ],
     ""e19_spec_ready"": [
      ""内容分发与社区运营:M02""
     ],
     ""e20_report_conflict"": [
      ""数字人与虚拟形象:M01""
     ],
     ""e20_report_ready"": [
      ""数字人与虚拟形象:M01""
     ],
     ""e20_spec_conflict"": [
      ""数字人与虚拟形象:M02""
     ],
     ""e20_spec_ready"": [
      ""数字人与虚拟形象:M02""
     ],
     ""f01_report_conflict"": [
      ""安全与对齐:M01""
     ],
     ""f01_report_ready"": [
      ""安全与对齐:M01""
     ],
     ""f01_spec_conflict"": [
      ""安全与对齐:M02""
     ],
     ""f01_spec_ready"": [
      ""安全与对齐:M02""
     ],
     ""f02_report_conflict"": [
      ""合规与监管:M01""
     ],
     ""f02_report_ready"": [
      ""合规与监管:M01""
     ],
     ""f02_spec_conflict"": [
      ""合规与监管:M02""
     ],
     ""f02_spec_ready"": [
      ""合规与监管:M02""
     ],
     ""f03_report_conflict"": [
      ""隐私与数据治理:M01""
     ],
     ""f03_report_ready"": [
      ""隐私与数据治理:M01""
     ],
     ""f03_spec_conflict"": [
      ""隐私与数据治理:M02""
     ],
     ""f03_spec_ready"": [
      ""隐私与数据治理:M02""
     ],
     ""f04_report_conflict"": [
      ""版权与知识产权:M01""
     ],
     ""f04_report_ready"": [
      ""版权与知识产权:M01""
     ],
     ""f04_spec_conflict"": [
      ""版权与知识产权:M02""
     ],
     ""f04_spec_ready"": [
      ""版权与知识产权:M02""
     ],
     ""f05_report_conflict"": [
      ""评测与基准:M01""
     ],
     ""f05_report_ready"": [
      ""评测与基准:M01""
     ],
     ""f05_spec_conflict"": [
      ""评测与基准:M02""
     ],
     ""f05_spec_ready"": [
      ""评测与基准:M02""
     ],
     ""f06_report_conflict"": [
      ""可解释性与审计:M01""
     ],
     ""f06_report_ready"": [
      ""可解释性与审计:M01""
     ],
     ""f06_spec_conflict"": [
      ""可解释性与审计:M02""
     ],
     ""f06_spec_ready"": [
      ""可解释性与审计:M02""
     ],
     ""f07_report_conflict"": [
      ""模型运营与成本:M01""
     ],
     ""f07_report_ready"": [
      ""模型运营与成本:M01""
     ],
     ""f07_spec_conflict"": [
      ""模型运营与成本:M02""
     ],
     ""f07_spec_ready"": [
      ""模型运营与成本:M02""
     ],
     ""f08_report_conflict"": [
      ""平台与基础设施:M01""
     ],
     ""f08_report_ready"": [
      ""平台与基础设施:M01""
     ],
     ""f08_spec_conflict"": [
      ""平台与基础设施:M02""
     ],
     ""f08_spec_ready"": [
      ""平台与基础设施:M02""
     ],
     ""f09_report_conflict"": [
      ""开源与开发者生态:M01""
     ],
     ""f09_report_ready"": [
      ""开源与开发者生态:M01""
     ],
     ""f09_spec_conflict"": [
      ""开源与开发者生态:M02""
     ],
     ""f09_spec_ready"": [
      ""开源与开发者生态:M02""
     ],
     ""f10_report_conflict"": [
      ""产业与商业落地:M01""
     ],
     ""f10_report_ready"": [
      ""产业与商业落地:M01""
     ],
     ""f10_spec_conflict"": [
      ""产业与商业落地:M02""
     ],
     ""f10_spec_ready"": [
      ""产业与商业落地:M02""
     ],
     ""factor_spec_conflict"": [
      ""量化金融:M32""
     ],
     ""factor_spec_ready"": [
      ""量化金融:M32""
     ],
     ""ghost_event"": [
      ""事件:M22""
     ],
     ""group_chat_event"": [],
     ""intent_received"": [
      ""M90""
     ],
     ""interaction_update"": [
      ""M95"",
      ""事件:M22""
     ],
     ""level_up"": [
      ""M03"",
      ""M13""
     ],
     ""load_order_ready"": [],
     ""market_event"": [
      ""M17"",
      ""事件:M22""
     ],
     ""minute_tick"": [
      ""M01"",
      ""M93"",
      ""M94""
     ],
     ""narrative_event"": [
      ""M96""
     ],
     ""npc_action"": [
      ""M43"",
      ""M55"",
      ""M57"",
      ""M58"",
      ""M59"",
      ""M91""
     ],
     ""phone_call_event"": [],
     ""polished_output"": [],
     ""prereq_missing"": [
      ""AI系统:M26""
     ],
     ""production_output"": [
      ""M92"",
      ""事件:M22""
     ],
     ""quest_state"": [
      ""M10"",
      ""M13"",
      ""M57"",
      ""M58"",
      ""M59"",
      ""M95""
     ],
     ""relationship_change"": [
      ""M43"",
      ""M55"",
      ""M57"",
      ""M58"",
      ""M59"",
      ""M91"",
      ""事件:M22""
     ],
     ""reputation_change"": [
      ""M06""
     ],
     ""revision_recorded"": [],
     ""romance_state_change"": [
      ""M43""
     ],
     ""social_feed_event"": [],
     ""spell_cast"": [
      ""M03""
     ],
     ""state_snapshot"": [
      ""M95""
     ],
     ""term_conflict_detected"": [
      ""M97""
     ],
     ""term_synced"": [],
     ""tick_day"": [
      ""M01"",
      ""M08"",
      ""M19"",
      ""M93"",
      ""M94""
     ],
     ""travel_event"": [
      ""M06""
     ],
     ""weather_state"": []
    },
    ""events_consumed"": 430,
    ""events_declared"": 442
   }
  },
  ""files"": {},
  ""name"": ""payload_consumer"",
  ""scanner"": ""payload_consumer""
 },
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""arrays"": 1,
    ""slots"": 2
   }
  },
  ""files"": {
   ""04_模块库/通用类/M00_数据结构.md"": ""# M00 数据结构\n\n槽位：state.mood / state.items / state.count 与 owner 说明。\n"",
   ""protocol/world_slots.json"": ""{\n  \""schema_version\"": \""1\"",\n  \""slots\"": {\n    \""state.mood\"": {\n      \""kind\"": \""string\"",\n      \""owner\"": \""M00\""\n    },\n    \""state.items\"": {\n      \""kind\"": \""array\"",\n      \""owner\"": \""M00\"",\n      \""item_kind\"": \""number\""\n    }\n  }\n}\n""
  },
  ""name"": ""world_slots/valid"",
  ""scanner"": ""world_slots""
 },
 {
  ""expected"": {
   ""issues"": [
    ""world_slots.schema_version: 应为 \""1\"""",
    ""world_slots.slots: 非空对象""
   ],
   ""stats"": {
    ""arrays"": 0,
    ""slots"": 0
   }
  },
  ""files"": {
   ""04_模块库/通用类/M00_数据结构.md"": ""# M00 数据结构\n\n槽位：state.mood / state.items / state.count 与 owner 说明。\n"",
   ""protocol/world_slots.json"": ""{\n  \""schema_version\"": \""2\"",\n  \""slots\"": {}\n}\n""
  },
  ""name"": ""world_slots/bad-head"",
  ""scanner"": ""world_slots""
 },
 {
  ""expected"": {
   ""issues"": [
    ""world_slots.slots.'state.mood'.kind: 非法类型 'wat'"",
    ""world_slots.slots.'state.mood'.owner: 非空字符串"",
    ""world_slots.slots.'state.count'.item_kind: 仅 kind=array 可用"",
    ""world_slots slot 路径段未在 M00 文档锚定：'ghost'（state.ghost）""
   ],
   ""stats"": {
    ""arrays"": 0,
    ""slots"": 3
   }
  },
  ""files"": {
   ""04_模块库/通用类/M00_数据结构.md"": ""# M00 数据结构\n\n槽位：state.mood / state.items / state.count 与 owner 说明。\n"",
   ""protocol/world_slots.json"": ""{\n  \""schema_version\"": \""1\"",\n  \""slots\"": {\n    \""state.mood\"": {\n      \""kind\"": \""wat\"",\n      \""owner\"": \""\""\n    },\n    \""state.count\"": {\n      \""kind\"": \""string\"",\n      \""owner\"": \""M00\"",\n      \""item_kind\"": \""string\""\n    },\n    \""state.ghost\"": {\n      \""kind\"": \""number\"",\n      \""owner\"": \""M00\""\n    }\n  }\n}\n""
  },
  ""name"": ""world_slots/bad-slots"",
  ""scanner"": ""world_slots""
 },
 {
  ""expected"": {
   ""issues"": [
    ""04_模块库/通用类/M00_数据结构.md 缺失""
   ],
   ""stats"": {
    ""arrays"": 0,
    ""slots"": 1
   }
  },
  ""files"": {
   ""README.md"": """",
   ""protocol/world_slots.json"": ""{\""schema_version\"": \""1\"", \""slots\"": {\""a\"": {\""kind\"": \""string\"", \""owner\"": \""M00\""}}}""
  },
  ""name"": ""world_slots/missing-m00"",
  ""scanner"": ""world_slots""
 },
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""docs"": 5,
    ""steps"": 3
   }
  },
  ""files"": {
   ""docs/agent/agent_组装指令包_v0.2.md"": ""跑 `nf stats` 看数字；再看 `docs/45_M2_回合级drill.md` 与 `python scripts/ai_domain_closure.py --list`。\n"",
   ""docs/44_M2_AI通道内容规范.md"": """",
   ""docs/45_M2_回合级drill.md"": ""# drill\n"",
   ""docs/45_M3_techdoc载荷提案.md"": """",
   ""docs/45_执行遥测规范.md"": """",
   ""scripts/ai_domain_closure.py"": ""# 占位\n"",
   ""scripts/nf.py"": ""sub = ap.add_subparsers()\np0 = sub.add_parser(\""stats\"")\np1 = sub.add_parser(\""doctor\"")\np2 = sub.add_parser(\""release\"")\n""
  },
  ""name"": ""instruction_step_audit/valid"",
  ""scanner"": ""instruction_step_audit""
 },
 {
  ""expected"": {
   ""issues"": [
    ""docs/45_M3_techdoc载荷提案.md: 引用未知子命令 nf 不存在"",
    ""docs/45_M3_techdoc载荷提案.md: 引用脚本不存在 scripts/不存在.py"",
    ""docs/45_M3_techdoc载荷提案.md: 引用路径不存在 docs/无此档.md""
   ],
   ""stats"": {
    ""docs"": 5,
    ""steps"": 6
   }
  },
  ""files"": {
   ""docs/agent/agent_组装指令包_v0.2.md"": ""跑 `nf stats` 看数字；再看 `docs/45_M2_回合级drill.md` 与 `python scripts/ai_domain_closure.py --list`。\n"",
   ""docs/44_M2_AI通道内容规范.md"": """",
   ""docs/45_M2_回合级drill.md"": ""# drill\n"",
   ""docs/45_M3_techdoc载荷提案.md"": ""跑 `nf 不存在` 与 `python scripts/不存在.py` 与 `docs/无此档.md` 都不该过。\n"",
   ""docs/45_执行遥测规范.md"": """",
   ""scripts/ai_domain_closure.py"": ""# 占位\n"",
   ""scripts/nf.py"": ""sub = ap.add_subparsers()\np0 = sub.add_parser(\""stats\"")\np1 = sub.add_parser(\""doctor\"")\np2 = sub.add_parser(\""release\"")\n""
  },
  ""name"": ""instruction_step_audit/bad"",
  ""scanner"": ""instruction_step_audit""
 },
 {
  ""expected"": {
   ""issues"": [
    ""docs/44_M2_AI通道内容规范.md 缺失（审计清单内档须在场）""
   ],
   ""stats"": {
    ""docs"": 5,
    ""steps"": 3
   }
  },
  ""files"": {
   ""docs/agent/agent_组装指令包_v0.2.md"": ""跑 `nf stats` 看数字；再看 `docs/45_M2_回合级drill.md` 与 `python scripts/ai_domain_closure.py --list`。\n"",
   ""docs/45_M2_回合级drill.md"": ""# drill\n"",
   ""docs/45_M3_techdoc载荷提案.md"": """",
   ""docs/45_执行遥测规范.md"": """",
   ""scripts/ai_domain_closure.py"": ""# 占位\n"",
   ""scripts/nf.py"": ""sub = ap.add_subparsers()\np0 = sub.add_parser(\""stats\"")\np1 = sub.add_parser(\""doctor\"")\np2 = sub.add_parser(\""release\"")\n""
  },
  ""name"": ""instruction_step_audit/missing-doc"",
  ""scanner"": ""instruction_step_audit""
 },
 {
  ""expected"": {
   ""issues"": [
    ""已登记事件无 machine 引用（死注册）：ev.three""
   ],
   ""stats"": {
    ""declared"": 2,
    ""pending"": 1,
    ""registered"": 3,
    ""used"": 2
   }
  },
  ""files"": {
   ""04_模块库/通用类/T01.md"": ""```yaml\nmachine_contract:\n  id: T01\n  events:\n    publish: [ev.one]\n    subscribe: [ev.two]\n```\n"",
   ""desktop/src/core/registry.json"": ""{\""subscriptions\"": {}}\n"",
   ""protocol/event_payload.schema.json"": ""{\""type\"": \""object\"", \""required\"": [\""events\""], \""properties\"": {\""events\"": {\""type\"": \""object\""}}}\n"",
   ""protocol/event_registry.json"": ""{\n  \""events\"": {\n    \""ev.one\"": {\n      \""fields\"": [\n        \""a\""\n      ]\n    },\n    \""ev.two\"": {\n      \""fields\"": [\n        \""b\""\n      ]\n    },\n    \""ev.three\"": {}\n  }\n}\n""
  },
  ""name"": ""payload_registry/valid"",
  ""scanner"": ""payload_registry""
 },
 {
  ""expected"": {
   ""issues"": [
    ""已登记事件无 machine 引用（死注册）：ev.dead"",
    ""机器事件未登记载荷（漏登）：ev.one, ev.two""
   ],
   ""stats"": {
    ""declared"": 1,
    ""pending"": 0,
    ""registered"": 1,
    ""used"": 2
   }
  },
  ""files"": {
   ""04_模块库/通用类/T01.md"": ""```yaml\nmachine_contract:\n  id: T01\n  events:\n    publish: [ev.one]\n    subscribe: [ev.two]\n```\n"",
   ""desktop/src/core/registry.json"": ""{\""subscriptions\"": {}}\n"",
   ""protocol/event_payload.schema.json"": ""{\""type\"": \""object\"", \""required\"": [\""events\""], \""properties\"": {\""events\"": {\""type\"": \""object\""}}}\n"",
   ""protocol/event_registry.json"": ""{\n  \""events\"": {\n    \""ev.dead\"": {\n      \""fields\"": [\n        \""a\""\n      ]\n    }\n  }\n}\n""
  },
  ""name"": ""payload_registry/dead+missing"",
  ""scanner"": ""payload_registry""
 },
 {
  ""expected"": {
   ""issues"": [],
   ""stats"": {
    ""consumer_map"": {
     ""ev.one"": [],
     ""ev.two"": [
      ""T01""
     ]
    },
    ""events_consumed"": 1,
    ""events_declared"": 2
   }
  },
  ""files"": {
   ""04_模块库/通用类/T01.md"": ""```yaml\nmachine_contract:\n  id: T01\n  events:\n    publish: [ev.one]\n    subscribe: [ev.two]\n```\n"",
   ""desktop/src/core/registry.json"": ""{\""subscriptions\"": {}}\n"",
   ""protocol/event_payload.schema.json"": ""{\""type\"": \""object\"", \""required\"": [\""events\""], \""properties\"": {\""events\"": {\""type\"": \""object\""}}}\n"",
   ""protocol/event_registry.json"": ""{\n  \""events\"": {\n    \""ev.one\"": {\n      \""fields\"": [\n        \""a\""\n      ]\n    },\n    \""ev.two\"": {\n      \""fields\"": [\n        \""b\""\n      ]\n    },\n    \""ev.plain\"": {}\n  }\n}\n""
  },
  ""name"": ""payload_consumer/valid"",
  ""scanner"": ""payload_consumer""
 }
]
";
}
