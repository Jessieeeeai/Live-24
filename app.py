import streamlit as st
import os
import time
import asyncio
import random
import json
from logic_core import CryptoBrain
from stream_engine import text_to_speech, start_stream, create_preview_video, get_audio_duration, trim_audio_silence

# --- 初始化环境 ---
os.makedirs("assets", exist_ok=True)
os.makedirs("temp", exist_ok=True)
os.makedirs("archive_videos", exist_ok=True)
DB_FILE = "knowledge_db.json"

st.set_page_config(page_title="Crypto Beauty Ultimate", page_icon="🎙️", layout="wide")

# --- 数据库操作 (CMS) ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f: 
            return json.load(f)
    return ["科普：比特币减半效应", "故事：披萨节的历史", "教学：如何保管私钥"]

def save_db(topics):
    with open(DB_FILE, "w", encoding='utf-8') as f: 
        json.dump(topics, f, ensure_ascii=False)

# --- 🔥 优化的字幕生成算法 (核心修复点) ---
def generate_srt(text, audio_duration, output_path, start_offset=0.0):
    """
    将长文案切分为 SRT 字幕
    🔥 核心修复：基于实际音频时长，而非估算语速
    🔥 新增：起始偏移，解决字幕语音不同步问题
    """
    # 预处理：移除换行，变成一长串
    full_text = text.replace("\n", " ").replace("  ", " ").strip()
    
    # 统计总字数
    total_chars = len(full_text)
    if total_chars == 0:
        print("⚠️ 文本为空，无法生成字幕")
        return False
    
    # 🔥 核心算法：基于真实音频时长计算实际语速
    actual_speed = total_chars / audio_duration  # 真实的字/秒
    print(f"📊 字幕同步参数: 总字数={total_chars}, 音频时长={audio_duration:.2f}s, 实际语速={actual_speed:.2f}字/秒")
    
    # 切分策略：智能断句，优先按标点，其次按长度
    segments = []
    current_seg = ""
    
    for i, char in enumerate(full_text):
        current_seg += char
        # 强断句标点
        if char in ["。", "！", "？", ";"]:
            if current_seg.strip():
                segments.append(current_seg.strip())
            current_seg = ""
        # 弱断句标点（但只在字数超过8时才断）
        elif char in ["，", ","] and len(current_seg) >= 8:
            if current_seg.strip():
                segments.append(current_seg.strip())
            current_seg = ""
        # 长度限制：超过18字强制断句
        elif len(current_seg) >= 18:
            if current_seg.strip():
                segments.append(current_seg.strip())
            current_seg = ""
            
    if current_seg.strip(): 
        segments.append(current_seg.strip())
    
    if len(segments) == 0:
        print("⚠️ 切分后无有效字幕段")
        return False
    
    # 计算每个片段的字数占比，按比例分配时间
    total_seg_chars = sum(len(seg) for seg in segments)
    
    # 写入 SRT 文件
    with open(output_path, "w", encoding="utf-8") as f:
        start_time = start_offset  # 🔥 起始偏移，补偿音频开头静音
        for i, seg in enumerate(segments):
            # 按字数占比分配时间
            seg_char_ratio = len(seg) / total_seg_chars
            duration = audio_duration * seg_char_ratio
            
            # 🔥 动态调整最短显示时间：短句1.5秒，长句2.5秒
            min_duration = 1.5 if len(seg) <= 10 else 2.0
            
            # 但不能超过实际剩余时间
            remaining_time = audio_duration - (start_time - start_offset)
            if remaining_time > 0:
                duration = max(min_duration, min(duration, remaining_time / (len(segments) - i)))
            else:
                duration = min_duration
            
            end_time = start_time + duration
            
            # SRT 时间格式 00:00:00,000
            def fmt(t):
                h, r = divmod(t, 3600)
                m, s = divmod(r, 60)
                return f"{int(h):02}:{int(m):02}:{int(s):02},{int((t%1)*1000):03}"
            
            f.write(f"{i+1}\n{fmt(start_time)} --> {fmt(end_time)}\n{seg}\n\n")
            start_time = end_time
    
    print(f"✅ 字幕生成完成: {len(segments)} 行，总时长 {audio_duration:.2f}s，起始偏移 {start_offset:.2f}s")
    return True

# --- UI 界面构建 ---
st.title("🎙️ 加密大漂亮 | 全自动 AI 直播中控台 (Ultimate)")

