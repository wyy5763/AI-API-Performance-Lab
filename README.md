# AI API Performance Lab

基于 JMeter 的 AI API / SSE 流式接口性能测试与分析示例。

## 项目能力

- 本地 Mock AI API，可模拟普通 JSON 和 SSE 流式接口
- JMeter 5.6.2 压测
- 参数化并发数、Ramp-up、循环次数、Host、Port
- SSE chunk / 字符数 / 完成状态解析
- JTL 结果统计：TPS、错误率、Average、P50、P90、P95、P99
- 单次 HTML 性能报告
- **5 / 10 / 20 / 50 / 100 并发阶梯测试**
- **阶梯测试自动生成 CSV + HTML 汇总报告**
- Windows / Linux Demo 脚本

## 快速运行

### 1. 启动 Mock Server

\`\`\`bash
python mock-server/app.py
\`\`\`

健康检查：\`http://127.0.0.1:8088/api/health\`

### 2. 单场景 JMeter 测试

需要 JMeter 5.6.2，并将 \`jmeter/bin\` 加入 PATH。

\`\`\`bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -q jmeter/user.properties -l result.jtl
\`\`\`

也可以覆盖参数：

\`\`\`bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -Jthreads=20 -JrampUp=10 -Jloops=50 -Jhost=127.0.0.1 -Jport=8088 -l result.jtl
\`\`\`

### 3. 自动并发阶梯测试

Windows：

\`\`\`bat
scripts\run_ladder.bat
\`\`\`

默认执行：

\`\`\`
5 → 10 → 20 → 50 → 100
\`\`\`

也可以只跑指定并发：

\`\`\`bat
scripts\run_ladder.bat 10 20 50
\`\`\`

Linux / macOS：

\`\`\`bash
chmod +x scripts/run_ladder.sh
./scripts/run_ladder.sh
\`\`\`

执行完成后：

\`\`\`
results/
└── ladder/
    ├── result_5.jtl
    ├── result_10.jtl
    ├── result_20.jtl
    ├── result_50.jtl
    ├── result_100.jtl
    ├── performance-summary.csv
    └── performance-summary.html
\`\`\`

也可以直接分析已有 JTL：

\`\`\`bash
python tools/aggregate_ladder.py results/ladder
\`\`\`

### 4. 单次结果分析

\`\`\`bash
python tools/analyze_result.py result.jtl
python tools/generate_report.py result.jtl report.html
\`\`\`

## 当前指标

阶梯报告会按并发等级统计：

- Samples
- TPS
- Average
- P50 / P90 / P95 / P99
- Min / Max
- Error Rate
- 测试持续时间

报告同时提供 TPS / P95 趋势图，用于观察并发增加后的吞吐量与尾延迟变化。

> 当前版本不会自动判断“是否达标”。容量结论应根据实际业务 SLA、目标 TPS、延迟上限和错误率要求进行判断。

## 下一阶段

后续将继续加入：

1. JSON API + SSE API 双场景
2. 更准确的 SSE TTFT 测量
3. Stream Chunk 数量与输出字符数独立指标
4. AI API 超时分类
5. 性能回归对比
6. 面向客户的完整测试报告

## 服务化方向

这个项目可以进一步包装为企业 AI API 性能专项服务，包括 AI 网关压测、SSE 流式接口专项测试、容量评估、稳定性测试、模型接口对比和自动化报告。

> \`examples/\` 中的数据仅用于演示，不代表真实生产测试结果。

## License

MIT
