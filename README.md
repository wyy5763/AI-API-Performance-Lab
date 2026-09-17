# AI API Performance Lab

基于 JMeter 的 AI / SSE 流式接口性能测试与分析实验项目。

## 项目定位

面向 AI API、SSE/流式接口的性能测试、稳定性测试和结果分析。项目提供：

- 可直接运行的 Python Mock AI API
- JMeter 5.6.2 测试计划
- JSON 与 SSE 接口测试
- TTFT、流式 chunk、字符数、错误率、TPS、P50/P90/P95/P99 分析
- HTML 测试报告生成
- Windows / Linux 一键 Demo 脚本

## 目录

```text
AI-API-Performance-Lab/
├─ mock-server/              # 本地 AI API 模拟服务
├─ jmeter/                   # JMeter 测试计划与测试数据
├─ tools/                    # JTL 结果分析和 HTML 报告
├─ docs/                     # 测试方案、交付说明
├─ examples/                 # 示例结果
└─ scripts/                  # Demo 启停脚本
```

## 快速开始

### 1. 启动 Mock Server

```bash
python mock-server/app.py
```

健康检查：`http://127.0.0.1:8088/api/health`

### 2. JMeter 运行

需要 JMeter 5.6.2。

```bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -Jthreads=5 -JrampUp=5 -Jduration=30 -l result.jtl
```

### 3. 分析结果

```bash
python tools/analyze_result.py result.jtl
python tools/generate_report.py result.jtl report.html
```

## 核心指标

- Average / Min / Max
- P50 / P90 / P95 / P99
- Error Rate
- TPS
- Bytes Received
- SSE Chunk Count
- SSE Character Count
- Server TTFT

> examples 中的数据仅用于演示，不代表真实生产系统测试结果。

## 服务化方向

这个项目可以进一步包装成企业交付服务：AI API 压测、SSE 流式接口专项测试、模型网关性能对比、容量评估、稳定性测试和自动化性能报告。

## License

MIT
