# evidence-policy

每条医学 claim 必须有 source_ids、locator（页/表/段）、support_excerpt（短摘录或精确释义）、scope、reviewer、reviewed_at。verified 只能在实际读取支持内容且对应主张后设置。摘要只能支持摘要包含的结论，付费墙不是编造细节的理由。
sources.json 记录标题、作者/机构、年份、类型、URL/DOI/PMID、访问日期、撤稿/更正检查、验证状态、验证方法。检索日志保存检索式、数据库、筛选理由、截止日期和局限。联网失败不能改记为 verified。
优先与问题匹配的最新适用指南/系统综述/原始研究/官方说明；证据层级须与问题类型匹配。每次生成前核对更新、更正和撤稿。资源脚本只核对 PubMed 元数据与撤稿关联，不自动核实医学结论。
允许 local_document 无公开 URL，但须本地 SHA256、定位与访问限制；public 输出中不包含内部文档内容或原始路径。