with st.sidebar:
    st.header("🔑 核心密钥")
    deepseek_key = st.text_input("DeepSeek Key", type="password")
    tavily_key = st.text_input("Tavily Key", type="password")
    yt_key = st.text_input("YouTube 推流码", type="password")
    
    st.header("🌐 信息源控制 (SOP)")
    target_domains = st.text_area("指定新闻来源 (逗号分隔)", 
        "coindesk.com, theblock.co, cointelegraph.com, decrypt.co",
        help="留空则搜索全网，建议填入 trusted media 以保证质量")
    
    st.header("🎛️ 运行模式")
    mode = st.radio("选择模式", ["🛠️ 试听 (生成预览视频)", "📡 直播 (24H无限循环)"])
    
    st.header("⚙️ 策略设置")
    topic = st.text_input("监控关键词", "Bitcoin, Ethereum, Solana, AI Agent")
    interval = st.slider("轮播间隔 (秒)", 30, 600, 120, help="播完一条休息多久")
    allow_replay = st.checkbox("允许插播老视频 (防冷场)", value=True)
    old_video_chance = st.slider("老视频插播概率 (%)", 0, 100, 30, help="无新闻时播放历史视频的概率")
    
    st.header("🎤 语音设置")
    voice_option = st.selectbox(
        "选择播报音色",
        [
            ("晓依 (推荐-自然播报)", "zh-CN-XiaoyiNeural"),
            ("晓晓 (情感丰富)", "zh-CN-XiaoxiaoNeural"),
            ("晓涵 (温柔自然)", "zh-CN-XiaohanNeural"),
            ("晓萱 (成熟知性)", "zh-CN-XiaoxuanNeural"),
            ("云希 (男声-沉稳)", "zh-CN-YunxiNeural")
        ],
        format_func=lambda x: x[0],
        help="选择不同的语音风格，晓依最接近真人播报"
    )
    selected_voice = voice_option[1]
    
    st.divider()
    bg_file = st.file_uploader("📺 直播背景 (MP4)", type=['mp4'])

# --- Tab 页面 ---
tab1, tab2 = st.tabs(["📡 运行监视器", "📚 备用话题管理 (CMS)"])

# === Tab 2: CMS 后台 ===
with tab2:
    st.subheader("当搜不到 24H 新闻时，随机聊以下话题：")
    curr_topics = load_db()
    edited = st.data_editor([{"topic": t} for t in curr_topics], num_rows="dynamic", use_container_width=True)
    if st.button("💾 保存话题库"):
        save_db([r["topic"] for r in edited if r["topic"]])
        st.success("知识库已更新！")

