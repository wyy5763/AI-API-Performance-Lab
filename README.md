# AI API Performance Lab

基于 JMeter 的 AI API / SSE 流式接口性能测试与分析示例。

## 项目能力

- 本地 Mock AI API，可模拟普通 JSON 和 SSE 流式接口
- JMeter 5.6.2 压测
- JSON API + SSE API 双场景
- 参数化并发数、Ramp-up、循环次数、Host、Port、超时
- SSE TTFT（压测客户端观测到第一个 `data:` 事件的时间）
- SSE Chunk 数量、输出字符数、完成率
- AI API 异常分类：连接超时、响应超时、连接拒绝、DNS、HTTP 4xx/5xx、SSE 未首块、SSE 中断、SSE 未完成
- JTL 结果统计：TPS、错误率、Average、P50、P90、P95、P99
- JSON / SSE 场景独立统计
- 单次 HTML 性能报告
- **5 / 10 / 20 / 50 / 100 并发阶梯测试**
- **阶梯测试自动生成 CSV + HTML 汇总报告**
- Windows / Linux Demo 脚本

## 快速运行

### 1. 启动 Mock Server

```bash
python mock-server/app.py
```

健康检查：`http://127.0.0.1:8088/api/health`

### 2. 单场景 / 双场景 JMeter 测试

需要 JMeter 5.6.2，并将 `jmeter/bin` 加入 PATH。

```bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -q jmeter/user.properties -l result.jtl
```

默认参数：

```
threads=5
rampUp=5
loops=10
host=127.0.0.1
port=8088
connectTimeoutMs=10000
readTimeoutMs=30000
```

也可以覆盖参数：

```bash
jmeter -n -t jmeter/ai_sse_performance_test.jmx -Jthreads=20 -JrampUp=10 -Jloops=50 -Jhost=127.0.0.1 -Jport=8088 -l result.jtl
```

一次循环包含：

```
JSON POST Request
        ↓
SSE POST Request
```

因此如果 `threads=5`、`loops=10`，理论上会产生约 100 个业务 Sample（JSON 50 + SSE 50）。

### 3. SSE 专项指标

SSE 场景会记录：

- **TTFT**：从压测客户端开始请求到读取第一个 SSE `data:` 事件的时间
- **Chunk Count**：收到的流式数据块数量
- **Output Characters**：解析到的 `delta` 字符数
- **Done**：是否收到 `[DONE]`

> TTFT 是客户端观测指标，不等同于模型服务端内部的首 token 时间。

### 4. 结果分析

```bash
python tools/analyze_result.py result.jtl
python tools/generate_report.py result.jtl report.html
```

分析结果会分别展示：

- JSON POST Request
- SSE POST Request
- SSE TTFT Average / P50 / P95 / P99
- Average Chunk Count
- Average Output Characters
- SSE Done Rate
- Overall TPS / P95 / P99 / Error Rate

### 5. 自动并发阶梯测试

Windows：

```bat
scripts\run_ladder.bat
```

默认执行：

```
5 → 10 → 20 → 50 → 100
```

也可以只跑指定并发：

```bat
scripts\run_ladder.bat 10 20 50
```

Linux / macOS：

```bash
chmod +x scripts/run_ladder.sh
./scripts/run_ladder.sh
```

执行完成后：

```
results/
└── ladder/
    ├── result_5.jtl
    ├── result_10.jtl
    ├── result_20.jtl
    ├── result_50.jtl
    ├── result_100.jtl
    ├── performance-summary.csv
    └── performance-summary.html
```

也可以直接分析已有 JTL：

```bash
python tools/aggregate_ladder.py results/ladder
```

### 异常分类快速验证

Mock Server 支持故障注入，可以直接验证异常分类：

