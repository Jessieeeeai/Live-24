# 🎙️ 加密大漂亮 | Crypto Beauty Ultimate

24小时不间断的 AI 自动化播客/直播系统

## 🌟 核心特性

### 1. 主播人设
- **名称**：加密大漂亮
- **性格**：知性、犀利、专业、带点幽默
- **风格**：像真人聊天八卦，拒绝"播音腔"

### 2. 内容生产系统
- **智能搜索**：基于 Tavily API 的 24 小时实时新闻搜索
- **信息源控制**：支持指定可信媒体（CoinDesk, The Block 等）
- **深度分析框架**：
  - 5W1H（热点解读）
  - PEST（趋势分析）
  - SWOT（争议分析）
  - MECE（深度复盘）
- **AI 大脑**：DeepSeek 驱动的深度内容生成
- **去重机制**：5 小时内不重复讲解同一话题

### 3. 音视频呈现
- **语音合成**：EdgeTTS zh-CN-XiaoxiaoNeural（晓晓）
- **字幕同步**：基于真实音频时长的精确字幕匹配
- **硬字幕**：抖音/TikTok 风格，白字黑边，底部居中
- **背景视频**：循环播放自定义 MP4 背景

### 4. 运行模式
- **🛠️ 试听模式**：生成预览视频，网页播放
- **📡 直播模式**：24 小时无限循环，RTMP 推流到 YouTube

### 5. 防冷场策略
- **备用话题库**：可视化 CMS 管理
- **历史视频插播**：支持随机播放历史内容
- **智能调度**：可配置插播概率和轮播间隔

## 🚀 快速开始

### 前置要求
- Python 3.8+
- FFmpeg 已安装
- DeepSeek API Key
- Tavily API Key
- YouTube 推流码（直播模式）

### 安装步骤

1. **克隆项目**
```bash
cd /home/user/webapp
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **验证 FFmpeg**
```bash
ffmpeg -version
ffprobe -version
```

4. **启动应用**
```bash
streamlit run app.py
```

## 📋 使用说明

### 1. 配置密钥
在侧边栏输入：
- DeepSeek API Key
- Tavily API Key
- YouTube 推流码（直播模式必需）

### 2. 设置信息源
指定可信新闻网站（逗号分隔）：
```
coindesk.com, theblock.co, cointelegraph.com, decrypt.co
```

### 3. 上传背景视频
上传 MP4 格式的循环背景视频

### 4. 配置策略
- **监控关键词**：Bitcoin, Ethereum, Solana, AI Agent
- **轮播间隔**：60-300 秒（推荐 120 秒）
- **老视频概率**：0-100%（推荐 30%）

### 5. 管理备用话题
在"备用话题管理"标签页：
- 添加/编辑科普话题
- 用于无新闻时的填充内容

### 6. 启动系统
- **试听模式**：生成一条预览视频，测试效果
- **直播模式**：24小时无限循环推流

## 🔧 核心修复说明

### 问题 1：字幕语音不同步 ✅ 已修复
**原因**：之前使用固定语速（3.2字/秒）估算时长，实际 TTS 语速会变化

**解决方案**：
- 使用 `ffprobe` 获取音频真实时长
- 基于实际时长按字数比例分配字幕时间
- 每行字幕最短显示 1.5 秒（防止闪烁）

**关键代码**：
```python
# stream_engine.py
def get_audio_duration(audio_path):
    # 使用 ffprobe 获取真实时长
    
# app.py
audio_duration = get_audio_duration(audio_path)
generate_srt(script, audio_duration, srt_path)
```

### 问题 2：不能持续播放 ✅ 已修复
**原因**：
- 试听模式用 `break` 导致循环退出
- 直播模式在错误后没有恢复机制

**解决方案**：
```python
# 试听模式：播完一次就退出
if is_preview:
    # 执行预览
    break  # 正常退出

# 直播模式：永不退出的死循环
while True:
    try:
        # 执行播放
        if is_live:
            time.sleep(interval)
            continue  # 继续下一轮
    except Exception as e:
        # 错误恢复
        time.sleep(10)
        continue  # 重试
