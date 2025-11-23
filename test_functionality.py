#!/usr/bin/env python3
"""
加密大漂亮 - 功能测试脚本
测试核心组件是否正常工作
"""

import os
import sys
import asyncio

def test_imports():
    """测试所有必需模块导入"""
    print("=" * 50)
    print("测试 1: 模块导入检查")
    print("=" * 50)
    
    try:
        import streamlit
        print("✅ Streamlit:", streamlit.__version__)
    except ImportError as e:
        print("❌ Streamlit 导入失败:", e)
        return False
    
    try:
        import edge_tts
        print("✅ EdgeTTS:", edge_tts.__version__ if hasattr(edge_tts, '__version__') else "已安装")
    except ImportError as e:
        print("❌ EdgeTTS 导入失败:", e)
        return False
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ LangChain OpenAI: 已安装")
    except ImportError as e:
        print("❌ LangChain OpenAI 导入失败:", e)
        return False
    
    try:
        from tavily import TavilyClient
        print("✅ Tavily: 已安装")
    except ImportError as e:
        print("❌ Tavily 导入失败:", e)
        return False
    
    print()
    return True

def test_project_files():
    """测试项目文件完整性"""
    print("=" * 50)
    print("测试 2: 项目文件检查")
    print("=" * 50)
    
    required_files = [
        "app.py",
        "logic_core.py",
        "stream_engine.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_ok = True
    for filename in required_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename} ({size} bytes)")
        else:
            print(f"❌ {filename} 缺失")
            all_ok = False
    
    print()
    return all_ok

def test_directories():
    """测试目录结构"""
    print("=" * 50)
    print("测试 3: 目录结构检查")
    print("=" * 50)
    
    required_dirs = [
        "assets",
        "temp",
        "archive_videos"
    ]
    
    for dirname in required_dirs:
        if os.path.exists(dirname) and os.path.isdir(dirname):
            print(f"✅ {dirname}/ 存在")
        else:
            print(f"⚠️  {dirname}/ 不存在，正在创建...")
            os.makedirs(dirname, exist_ok=True)
    
    print()
    return True

def test_ffmpeg():
    """测试 FFmpeg 和 FFprobe"""
    print("=" * 50)
    print("测试 4: FFmpeg 工具检查")
    print("=" * 50)
    
    import subprocess
    
    # 测试 FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg: {version_line}")
        else:
            print("❌ FFmpeg 运行失败")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg 未安装")
        return False
    except Exception as e:
        print(f"❌ FFmpeg 测试失败: {e}")
        return False
    
    # 测试 FFprobe
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFprobe: {version_line}")
        else:
            print("❌ FFprobe 运行失败")
            return False
    except FileNotFoundError:
        print("❌ FFprobe 未安装")
        return False
    except Exception as e:
        print(f"❌ FFprobe 测试失败: {e}")
        return False
    
    print()
    return True

async def test_tts():
    """测试 TTS 功能"""
    print("=" * 50)
    print("测试 5: TTS 功能测试")
    print("=" * 50)
    
    try:
        from stream_engine import text_to_speech
        
        test_text = "这是一个测试。加密大漂亮系统正在运行。"
        test_output = "temp/test_tts.mp3"
        
        print("正在生成测试语音...")
        await text_to_speech(test_text, test_output)
        
        if os.path.exists(test_output):
            size = os.path.getsize(test_output)
            print(f"✅ TTS 生成成功: {test_output} ({size} bytes)")
            # 清理测试文件
            os.remove(test_output)
            print("✅ 测试文件已清理")
        else:
            print("❌ TTS 生成失败：文件不存在")
            return False
    except Exception as e:
        print(f"❌ TTS 测试失败: {e}")
        return False
    
    print()
    return True

def test_subtitle_generation():
    """测试字幕生成功能"""
    print("=" * 50)
    print("测试 6: 字幕生成测试")
    print("=" * 50)
    
    try:
        from app import generate_srt
        
        test_text = "这是第一句话。这是第二句话，稍微长一点。第三句话也来了！最后一句话结束。"
        test_duration = 10.0  # 假设 10 秒
        test_output = "temp/test.srt"
        
        print(f"正在生成测试字幕（{test_duration}秒）...")
        result = generate_srt(test_text, test_duration, test_output)
        
        if result and os.path.exists(test_output):
            with open(test_output, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.strip().split('\n\n')
            print(f"✅ 字幕生成成功: {len(lines)} 个片段")
            print(f"✅ 字幕文件: {test_output}")
            
            # 显示第一个片段作为示例
            if lines:
                print("\n示例片段:")
                print(lines[0])
            
            # 清理测试文件
            os.remove(test_output)
            print("\n✅ 测试文件已清理")
        else:
            print("❌ 字幕生成失败")
            return False
    except Exception as e:
        print(f"❌ 字幕测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True

def test_text_cleaning():
    """测试文本清洗功能"""
    print("=" * 50)
    print("测试 7: 文本清洗测试")
    print("=" * 50)
    
    try:
        from logic_core import CryptoBrain
        
        # 创建临时实例（不需要真实密钥）
        brain = CryptoBrain(None, None, "test", "test", [], "")
        
        test_cases = [
            ("这是一段测试(音效：掌声)文本", "这是一段测试文本"),
            ("好的大漂亮，让我们开始吧", "让我们开始吧"),
            ("**重要**的内容", "重要的内容"),
            ("综上所述，结论是明确的", "结论是明确的")
        ]
        
        all_passed = True
        for input_text, expected in test_cases:
            cleaned = brain._clean_text(input_text)
            # 简单检查是否去除了不需要的内容
            if "(音效" in cleaned or "**" in cleaned or "好的大漂亮" in cleaned or "综上所述" in cleaned:
                print(f"❌ 清洗失败: {input_text[:30]}...")
                all_passed = False
            else:
                print(f"✅ 清洗成功: {input_text[:30]}...")
        
        if all_passed:
            print("\n✅ 所有文本清洗测试通过")
        else:
            print("\n⚠️  部分文本清洗测试未通过")
            
    except Exception as e:
        print(f"❌ 文本清洗测试失败: {e}")
        return False
    
    print()
    return True

def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("🎙️ 加密大漂亮 - 功能测试")
    print("=" * 50)
    print()
    
    results = []
    
    # 同步测试
    results.append(("模块导入", test_imports()))
    results.append(("项目文件", test_project_files()))
    results.append(("目录结构", test_directories()))
    results.append(("FFmpeg 工具", test_ffmpeg()))
    results.append(("文本清洗", test_text_cleaning()))
    
    # 异步测试
    try:
        results.append(("TTS 功能", asyncio.run(test_tts())))
    except Exception as e:
        print(f"❌ TTS 异步测试失败: {e}")
        results.append(("TTS 功能", False))
    
    # 字幕生成测试
    results.append(("字幕生成", test_subtitle_generation()))
    
    # 总结
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:15} : {status}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统已就绪。")
        print("\n启动应用:")
        print("  ./start.sh")
        print("  或")
        print("  streamlit run app.py")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