```bat
:: JSON 500
jmeter -n -t jmeter\ai_sse_performance_test.jmx -q jmeter\user.properties -JjsonPath=/api/chat?status=500 -Jloops=1 -Jthreads=1 -l error-500.jtl

:: JSON 读取超时（默认 readTimeout=30000ms）
jmeter -n -t jmeter\ai_sse_performance_test.jmx -q jmeter\user.properties -JjsonPath=/api/chat?delay_ms=35000 -Jloops=1 -Jthreads=1 -l error-timeout.jtl

:: SSE 没有第一个数据块
jmeter -n -t jmeter\ai_sse_performance_test.jmx -q jmeter\user.properties -JssePath=/api/chat/stream?mode=empty -Jloops=1 -Jthreads=1 -l error-sse-empty.jtl

:: SSE 中途没有 [DONE]
jmeter -n -t jmeter\ai_sse_performance_test.jmx -q jmeter\user.properties -JssePath=/api/chat/stream?mode=incomplete -Jloops=1 -Jthreads=1 -l error-sse-incomplete.jtl
```

然后：

```bash
python tools/analyze_result.py error-500.jtl
python tools/generate_report.py error-500.jtl error-500.html
```

Mock Server 支持的故障参数：

- `status=500`：模拟 HTTP 5xx
- `delay_ms=35000`：模拟响应读取超时
- `mode=empty`：SSE 无首块
- `mode=incomplete`：SSE 有输出但不发送 `[DONE]`
- `ttft_ms=...`：控制 SSE 首块延迟
- `interval_ms=...`：控制 SSE chunk 间隔

## 异常分类体系

测试结果中的失败不再只显示为“Error”，而是记录 `error_type`：

| error_type | 含义 |
|---|---|
| `CONNECT_TIMEOUT` | 建立连接阶段超时 |
| `READ_TIMEOUT` | 已建立连接，但读取响应超时 |
| `CONNECTION_REFUSED` | 目标端口拒绝连接 |
| `DNS_ERROR` | 域名解析失败 |
| `NETWORK_ERROR` | 其他网络异常 |
| `HTTP_4XX` | 服务端返回 4xx |
| `HTTP_5XX` | 服务端返回 5xx |
| `SSE_NO_FIRST_CHUNK` | SSE 返回成功，但没有收到第一个数据块 |
| `SSE_INCOMPLETE` | SSE 收到数据，但没有收到 `[DONE]` |
| `SSE_READ_TIMEOUT` | SSE 已开始读取，但后续读取发生超时 |\n| `SSE_INTERRUPTED` | SSE 已开始输出，中途发生其他网络/读取异常 |

JMeter sampler 使用 `598` 表示 SSE 流协议异常、`599` 表示客户端网络/超时异常；真实 HTTP 4xx/5xx 状态码仍保留。这样可以在性能测试中区分“服务端业务错误”和“客户端网络/超时问题”。

## 当前指标体系

### 普通 JSON API

```
Response Time
Average
P50 / P90 / P95 / P99
TPS
Error Rate
```

### SSE 流式 API

```
Full Response Time
TTFT
P50 / P95 / P99
TPS
Error Rate
Chunk Count
Output Characters
Done Rate
```

### 并发阶梯

```
5
10
20
50
100
```

通过阶梯结果可以观察并发增加后 TPS、P95、P99 和错误率的变化。

> 当前版本不会自动判断“是否达标”。容量结论应根据实际业务 SLA、目标 TPS、延迟上限和错误率要求进行判断。

## 下一阶段

后续继续加入：

1. AI API 超时分类
2. 性能回归对比
3. 稳定性 / 长时间运行测试
4. 模型 / 网关多目标对比
5. 面向客户的完整测试报告
6. 测试任务配置化与一键执行

## 服务化方向

这个项目可以进一步包装为企业 AI API 性能专项服务，包括：

- AI 网关压测
- SSE 流式接口专项测试
- TTFT / 输出速度分析
- 容量评估
- 稳定性测试
- 模型接口对比
- 自动化测试报告

> `examples/` 中的数据仅用于演示，不代表真实生产测试结果。

## License

MIT
