import os
import json
import time
import re
import datetime
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

# 历史记录文件
HISTORY_FILE = "topic_history.json"

class CryptoBrain:
    def __init__(self, deepseek_key, tavily_key, topic_scope, persona_prompt, backup_topics, target_domains):
        self.backup_topics = backup_topics
        self.target_domains = target_domains # 用户指定的信源列表
        
        # 1. 初始化大脑 (DeepSeek)
        if deepseek_key:
            self.llm = ChatOpenAI(
                model="deepseek-chat", 
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
                temperature=1.3, # 提高创造性，模拟真人聊天的发散性
                timeout=60  # 增加超时时间
            )
        else:
            self.llm = None
            
        # 2. 初始化搜索 (Tavily)
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None
        self.topic = topic_scope
        self.persona = persona_prompt
        
        # 3. 定义深度分析框架 SOP
        self.frameworks = {
            "5W1H": "热点解读 (Who, What, Where, When, Why, How)",
            "PEST": "趋势分析 (政治 Political, 经济 Economic, 社会 Social, 技术 Technology)",
            "SWOT": "争议人物/项目 (优势 Strengths, 劣势 Weaknesses, 机会 Opportunities, 威胁 Threats)",
            "MECE": "深度复盘 (完全穷尽，相互独立)"
        }

    def _check_duplication(self, new_topic):
        """
        5小时去重机制：避免短时间内重复讲同一个新闻
        """
        try:
            if not os.path.exists(HISTORY_FILE):
                # 文件不存在，创建初始记录
                with open(HISTORY_FILE, "w") as f:
                    json.dump([{"topic": new_topic, "time": time.time()}], f)
                return False
            
            with open(HISTORY_FILE, "r") as f: 
                history = json.load(f)
            
            # 1. 清理超过5小时的旧记录
            current_time = time.time()
            valid_history = [h for h in history if current_time - h['time'] < 5 * 3600]
            
            # 2. 查重 (简单关键词匹配 + 相似度检测)
            is_dup = False
            for h in valid_history:
                # 方法1：包含关系
                if h['topic'] in new_topic or new_topic in h['topic']:
                    is_dup = True
                    break
                # 方法2：提取关键词对比
                old_words = set(re.findall(r'\w+', h['topic'].lower()))
                new_words = set(re.findall(r'\w+', new_topic.lower()))
                # 如果有超过 50% 的关键词重叠，视为重复
                if len(old_words & new_words) / max(len(new_words), 1) > 0.5:
                    is_dup = True
                    break
            
            # 3. 如果不重复，更新文件
            if not is_dup:
                valid_history.append({"topic": new_topic, "time": current_time})
                with open(HISTORY_FILE, "w") as f: 
                    json.dump(valid_history, f, ensure_ascii=False, indent=2)
                print(f"✅ 新话题已记录: {new_topic[:30]}...")
            else:
                print(f"⚠️ 话题重复，跳过: {new_topic[:30]}...")
            
            return is_dup
        except Exception as e:
            print(f"⚠️ 去重检查失败: {e}")
            return False

    def _clean_text(self, text):
        """
        🔥 强力去废话正则清洗器
        """
        if not text:
            return ""
        
        # 1. 去掉 (音效: xxx), [动作], 【背景音】, <标签>
        text = re.sub(r"[\(\[\【<].*?[\)\]\】>]", "", text)
        
        # 2. 去掉 Markdown 格式符号
        text = text.replace("*", "").replace("#", "").replace("`", "")
        text = text.replace("_", "").replace("~", "")
        
        # 3. 去掉 AI 习惯性废话（扩展列表）
        bad_phrases = [
            "好的大漂亮", "没问题", "好的", "综上所述", "总之", 
            "主持人", "Let's go", "各位听众", "大家好",
            "接下来", "那么", "首先", "其次", "最后",
            "值得注意的是", "需要指出的是", "我们可以看到",
            "根据以上分析", "通过分析", "可以发现",
            "音效", "背景音乐", "掌声", "笑声"
        ]
        for phrase in bad_phrases:
            text = text.replace(phrase, "")
        
        # 4. 去除不适合朗读的标点符号（保留基本标点）
        # 移除：引号、括号、书名号等
        text = re.sub(r'["""''「」『』（）\(\)\[\]【】《》<>]', '', text)
        
        # 5. 规范化标点：多个标点合并为一个
        text = re.sub(r'[，,]{2,}', '，', text)
        text = re.sub(r'[。.]{2,}', '。', text)
        text = re.sub(r'[！!]{2,}', '！', text)
        text = re.sub(r'[？?]{2,}', '？', text)
        
        # 6. 去除多余空行和空格
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        # 7. 去除行首的序号（1. 2. 一、二、等）
        text = re.sub(r'^\s*[\d一二三四五六七八九十]+[、\.\s]+', '', text, flags=re.MULTILINE)
        
        return text.strip()

    def fetch_news_and_analyze(self):
        """
        主流程：搜索新闻 -> 分析 -> 生成文案
        返回：(script, error, is_backup)
        """
        if not self.tavily: 
            return None, "缺少 Tavily Key", False
        
        # 🟢 获取今天日期，强制搜最新
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"🔍 正在从指定信源搜索 {today_str} 的 {self.topic} 新闻...")
        
        # 处理用户指定的域名
        domain_list = [d.strip() for d in self.target_domains.split(",") if d.strip()]
        
        try:
            # 🔥 Tavily 高级搜索配置
            response = self.tavily.search(
                query=f"breaking news {self.topic} crypto blockchain {today_str}",
                search_depth="advanced",
                include_domains=domain_list if domain_list else None, # 只搜指定网站
                max_results=10,  # 增加搜索结果数量
                days=1  # 强制 24 小时内
            )
            results = response.get("results", [])
            print(f"📰 搜索到 {len(results)} 条结果")
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return None, f"搜索失败: {e}", False

        # 筛选未讲过的新闻
        selected_news = None
        for item in results:
            title = item.get('title', '')
            if title and not self._check_duplication(title):
                selected_news = item
                break
        
        # 没新闻 -> 启用 CMS 备用库
        if not selected_news:
            print("⚠️ 无最新高价值新闻，或都已讲过。启用备用话题库...")
            import random
            if self.backup_topics:
                backup = random.choice(self.backup_topics)
            else:
                backup = "比特币去中心化精神科普"
            
            print(f"📚 使用备用话题: {backup}")
            return backup, None, True  # True = 是备用内容

        print(f"✅ 选中头条: {selected_news['title']}")

        # 构建分析框架提示词列表
        framework_str = "\n".join([f"- {k}: {v}" for k, v in self.frameworks.items()])
        
        # 🔥 核心 Prompt：SOP + 去废话 + 口语化
        prompt = f"""
{self.persona}

【原始新闻】
标题：{selected_news['title']}
内容：{selected_news['content']}
来源：{selected_news['url']}

【任务指令 - 请严格执行】
1. **思维链分析**：先在内心思考，从以下框架中选一个最适合的进行推演：
{framework_str}

2. **深度撰写**：
   - 将分析结果转化为一篇【口语化】的播客文案。
   - 必须有犀利观点，不能只是复述新闻。
   - 句子要短，节奏要快，像真人在聊天。
   - 适合女性主持人播报的语气和用词。

3. **格式清洗 (违者死机)**：
   - 严禁输出 "我选择了xx框架" 或 "好的" 等元语言。
   - 严禁包含 (音效)、【动作】、[背景音] 等剧本标记。
   - 严禁使用引号、括号等不适合朗读的标点符号。
   - 严禁使用"综上所述"、"总之"、"接下来"等书面语。
   - 只使用逗号、句号、问号、感叹号作为标点。
   - 字数控制在 500-700 字之间。

4. **输出要求**：
   - 直接输出最终的播客文案。
   - 语气自然流畅，像是在和朋友聊天。
   - 包含情感和节奏变化。

现在开始创作：
"""
        
        try:
            # 调用 DeepSeek
            print("🧠 DeepSeek 正在深度分析...")
            raw_script = self.llm.invoke(prompt).content
            
            # 清洗结果
            print("🧹 清洗文案...")
            clean_script = self._clean_text(raw_script)
            
            # 验证输出质量
            if len(clean_script) < 100:
                print("⚠️ 生成内容过短，可能存在问题")
                return None, "生成内容质量不佳", False
            
            print(f"✅ 文案生成完成，共 {len(clean_script)} 字")
            return clean_script, None, False
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return None, f"生成失败: {e}", False
