# 项目 Token 用量记录（v05）

仅在用户需要统计用量时读取。工具记录**指定来源、指定观测区间的已记录 Token**；不能从 `.blend`、精简对话、渲染时长或订阅额度反推历史消费。过去三个作品没有原始 usage 记录时，历史用量保持未知。

## 支持范围

- 一个项目、一个明确指定的本地 Codex JSONL、一个账本。支持带 `session_meta` 的 rollout 累计快照，以及带 `thread.started` 的 `codex exec --json` 逐轮用量，自动识别。
- 只读取指定文件，不搜索所有私人会话，不发模型请求，不需要 API key。解析期间不把对话原文保存到统计结果。
- 开始时取最新已记录位置为基线；**不导入开始前的历史**，也不自动合并其它线程、子代理、fork 或另一种采集来源。
- 同会话涉及多个作品的用量不能客观拆分。优先使用专用会话；同一区间只保留一个权威账本，不把复制的账本或同一会话的不同路径相加。本版没有跨账本注册服务，也不声称能识别所有外部重复账本。
- 所有计数均称“已观测”，包括当前项目内已记录的诊断、审核与返工；不是“仅建模净用量”，也不是费用。

## 使用

路径由当前环境和用户指定来源确定。以下仅为示例；不要扫描私人目录来自动寻找历史。

```text
python scripts/token_usage.py begin --project-id green-desk-lamp --source /absolute/path/session.jsonl --ledger /absolute/path/project/token-ledger.json
python scripts/token_usage.py update --ledger /absolute/path/project/token-ledger.json
python scripts/token_usage.py end --ledger /absolute/path/project/token-ledger.json
python scripts/token_usage.py update --ledger /absolute/path/project/token-ledger.json
python scripts/token_usage.py report --ledger /absolute/path/project/token-ledger.json --output /absolute/path/project/token-summary-v001.json
```

`begin` 不覆盖已有账本。重复执行 `update` 不重复入账。`report` 读取账本缓存，不读取或刷新源日志；需要最新已落盘记录时先执行 `update`。各命令都输出 JSON，`--output` 可另存净化摘要到**尚不存在的文件**；给新摘要使用新版本名。

为减少统计本身增加的模型用量，刷新由本地程序按里程碑执行，不循环询问模型。执行 `begin` 时已有在途请求，它的输入或输出可能跨越基线；本版不会把墙钟差分称为完整轮次或精确项目用量。

## 结束与待结算

`end` 的含义是请求停止采集，不保证当前回复已经结算：

| 状态 | 含义 |
|---|---|
| `observed_pending` | 观测中；当前回复及尚未落盘的最终用量可能未包含 |
| `close_requested_pending` | 已绑定当前轮次，等后续 `update` 补读结束边界 |
| `closed_observed` | 观察到绑定轮次结束，或在已有可信轮次边界处停止；不是“全项目精确结算完成” |
| `closed_partial` | 缺可信生命周期、结束前另起新轮、或绑定轮次中断；已停止，缺失用量未知 |

rollout 根据 `task_started.turn_id` 绑定结束范围，最多补到同轮 `task_complete`；到达边界后停止导入。若先出现其它 `task_started`，保留已记录量并关闭为 partial，不把下一轮计入旧项目。`task_aborted`／exec 的 `turn.failed` 也关闭为 partial，不把缺失用量记作零。

观测区间内已有中断／失败，或出现空的 usage 信息时，即使这些事件在 `end` 之前已经读取，收尾仍保留 partial。后续累计数可以补充已记录量，但本版不据此认定缺失事件全部得到覆盖。

没有生命周期的来源，`end` 在当前位置停止并标 partial，不无限追读未来对话。已关闭账本的 `update` 只校验已记录前缀，不纳入后续记录。关闭前保持来源专用于这个项目；不要依赖此工具拆分同一轮的多项目工作。模型本轮最后一次读取之后产生的说明文字仍可能未出现在报告中。

## 报告与边界

`usage` 包含 `input_tokens`、`cached_input_tokens`、`output_tokens`、`reasoning_output_tokens`、`total_tokens`。总量为输入加输出；缓存是输入子项，推理是输出子项，不再次相加。缺少的明细为 `null`。exec 日志没有 usage 时间戳时 `observed_through` 为 `null`；`read_at` 只是读取时间。

`coverage` 说明只覆盖一条来源及基线后的用量事件数，项目归属未被证明，子代理未纳入。即使状态为 `closed_observed`，覆盖性质仍是 `observed_interval`。建议用户文案：**“已记录 12,300 Token；截至来源给出的时间；当前轮待补记。仅覆盖本会话的观测区间。”** 未知时间应写“来源未提供”，不要用文件修改时间替代。

内部账本保存源路径、会话 ID、已读取字节游标、完整前缀 SHA-256、基线和累计计数，仅用于本地续读。统计摘要省略路径和原文；公开到 GitHub 前仍检查项目名、会话标识等必要元数据是否适合公开，**不上传原始 JSONL 或内部账本**。它与用户维护的 GitHub 精简对话资料独立。

更新发现累计回退、完整行损坏、前缀替换、截断、来源身份变化或必要字段缺失时，报错并保持旧账本；不自动把回退解释为新计数段。开始前的历史回退不追算，开始后的回退需要重新核实来源范围，不能把两个未经校准的账本相加。没有换行符的最后一条记录可能尚未写完，留到下一次读取。

当前适配使用真实来源的字段，不保证所有 Codex 版本、服务商或自定义日志都兼容。出现不支持的结构应报告不可读取，不猜测字段。相关来源：[Codex 非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)、[Codex App Server](https://learn.chatgpt.com/docs/app-server)。