# === Tab 1: 运行前台 ===
with tab1:
    col1, col2 = st.columns([3, 2])
    with col1: 
        monitor = st.empty() # 视频播放区
    with col2: 
        log_box = st.empty() # 日志区
        status_box = st.empty() # 状态区
        start_btn = st.button("🚀 启动系统", type="primary", use_container_width=True)

    if start_btn:
        # 1. 基础环境检查
        if not deepseek_key or not tavily_key:
            st.error("❌ 错误：请填入 DeepSeek 和 Tavily Key")
            st.stop()
        
        video_path = "assets/background.mp4"
        if bg_file:
            with open(video_path, "wb") as f: 
                f.write(bg_file.getbuffer())
            
        if not os.path.exists(video_path):
            st.error("❌ 错误：请上传背景视频")
            st.stop()

        # 2. 初始化大脑
        db_topics = load_db()
        persona_prompt = """你是"加密大漂亮"，一位专业的加密货币播客主持人。
你的风格：知性、犀利、专业、带点幽默、拒绝模棱两可。
你像真人在聊天八卦，严禁"播音腔"或"念通稿"。
你的任务是将新闻进行深度分析，给出独到见解，而不是简单复述。"""
        
        brain = CryptoBrain(deepseek_key, tavily_key, topic, persona_prompt, db_topics, target_domains)
        
        is_preview = "试听" in mode
        is_live = "直播" in mode
        
        # 3. 主循环统计
        round_count = 0
        success_count = 0
        error_count = 0
        
        # 🔥 核心修复：真正的无限循环
        while True:
            round_count += 1
            
            try:
                with log_box.container():
                    st.info(f"🔄 第 {round_count} 轮 | 正在全网搜寻 24H 内的新闻...")
                    
                    # 更新状态
                    with status_box.container():
                        st.metric("运行轮次", round_count)
                        col_a, col_b = st.columns(2)
                        col_a.metric("成功", success_count)
                        col_b.metric("错误", error_count)
                    
                    # A. 思考与写稿
                    script, err, is_backup = brain.fetch_news_and_analyze()
                    
                    # B. 决策：是否插播老视频
                    play_old_video = False
                    final_video_file = None
                    
                    if is_backup and allow_replay:
                        local_videos = [f for f in os.listdir("archive_videos") if f.endswith(".mp4")]
                        if local_videos and random.random() * 100 < old_video_chance:
                            play_old_video = True
                            chosen = random.choice(local_videos)
                            final_video_file = os.path.join("archive_videos", chosen)
                            st.warning(f"📼 无热点新闻，随机插播历史视频：{chosen}")

                    # C. 执行播放/生成
                    if play_old_video:
                        if is_preview:
                            monitor.video(final_video_file)
                            st.success("✅ 预览播放了老视频")
                            success_count += 1
                            # 🔥 试听模式：只播一次就退出循环
                            st.info("试听模式完成，停止运行")
                            break
                        else:
                            # 直播模式：推流老视频
                            if yt_key:
                                monitor.image("https://via.placeholder.com/800x450/FF0000/FFFFFF?text=LIVE+ON+AIR", 
                                            caption="🔴 推流中...", use_column_width=True)
                                result = start_stream(yt_key, final_video_file, is_direct_file=True)
                                if result:
                                    st.success("✅ 历史视频推流完成")
                                    success_count += 1
                                else:
                                    st.error("❌ 推流失败")
                                    error_count += 1
                            else:
                                st.error("❌ 缺少推流码")
                                error_count += 1
                    
                    elif script:
                        st.success("📝 深度文案已生成 (SOP框架+去废话)")
                        with st.expander("查看文案详情"): 
                            st.write(script)
                        
                        st.write("🗣️ 合成晓晓语音...")
                        ts = int(time.time())
                        audio_path = f"temp/s_{ts}.mp3"
                        srt_path = f"temp/s_{ts}.srt"
                        
                        # 生成语音（使用SSML优化）
                        asyncio.run(text_to_speech(script, audio_path, use_ssml=True))
                        
                        # 🔥 去除音频开头和结尾的静音
                        st.write("✂️ 优化音频（去除静音）...")
                        audio_path = trim_audio_silence(audio_path, audio_path.replace('.mp3', '_clean.mp3'))
                        
                        # 🔥 获取音频真实时长和静音偏移
                        result = get_audio_duration(audio_path)
                        if result and len(result) == 2:
                            audio_duration, start_silence = result
                        else:
                            audio_duration = result if result else len(script) / 3.2
                            start_silence = 0.0
                        
                        if audio_duration:
                            st.info(f"⏱️ 音频时长: {audio_duration:.2f} 秒 ({int(audio_duration//60)}分{int(audio_duration%60)}秒) | 起始偏移: {start_silence:.2f}s")
                        else:
                            st.warning(f"⚠️ 使用估算时长: {audio_duration:.2f}s")
                        
                        # 🔥 基于真实时长和偏移生成字幕
                        st.write("🔥 生成精确同步字幕...")
                        srt_success = generate_srt(script, audio_duration, srt_path, start_offset=start_silence)
                        
                        if not srt_success:
                            st.error("❌ 字幕生成失败")
                            error_count += 1
                            # 继续下一轮，不中断
                            if is_live:
                                time.sleep(10)
                                continue
                            else:
                                break
                        
                        if is_preview:
                            # 试听模式：生成预览视频
                            preview_file = f"temp/p_{ts}.mp4"
                            st.write("🎬 合成预览视频（带硬字幕）...")
                            final = create_preview_video(video_path, audio_path, srt_path, preview_file)
                            if final: 
                                monitor.video(final)
                                st.balloons()
                                st.success("✅ 预览视频生成完成！")
                                success_count += 1
                            else:
                                st.error("❌ 视频合成失败")
                                error_count += 1
                            # 🔥 试听模式：播完就退出
                            st.info("试听模式完成，停止运行")
                            break
                        else:
                            # 直播模式：推流
                            if yt_key:
                                st.warning("📡 直播中 (带硬字幕)...")
                                monitor.image("https://via.placeholder.com/800x450/FF0000/FFFFFF?text=LIVE+ON+AIR", 
                                            caption="🔴 LIVE 正在推流", use_column_width=True)
                                result = start_stream(yt_key, video_path, audio_path, srt_path)
                                if result:
                                    st.success("✅ 本轮推流完成")
                                    success_count += 1
                                else:
                                    st.error("❌ 推流失败")
                                    error_count += 1
                            else:
                                st.error("❌ 缺少推流码")
                                error_count += 1
                    
                    else:
                        # 无内容可播
                        st.error(f"❌ 错误: {err}")
                        error_count += 1
                    
                    # D. 智能休息逻辑 (仅直播模式)
                    if is_live:
                        # 如果有音频时长，在结束前30秒开始准备下一条
                        if 'audio_duration' in locals() and audio_duration:
                            # 计算实际等待时间：音频时长 - 30秒（提前准备）
                            wait_time = max(10, audio_duration - 30)
                            st.info(f"⏳ 当前内容时长 {audio_duration:.0f}秒，将在播放结束前30秒开始准备下一条...")
                            st.info(f"⏳ 等待 {wait_time:.0f} 秒后开始下一轮...")
                            time.sleep(wait_time)
                        else:
                            st.info(f"⏳ 本条结束，休息 {interval} 秒后继续下一轮...")
                            time.sleep(interval)
                        # 🔥 继续循环，不退出
                        continue
                    else:
                        # 试听模式已经在上面 break 了
                        break

            except KeyboardInterrupt:
                st.warning("⚠️ 用户手动停止")
                break
            
            except Exception as e:
                st.error(f"💥 发生意外错误: {e}")
                error_count += 1
                if is_live:
                    st.warning("🔄 系统将在 10 秒后尝试重启下一轮...")
                    time.sleep(10)
                    # 🔥 继续循环，不退出
                    continue
                else:
                    # 试听模式出错就停止
                    break
        
        # 循环结束后的总结（只有试听模式会到这里）
        st.success(f"🏁 运行结束 | 总轮次: {round_count}, 成功: {success_count}, 错误: {error_count}")
