#!/bin/bash

# 加密大漂亮启动脚本

echo "🎙️ 加密大漂亮 | Crypto Beauty Ultimate"
echo "======================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python 3"
    echo "请安装 Python 3.8 或更高版本"
    exit 1
fi

echo "✅ Python 版本："
python3 --version
echo ""

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ 错误：未找到 FFmpeg"
    echo "请先安装 FFmpeg："
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: 从 https://ffmpeg.org 下载"
    exit 1
fi

echo "✅ FFmpeg 版本："
ffmpeg -version | head -n 1
echo ""

# 检查 FFprobe
if ! command -v ffprobe &> /dev/null; then
    echo "❌ 错误：未找到 FFprobe（FFmpeg 组件）"
    exit 1
fi

echo "✅ FFprobe 已安装"
echo ""

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误：未找到 requirements.txt"
    exit 1
fi

echo "📦 检查 Python 依赖..."
pip3 list | grep -E "streamlit|edge-tts|langchain|tavily" > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  检测到缺失依赖，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

echo "✅ 所有依赖已就绪"
echo ""

# 创建必要目录
mkdir -p assets temp archive_videos
echo "✅ 目录结构已创建"
echo ""

# 启动应用
echo "🚀 启动 Streamlit 应用..."
echo "======================================"
echo ""
echo "📍 访问地址："
echo "   本地: http://localhost:8501"
echo "   网络: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "💡 提示："
echo "   - 按 Ctrl+C 停止服务"
echo "   - 首次使用请配置 API Keys"
echo ""

streamlit run app.py --server.port=8501 --server.address=0.0.0.0
