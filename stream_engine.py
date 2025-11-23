import subprocess
import edge_tts
import os
import json

# 确保临时文件夹存在
os.makedirs("temp", exist_ok=True)

async def text_to_speech(text, output_file="temp/output.mp3"):
    """
    TTS生成：强制使用最自然的 '晓晓' 音色
    """
    # zh-CN-XiaoxiaoNeural 是目前 EdgeTTS 中情感最丰富的中文女声
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural") 
    await communicate.save(output_file)
    return output_file

def get_audio_duration(audio_path):
    """
    🔥 核心修复：使用 ffprobe 获取音频真实时长
    解决字幕与语音不同步的根本问题
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
        print(f"✅ 音频时长: {duration:.2f}秒")
        return duration
    except Exception as e:
        print(f"⚠️ 无法获取音频时长，使用备用估算: {e}")
        # 备用方案：按 3.2 字/秒估算
        return None

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
