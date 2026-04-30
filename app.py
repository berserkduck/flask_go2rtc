import os
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# 配置
GO2RTC_API_URL = os.environ.get("GO2RTC_API_URL", "http://127.0.0.1:1984")
STREAM_ID = "device_1"


@app.route("/")
def index():
    return render_template("index.html", stream_id=STREAM_ID)


@app.route("/api/webrtc/whep", methods=["POST"])
def webrtc_proxy():
    """
    WHEP 协议代理端点
    用于信令交换和从go2rtc拉取视频流到客户端
    """
    whep_url = f"{GO2RTC_API_URL}/api/webrtc?src={STREAM_ID}"
    offer_sdp = request.get_data(as_text=True)

    if not offer_sdp:
        return "缺少 Offer SDP", 400

    response = requests.post(
        whep_url,
        data=offer_sdp,
        headers={"Content-Type": "application/sdp"},
        timeout=30
    )

    if response.status_code in (200, 201):
        return response.text, 200, {"Content-Type": "application/sdp"}
    else:
        return f"go2rtc 错误: {response.status_code}", response.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
