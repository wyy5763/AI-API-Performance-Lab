# Mock Server

纯 Python 标准库实现，不需要安装第三方依赖。

```bash
python app.py
```

默认监听 `127.0.0.1:8088`。

接口：
- `GET /api/health`
- `POST /api/chat`
- `POST /api/chat/stream`

## 故障注入

普通 JSON：

```
POST /api/chat?status=500
POST /api/chat?delay_ms=35000
```

SSE：

```
POST /api/chat/stream?status=503
POST /api/chat/stream?mode=empty
POST /api/chat/stream?mode=incomplete
POST /api/chat/stream?ttft_ms=1000
POST /api/chat/stream?interval_ms=500
```

参数说明：

| 参数 | 作用 |
|---|---|
| `status` | 返回指定 HTTP 状态码 |
| `delay_ms` | JSON 接口响应前等待时间 |
| `mode=empty` | SSE 返回 200，但不发送数据块 |
| `mode=incomplete` | SSE 发送数据但不发送 `[DONE]` |
| `ttft_ms` | SSE 首个数据块前等待时间 |
| `interval_ms` | SSE chunk 之间等待时间 |

这些参数主要用于验证性能测试工具的超时、HTTP 错误和 SSE 异常分类。
