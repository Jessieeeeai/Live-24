# 📝 更新日志

## [2.0.0] - 2024-11-23

### 🔥 重大修复

#### 1. 字幕语音同步问题 ✅
**问题描述**：
- 字幕显示速度与实际语音不匹配
- 字幕提前消失或滞后
- 使用固定语速（3.2字/秒）估算，不准确

**解决方案**：
- 使用 FFprobe 获取音频真实时长
- 基于实际时长按字数比例分配字幕时间
- 每行字幕最短显示 1.5 秒（防止闪烁）
- 支持备用方案（FFprobe 不可用时）

**技术细节**：
```python
# stream_engine.py - 新增函数
def get_audio_duration(audio_path):
    # 使用 ffprobe 获取精确时长
    
# app.py - 字幕生成改进
def generate_srt(text, audio_duration, output_path):
    # 计算实际语速
    actual_speed = total_chars / audio_duration
    # 按字数占比分配时间
    seg_char_ratio = len(seg) / total_seg_chars
    duration = audio_duration * seg_char_ratio
```

#### 2. 持续播放问题 ✅
**问题描述**：
- 试听模式播完一次就退出程序
- 直播模式遇到错误后停止
- 没有实现真正的 24 小时无限循环

**解决方案**：
- 试听模式：明确使用 `break` 退出（设计行为）
- 直播模式：使用 `continue` 保持循环
- 添加全局异常捕获和重试机制
- 错误后自动等待 10 秒重启下一轮

**技术细节**：
```python
# app.py - 主循环改进
while True:
    try:
        # 执行内容生成和播放
        if is_preview:
            # 试听模式：播完就退出
            break
        else:
            # 直播模式：继续循环
            time.sleep(interval)
            continue
    except Exception as e:
        # 错误恢复
        if is_live:
            time.sleep(10)
            continue  # 重试
        else:
            break  # 试听模式退出
```

### ✨ 新增功能

#### 1. 音频时长检测
- 新增 `get_audio_duration()` 函数
- 自动获取 TTS 生成音频的精确时长
- 支持 JSON 格式输出解析

#### 2. 运行状态监控
- 显示运行轮次统计
- 成功/错误计数
- 实时状态更新

#### 3. 增强的去重机制
- 关键词匹配 + 相似度检测
- 50% 词汇重叠阈值
- 自动清理过期记录

#### 4. 文本清洗优化
- 扩展废话词库
- 去除不适合朗读的标点符号
- 规范化标点合并
- 移除行首序号

### 🔧 优化改进

#### 代码质量
- 添加详细注释和文档字符串
- 统一错误处理机制
- 改进日志输出格式
- 增加类型提示

#### 性能优化
- FFmpeg 预设调整为 ultrafast（预览）/ veryfast（推流）
- 减少不必要的文件 I/O
- 优化字幕切分算法

#### 用户体验
- 更清晰的状态提示
- 彩色 emoji 图标
- 进度百分比显示
- 错误信息更友好

### 📚 文档完善

#### 新增文档
- `README.md` - 完整项目文档
- `QUICKSTART.md` - 5 分钟快速开始
- `CHANGELOG.md` - 本更新日志
- `test_functionality.py` - 自动化测试脚本
- `start.sh` - 一键启动脚本

#### 文档内容
- 详细的安装说明
- 功能使用教程
- 故障排查指南
- API 配置说明
- 自定义配置指南

### 🐛 Bug 修复

1. **字幕时间计算错误**
   - 修复：使用真实音频时长而非估算
   
2. **循环提前退出**
   - 修复：区分试听/直播模式的循环逻辑
   
3. **异常未捕获**
   - 修复：添加全局异常处理器
   
4. **文本清洗不完整**
   - 修复：扩展正则表达式规则
   
5. **去重失效**
   - 修复：改进相似度检测算法

### 🔒 安全性

- 添加 `.gitignore` 防止密钥泄露
- 密码输入框使用 `type="password"`
- 敏感信息不输出到日志

### 📦 依赖更新

```txt
streamlit>=1.28.0
edge-tts>=6.1.9
langchain-openai>=0.0.2
tavily-python>=0.3.0
python-dotenv>=1.0.0
```

### 🗂️ 文件结构

```
webapp/
├── app.py                    # 主应用（12.7KB）
├── logic_core.py             # AI 核心（7.8KB）
├── stream_engine.py          # 音视频引擎（4.0KB）
├── test_functionality.py     # 测试脚本（7.8KB）
├── start.sh                  # 启动脚本（1.6KB）
├── requirements.txt          # 依赖列表
├── README.md                 # 项目文档（5.1KB）
├── QUICKSTART.md            # 快速开始（2.8KB）
├── CHANGELOG.md             # 本文件
├── .gitignore               # Git 忽略规则
├── assets/                  # 资源文件夹
├── temp/                    # 临时文件夹
└── archive_videos/          # 历史视频库
```

### ⚙️ 配置变更

#### 字幕样式
- Fontsize: 16 → 18
- MarginV: 35 → 40

#### AI 参数
- temperature: 1.3（保持）
- timeout: 30 → 60 秒

#### 搜索配置
- max_results: 5 → 10
- days: 1（保持）

### 🎯 已知问题

无重大已知问题。

### 🔮 下一步计划

1. [ ] 支持多语言 TTS
2. [ ] 添加实时弹幕互动
3. [ ] 支持更多直播平台（Twitch, Twitter）
4. [ ] 添加声音特效和背景音乐
5. [ ] 图表数据可视化展示
6. [ ] AI 生成配图
7. [ ] 自动剪辑精彩片段
8. [ ] 用户反馈学习机制

---

## [1.0.0] - 初始版本

### 基础功能
- AI 内容生成
- TTS 语音合成
- 字幕烧录
- YouTube 推流
- 备用话题库
- 历史视频插播

### 核心问题
- 字幕语音不同步 ❌
- 无法持续播放 ❌

---

**更新频率**：按需更新
**维护者**：Crypto Beauty Team
