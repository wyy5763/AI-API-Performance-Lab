# AI API Performance Lab

基于 JMeter 的 AI API / SSE 流式接口性能测试与分析示例。

## 项目能力

- 本地 Mock AI API，可模拟普通 JSON 和 SSE 流式接口
- JMeter 5.6.2 压测
- 参数化并发数、Ramp-up、循环次数、Host、Port
- SSE chunk / 字符数 / 完成状态解析
- JTL 结果统计：TPS、错误率、Average、P50、P90、P95、P99
- HTML 性能报告
- Windows / Linux Demo 脚本

## 快速运行

### 1. 启动 Mock Server

```bash
python mock-server/app.py
```

健康检查：`http://127.0.0.1:8088/api/health`

### 2. 使用 JMeter

需要 JMeter 5.6.2，并将 `jmeter/bin` 加入 PATH。

```bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -q jmeter/user.properties -l result.jtl
```

也可以覆盖参数：

```bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -Jthreads=20 -JrampUp=10 -Jloops=50 -Jhost=127.0.0.1 -Jport=8088 -l result.jtl
```

### 3. 分析结果

```bash
python tools/analyze_result.py result.jtl
python tools/generate_report.py result.jtl report.html
```

## 服务化方向

这个项目可以进一步包装为企业 AI API 性能专项服务，包括 AI 网关压测、SSE 流式接口专项测试、容量评估、稳定性测试、模型接口对比和自动化报告。

> `examples/` 中的数据仅用于演示，不代表真实生产测试结果。

## License

MIT
