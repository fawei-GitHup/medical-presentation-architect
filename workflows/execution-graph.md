# execution-graph

工作流按依赖图运行，并用 `stage` 为每个分支写入 `run/stages.json`、checkpoint 与产物哈希。状态更新采用跨进程文件锁和原子替换，多个已就绪分支不会互相覆盖。`resume` 重新核对哈希；缺失、变更或上游失效的产物标为 stale，只重跑受影响分支。

关键串行路径：intake → narrative/architecture → prototype → publication build → render → final QA → export。`revise → rebuild → rerender → targeted review` 也是因果闭环。

brief 完成后，source design audit、media/privacy 初筛、research/evidence、doctor/font 检查可并行。architecture 后，visual/assets、claims/source、notes、citation mapping 可并行。build 后，PPTX lint、source-map-check、结构型 perceptual-preflight、notes、privacy/rights 可并行。render 后，contact sheet、逐页视觉审核、页数/哈希和截图可读性可并行。最终 QA 是 join gate，任何失败只使自身及依赖分支失效。

`resume` 返回的 `ready` 数组表示依赖上可以同时开始的阶段，`resume_from` 只提供一个兼容旧宿主的顺序入口。依赖图不是自带的模型调度器：宿主明确支持并行 agent/任务时可同时派发 `ready`；宿主禁用或没有该能力时顺序执行，但仍分别写 checkpoint，不能声称已经并行。不同分支不得同时写同一个业务产物；共享账本需要先拆分为分支文件，再在 join 阶段合并。

长任务用 `scripts/capture_run.py --scrub-images --heartbeat 60` 包装。心跳只报告阶段、耗时、最新文件和重试次数；不得记录模型密钥，也不得通过恢复机制绕过宿主权限或人工/临床审核。
