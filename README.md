# flask go2rtc 最小项目模板

## 项目介绍
本项目利用 [go2rtc](www.go2rtc.org) 将摄像机的 RTSP 流转换为 WebRTC 格式，解决 RTSP 流在网页中的播放问题。

## 项目结构

```
miniapp/
├── app.py                  # Flask 主程序
├── templates/
│   └── index.html          # 前端页面（WebRTC 播放器）
├── pyproject.toml          # PDM 项目配置和依赖管理
├── Dockerfile              # Flask 应用镜像构建文件
├── docker-compose.yml      # Docker Compose 编排文件（含 go2rtc + flask）
├── go2rtc.yaml             # go2rtc 配置文件
└── README.md               # 项目文档
```

---

## 关键代码说明

### 后端程序(app.py)

#### 1. 应用配置
```python
app = Flask(__name__)

# 配置
GO2RTC_API_URL = "http://127.0.0.1:1984"  # go2rtc 服务地址
STREAM_ID = "device_1"                     # 流标识符，对应 go2rtc.yaml 中配置的流名称
```

#### 2. WebRTC 代理端点

`webrtc_proxy()` 端点利用 WHEP 协议简化了信令交换过程，实现客户端拉流。

```python
# 1. 接收客户端发送的 Offer SDP
offer_sdp = request.get_data()

# 2. 转发 Offer SDP 给 go2rtc 服务
response = requests.post(
    whep_url,
    data=offer_sdp,
    headers={"Content-Type": "application/sdp"},
    timeout=30
)

# 3. 将 go2rtc 返回的 Answer SDP 回传给客户端
return response
```

**WHEP 协议 （WebRTC-HTTP Egress Protocol）** 是通过 HTTP 传输 WebRTC 流的标准协议，允许浏览器从服务器拉取视频流。

go2rtc 的 [WHEP 接口文档](https://go2rtc.org/api/#tag/Consume-stream/paths/~1api~1webrtc?src=%7Bsrc%7D/post)


---

### 前端页面(templates/index.html)

页面实现 WebRTC 基础配置，并利用后端的 WHEP 端点实现 SDP 交换
```javascript
const response = await fetch('/api/webrtc/whep', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/sdp'
    },
    body: peerConnection.localDescription.sdp
});

```

## go2rtc 配置文件操作接口
go2rtc 默认运行在 1984 端口
```
http://localhost:1984
```

可以通过 http://localhost:1984/api/streams 修改配置文件



### 增加/更新流
路径：/api/streams

方法：PUT

请求参数：

|参数名|描述|类型|示例|
|---|---|---|---|
|name|名称|string|src=rtsp://rtsp:12345678@192.168.1.123/av_stream/ch0
|src|流路径|string|name=camera1|

[Create new stream - API](https://go2rtc.org/api/#tag/Streams-list/paths/~1api~1streams/put)

### 移除流
路径：/api/streams

方法：DELETE

请求参数：

|参数名|描述|类型|示例|
|---|---|---|---|
|src|名称|string|src=camera1|

[Delete stream - API](https://go2rtc.org/api/#tag/Streams-list/paths/~1api~1streams/delete)

更多接口参考[go2rtc接口文档](https://go2rtc.org/api)

> [!NOTE] 注意
> 接口使用查询参数操作，不支持JSON请求体
> 更新流示例：curl -X PUT "<http://localhost:1984/api/streams?src=rtsp://192.168.0.180/ch1&name=device_1>"

---

## 工作流程图

```mermaid
sequenceDiagram
    participant Browser as 浏览器
    participant Flask as Flask 后端
    participant Go2rtc as go2rtc

    Note over Browser: 1. 创建 RTCPeerConnection<br/>2. 生成 SDP Offer<br/>3. 收集 ICE 候选

    Browser->>Flask: POST /api/webrtc<br/>(携带 SDP Offer)
    Flask->>Go2rtc: POST /api/webrtc?src=xxx<br/>(转发 SDP Offer)
    Go2rtc-->>Flask: SDP Answer
    Flask-->>Browser: 返回 SDP Answer

    Note over Browser: 4. 设置 Remote Description<br/>5. 建立 WebRTC 连接<br/>6. 接收视频流并播放

```
## 本地运行模式

### go2rtc 配置

1. 下安装[go2rtc可执行文件](https://github.com/AlexxIT/go2rtc/releases/)

2. 配置go2rtc.yaml
```yaml
streams:
  device_1: rtsp://192.168.0.180/ch2
```
3. 启动go2rtc

### flask 配置

1. 安装依赖
```bash
pdm install
```

2. 启动服务
```bash
pdm run app.py
```



## Docker Compose 部署（推荐）

本项目支持通过 Docker Compose 一键部署 Flask 应用 和 go2rtc，适用于局域网环境。

### 1. 修改配置文件

部署前，请根据实际环境修改以下配置：

#### go2rtc.yaml
```yaml
streams:
  device_1: rtsp://192.168.0.180/ch2   # 修改为你的摄像头 RTSP 地址

webrtc:
  listen: ":8555"
  candidates:
    - 192.168.0.19:8555               # 修改为宿主机的局域网 IP
```

### 2. 构建并启动服务

```bash
cd miniapp
docker-compose up -d --build
```

这将同时启动两个服务：
- **go2rtc**：负责 RTSP 转 WebRTC，管理在 http://宿主机IP:1984
- **flask**：Web 应用服务，访问 http://宿主机IP:80

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止服务

```bash
docker-compose down
```

---

## 仅部署 Flask 应用

1. 构建Docker镜像

```bash
cd miniapp
docker build -t miniapp .
```

2. 运行容器

```bash
docker run -d -p 80:80 --name flask_go2rtc miniapp
```

3. 访问容器

```
http://localhost:80
```

停止容器

```bash
docker stop flask_go2rtc
```

移除容器

```bash
docker rm flask_go2rtc
```

