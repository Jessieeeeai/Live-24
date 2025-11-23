# 📑 加密大漂亮 - 文档索引

欢迎使用 **加密大漂亮 (Crypto Beauty Ultimate)** 2.0！

## 🚀 快速导航

### 初次使用？从这里开始 👇

1. **[QUICKSTART.md](QUICKSTART.md)** - 5 分钟快速上手
   - ⏱️ 阅读时间：5 分钟
   - 📋 内容：环境检查、API 配置、启动步骤
   - 👤 适合：新用户、快速部署

2. **运行测试脚本**
   ```bash
   python3 test_functionality.py
   ```
   - 验证所有依赖和工具是否正常

3. **启动应用**
   ```bash
   ./start.sh
   ```
   - 一键启动，自动检查环境

---

## 📚 完整文档

### 核心文档

#### [README.md](README.md) - 完整项目文档
- ⏱️ 阅读时间：15 分钟
- 📋 内容：
  - ✅ 项目定位与特性
  - ✅ 详细安装说明
  - ✅ 功能使用教程
  - ✅ API 配置说明
  - ✅ 故障排查指南
  - ✅ 高级配置
- 👤 适合：深入了解系统

#### [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目交付总结
- ⏱️ 阅读时间：10 分钟
- 📋 内容：
  - ✅ 问题解决详情
  - ✅ 交付文件清单
  - ✅ 核心功能特性
  - ✅ 技术架构说明
  - ✅ 性能指标
  - ✅ 使用建议
- 👤 适合：项目管理者、技术评审

#### [CHANGELOG.md](CHANGELOG.md) - 版本更新日志
- ⏱️ 阅读时间：8 分钟
- 📋 内容：
  - ✅ 2.0 版本重大修复
  - ✅ 新增功能列表
  - ✅ 优化改进详情
  - ✅ Bug 修复记录
  - ✅ 下一步计划
- 👤 适合：了解版本变化、升级参考

---

## 💻 代码文件

### 核心代码（必读）

#### [app.py](app.py) - Streamlit 主应用
- 📝 代码行数：~350 行
- 🎯 核心功能：
  - Streamlit UI 界面
  - 字幕生成算法（核心修复）
  - 主循环逻辑（无限循环）
  - 状态监控和日志
- 🔑 关键函数：
  - `generate_srt()` - 字幕生成（基于真实时长）
  - 主循环 - 试听/直播模式控制

#### [logic_core.py](logic_core.py) - AI 内容生成核心
- 📝 代码行数：~200 行
- 🎯 核心功能：
  - DeepSeek API 调用
  - Tavily 新闻搜索
  - 4 种分析框架（5W1H、PEST、SWOT、MECE）
  - 去重机制（5 小时窗口）
  - 文本清洗（去 AI 味）
- 🔑 关键函数：
  - `fetch_news_and_analyze()` - 主流程
  - `_check_duplication()` - 去重检测
  - `_clean_text()` - 文本清洗

#### [stream_engine.py](stream_engine.py) - 音视频引擎
- 📝 代码行数：~130 行
- 🎯 核心功能：
  - EdgeTTS 语音合成
  - FFprobe 音频时长检测（核心修复）
  - FFmpeg 视频合成
  - RTMP 推流
- 🔑 关键函数：
  - `text_to_speech()` - TTS 生成
  - `get_audio_duration()` - 时长检测（新增）
  - `create_preview_video()` - 预览视频
  - `start_stream()` - RTMP 推流

---

## 🛠️ 工具脚本

### [start.sh](start.sh) - 启动脚本
```bash
./start.sh
```
- 自动检查 Python、FFmpeg
- 安装缺失依赖
- 创建必要目录
- 启动 Streamlit 应用

### [test_functionality.py](test_functionality.py) - 测试脚本
```bash
python3 test_functionality.py
```
- 7 项自动化测试
- 验证所有依赖
- 测试核心功能
- 生成测试报告

---

## ⚙️ 配置文件

### [requirements.txt](requirements.txt) - Python 依赖
```bash
pip install -r requirements.txt
```
- streamlit
- edge-tts
- langchain-openai
- tavily-python
- python-dotenv

### [.env.example](.env.example) - 环境变量示例
```bash
cp .env.example .env
# 编辑 .env 填入真实密钥
```

### [.gitignore](.gitignore) - Git 忽略规则
- 临时文件
- 密钥配置
- 生成内容

---

## 📊 项目统计

```
文件总数：12 个
代码行数：1,007 行 (Python)
文档行数：1,195 行 (Markdown)
项目大小：220 KB
```

**代码质量**：
- ✅ 模块化设计
- ✅ 详细注释
- ✅ 错误处理
- ✅ 类型提示

**文档质量**：
- ✅ 完整覆盖
- ✅ 示例丰富
- ✅ 易于理解
- ✅ 持续更新

---

## 🎯 使用场景

### 场景 1：快速测试（5 分钟）
```
QUICKSTART.md → test_functionality.py → start.sh → 试听模式
```

### 场景 2：正式部署（30 分钟）
```
README.md → 配置 API → 上传视频 → 测试 → 直播模式
```

### 场景 3：深入学习（2 小时）
```
PROJECT_SUMMARY.md → 核心代码 → CHANGELOG.md → 自定义开发
```

### 场景 4：故障排查（10 分钟）
```
README.md#故障排查 → test_functionality.py → 日志分析
```

---

## 🔥 核心修复亮点

### ✅ 问题 1：字幕语音同步
**文件**：`stream_engine.py`, `app.py`  
**函数**：`get_audio_duration()`, `generate_srt()`  
**原理**：FFprobe 获取真实时长，按字数比例分配

### ✅ 问题 2：持续播放循环
**文件**：`app.py`  
**位置**：主循环逻辑（while True）  
**原理**：区分模式 + 异常恢复 + continue 机制

---

## 📱 联系方式

- 📖 查看文档：本项目所有 `.md` 文件
- 🐛 报告问题：提交 Issue（附日志截图）
- 💡 功能建议：提交 Feature Request
- 🤝 贡献代码：Fork + Pull Request

---

## 🎉 开始使用

**3 步启动**：
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行测试
python3 test_functionality.py

# 3. 启动应用
./start.sh
```

**推荐阅读顺序**：
1. 📘 QUICKSTART.md（5 分钟）
2. 🧪 运行测试脚本
3. 🚀 启动应用试用
4. 📗 README.md（深入了解）
5. 📙 PROJECT_SUMMARY.md（技术细节）

---

**祝您使用愉快！** 🎙️✨

如有任何问题，请查阅对应文档或运行测试脚本诊断。

---

_文档版本：2.0.0_  
_最后更新：2024-11-23_
