import subprocess
import edge_tts
import os
import json

# 确保临时文件夹存在
os.makedirs("temp", exist_ok=True)

def optimize_text_for_tts(text):
    """
    🔥 文本预处理 - 让 TTS 更自然
    """
    import re
    
    # 1. 数字转中文
    def num_to_chinese(num_str):
        num_map = {"0":"零","1":"一","2":"二","3":"三","4":"四",
                   "5":"五","6":"六","7":"七","8":"八","9":"九"}
        return ''.join([num_map.get(c, c) for c in num_str])
    
    # 简单替换常见数字（避免复杂转换）
    text = re.sub(r'\b(\d{1,2})\b', lambda m: num_to_chinese(m.group(1)), text)
    
    # 2. 常见缩写展开
    abbreviations = {
        "BTC": "比特币",
        "ETH": "以太坊",
        "AI": "人工智能",
        "NFT": "恩艾夫提",
        "DeFi": "去中心化金融",
        "USD": "美元",
        "CEO": "首席执行官"
    }
    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)
    
    # 3. 长句拆分（避免一口气读完）
    # 在句子超过30字时添加停顿标记
    sentences = re.split(r'([。！？])', text)
    result = []
    current = ""
    for s in sentences:
        current += s
        if len(current) > 30 and s in ['。', '！', '？']:
            result.append(current)
            current = ""
    if current:
        result.append(current)
    
    return ''.join(result)

async def text_to_speech(text, output_file="temp/output.mp3", use_ssml=True):
    """
    🔥 TTS生成：优化语音自然度
    使用 SSML 控制语速、停顿、重音
    """
    # 预处理文本
    text = optimize_text_for_tts(text)
    
    if use_ssml:
        # 🔥 使用 SSML 增强自然度
        ssml_text = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">
            <voice name="zh-CN-XiaoxiaoNeural">
                <prosody rate="-5%" pitch="+2Hz">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        communicate = edge_tts.Communicate(ssml_text, voice="zh-CN-XiaoxiaoNeural")
    else:
        # 简单模式
        communicate = edge_tts.Communicate(
            text,
            voice="zh-CN-XiaoxiaoNeural",
            rate="-5%",
            pitch="+2Hz"
        )
    
    await communicate.save(output_file)
    print(f"✅ 语音生成完成: {output_file}")
    return output_file

def detect_audio_silence(audio_path):
    """
    检测音频开头和结尾的静音时长
    返回 (开头静音, 结尾静音) 单位：秒
    """
    try:
        # 检测开头静音
        cmd_start = [
            'ffmpeg', '-i', audio_path,
            '-af', 'silencedetect=noise=-30dB:d=0.1',
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd_start, capture_output=True, text=True)
        
        # 从输出中解析静音时间
        import re
        silence_start = re.search(r'silence_start: (\d+\.\d+)', result.stderr)
        silence_end = re.search(r'silence_end: (\d+\.\d+)', result.stderr)
        
        start_silence = float(silence_start.group(1)) if silence_start else 0.0
        end_silence = float(silence_end.group(1)) if silence_end else 0.0
        
        return start_silence, end_silence
    except:
        return 0.0, 0.0

def get_audio_duration(audio_path):
    """
    🔥 获取音频真实时长 + 检测静音偏移
    """
    try:
        command = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            audio_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        
        # 检测静音偏移
        start_silence, _ = detect_audio_silence(audio_path)
        
        print(f"✅ 音频时长: {duration:.2f}秒 | 开头静音: {start_silence:.2f}秒")
        return duration, start_silence
    except Exception as e:
        print(f"⚠️ 无法获取音频时长: {e}")
        return None, 0.0

def trim_audio_silence(audio_path, output_path=None):
    """
    去除音频开头和结尾的静音段
    确保字幕与实际语音精确对齐
    """
    if output_path is None:
        output_path = audio_path.replace('.mp3', '_trimmed.mp3')
    
    try:
        command = [
            'ffmpeg', '-y',
            '-i', audio_path,
            '-af', 'silenceremove=start_periods=1:start_silence=0.1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-40dB,areverse',
            '-acodec', 'libmp3lame',
            output_path
        ]
        subprocess.run(command, check=True, capture_output=True)
        print(f"✅ 音频静音已去除: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️ 去除静音失败，使用原音频: {e}")
        return audio_path

def create_preview_video(video_path, audio_path, srt_path, output_path="temp/preview_output.mp4"):
    """
    合成预览视频（带硬字幕）- 用于试听模式
    """
    # 获取绝对路径，防止FFmpeg找不到文件
    abs_srt_path = os.path.abspath(srt_path).replace("\\", "/")
    
    # 🔥 字幕样式配置 (抖音/TikTok风格)
    # Fontsize=18: 字号稍大
    # MarginV=40: 抬高底部边距，绝对不挡脸
    # Outline=2: 黑色描边，确保在任何背景下都清晰
    style = "Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40"
    
    # 构建滤镜字符串 (注意转义)
    subtitle_filter = f"subtitles='{abs_srt_path}':force_style='{style}'"

    command = [
        'ffmpeg', '-y',
        '-stream_loop', '-1', '-i', video_path,  # 输入1: 循环背景
        '-i', audio_path,                        # 输入2: AI语音
        '-vf', subtitle_filter,                  # 【关键】烧录硬字幕
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-c:a', 'aac',
        '-shortest',                             # 音频播完视频即停
        '-preset', 'ultrafast',                  # 追求合成速度
        output_path
    ]
    
    try:
        # 执行命令，捕获输出
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ 预览视频生成成功: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 预览生成失败: {e.stderr}")
        return None

def start_stream(stream_key, video_path, audio_path=None, srt_path=None, is_direct_file=False):
    """
    RTMP 推流核心
    返回值：True 表示推流成功完成，False 表示失败
    """
    if not stream_key:
        print("❌ 错误：没有推流码")
        return False

    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    
    if is_direct_file:
        # === 模式 A：老视频直接推 ===
        print(f"📡 正在推流历史视频文件: {video_path}")
        command = [
            'ffmpeg', '-re',
            '-i', video_path,
            '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '3000k',
            '-c:a', 'aac', '-b:a', '192k',
            '-f', 'flv', rtmp_url
        ]
    else:
        # === 模式 B：AI 合成推流 (带字幕) ===
        print("📡 正在推流 AI 生成内容...")
        abs_srt_path = os.path.abspath(srt_path).replace("\\", "/")
        # 同样的字幕样式
        style = "Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=40"
        subtitle_filter = f"subtitles='{abs_srt_path}':force_style='{style}'"
        
        command = [
            'ffmpeg', '-re',
            '-stream_loop', '-1', '-i', video_path,
            '-i', audio_path,
            '-vf', subtitle_filter, # 烧录字幕
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '3000k',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest',
            '-f', 'flv', rtmp_url
        ]
    
    try:
        subprocess.run(command, check=True)
        print("✅ 推流完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 推流发生错误: {e}")
        return False