```

## 📁 项目结构

```
webapp/
├── app.py              # Streamlit 主界面
├── logic_core.py       # AI 内容生成核心
├── stream_engine.py    # 音视频处理引擎
├── requirements.txt    # Python 依赖
├── README.md          # 项目文档
├── assets/            # 资源文件
│   └── background.mp4 # 背景视频
├── temp/              # 临时文件
│   ├── s_*.mp3       # 生成的语音
│   ├── s_*.srt       # 生成的字幕
│   └── p_*.mp4       # 预览视频
├── archive_videos/    # 历史视频库
└── knowledge_db.json  # 备用话题数据库
```

## 🎯 核心功能详解

### 字幕生成算法
```python
def generate_srt(text, audio_duration, output_path):
    # 1. 计算实际语速
    actual_speed = total_chars / audio_duration
    
    # 2. 按标点和长度切分
    segments = split_by_punctuation_and_length(text, max_len=12)
    
    # 3. 按字数比例分配时间
    for seg in segments:
        duration = audio_duration * (len(seg) / total_chars)
        duration = max(1.5, duration)  # 最短 1.5 秒
```

### 去重机制
```python
def _check_duplication(new_topic):
    # 1. 加载 5 小时内的历史记录
    # 2. 关键词匹配 + 相似度检测（50% 阈值）
    # 3. 自动清理过期记录
```

### 文案清洗
```python
def _clean_text(text):
    # 去除：(音效)、[动作]、【背景】
    # 去除：Markdown 格式符号
    # 去除：AI 废话（"综上所述"等）
    # 规范：标点符号合并
    # 移除：不适合朗读的符号
```

## ⚙️ 高级配置

### 字幕样式调整
在 `stream_engine.py` 中修改：
```python
style = "Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40"

# 参数说明：
# Fontsize=18        : 字号
# MarginV=40         : 底部边距
# Outline=2          : 描边宽度
# PrimaryColour      : 字体颜色（白色）
# OutlineColour      : 描边颜色（黑色）
```

### DeepSeek 参数调整
在 `logic_core.py` 中修改：
```python
self.llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=1.3,  # 创造性（0.0-2.0）
    timeout=60        # 超时时间
)
```

### Tavily 搜索配置
```python
response = self.tavily.search(
    search_depth="advanced",  # basic | advanced
    max_results=10,           # 结果数量
    days=1                    # 时间范围
)
```

## 🐛 故障排查

### FFmpeg 相关错误
```bash
# 检查 FFmpeg 是否安装
which ffmpeg
which ffprobe

# 测试字幕烧录
ffmpeg -i test.mp4 -vf "subtitles=test.srt" output.mp4
```

### 字幕不显示
1. 检查 SRT 文件是否生成
2. 查看字幕文件编码（必须 UTF-8）
3. 验证时间码格式（00:00:00,000）

### 推流失败
1. 验证推流码正确性
2. 检查网络连接
3. 确认 YouTube 直播已开启
4. 查看 FFmpeg 错误日志

### API 调用失败
1. 检查密钥是否正确
2. 验证 API 额度是否充足
3. 查看网络代理设置

## 📊 性能优化

### 处理速度
- **TTS 生成**：约 5-10 秒
- **字幕生成**：< 1 秒
- **视频合成**：10-30 秒（取决于音频长度）
- **推流延迟**：实时（-re 参数）

### 资源占用
- **内存**：约 500MB-1GB
- **CPU**：视频编码时较高
- **磁盘**：临时文件自动清理

## 🔐 安全建议

1. **密钥管理**：不要将 API Key 提交到代码仓库
2. **访问控制**：Streamlit 默认本地访问（127.0.0.1）
3. **推流码保护**：使用环境变量或密钥管理服务

## 📝 更新日志

### v2.0 (2024-11-23)
- ✅ 修复字幕语音不同步问题
- ✅ 实现真正的 24 小时无限循环
- ✅ 优化字幕生成算法（基于真实音频时长）
- ✅ 增强去重机制（关键词 + 相似度）
- ✅ 完善错误处理和恢复机制
- ✅ 添加运行统计和状态监控

### v1.0 (初始版本)
- 基础功能实现

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- **EdgeTTS**：微软语音合成
- **DeepSeek**：AI 内容生成
- **Tavily**：智能搜索
- **FFmpeg**：音视频处理
- **Streamlit**：Web 界面

---

**Built with ❤️ for Crypto Community**
