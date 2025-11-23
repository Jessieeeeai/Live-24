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
        self.target_domains = target_domains  # 用户指定的信源列表
        
        # 1. 初始化大脑 (DeepSeek)
        if deepseek_key:
            self.llm = ChatOpenAI(
                model="deepseek-chat", 
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
                temperature=1.2,  # 提高创造性
                timeout=120,  # 增加超时时间，支持深度分析
                max_tokens=4000  # 🔥 明确设置最大token数，确保长内容生成
            )
        else:
            self.llm = None
            
        # 2. 初始化搜索 (Tavily)
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None
        self.topic = topic_scope
        self.persona = persona_prompt
        
        # 3. 🔥 定义10种深度分析框架 (完整版)
        self.frameworks = {
            "5W1H": {
                "name": "热点解读框架",
                "structure": "事件概述→背景分析→关键人物→时间脉络→深层原因→影响预测",
                "适用": ["突发事件", "新闻快讯", "实时动态"]
            },
            "PEST": {
                "name": "趋势分析框架",
                "structure": "政治因素→经济环境→社会文化→技术变革→综合影响→趋势判断",
                "适用": ["市场趋势", "宏观环境", "长期变化"]
            },
            "MECE": {
                "name": "商业事件框架",
                "structure": "问题拆解→分类归纳→逐层分析→逻辑验证→结论整合",
                "适用": ["商业决策", "战略分析", "复杂问题"]
            },
            "SWOT": {
                "name": "人物争议框架",
                "structure": "优势分析→劣势剖析→机会识别→威胁评估→战略建议",
                "适用": ["人物评价", "项目评估", "竞争分析"]
            },
            "利益相关者": {
                "name": "政策解读框架",
                "structure": "政府层面→企业角度→民众视角→专家观点→媒体立场→综合平衡",
                "适用": ["政策发布", "监管变化", "公共事件"]
            },
            "波特五力": {
                "name": "产业变化框架",
                "structure": "竞争对手→供应商→买方→替代品→潜在进入者→行业前景",
                "适用": ["行业分析", "竞争格局", "市场进入"]
            },
            "金字塔原理": {
                "name": "社会现象框架",
                "structure": "核心观点→支撑论据→具体事实→逻辑推理→结论强化",
                "适用": ["观点表达", "说服沟通", "报告撰写"]
            },
            "问题树": {
                "name": "案例复盘框架",
                "structure": "核心问题→子问题拆解→根因分析→解决方案→实施路径",
                "适用": ["案例分析", "事后复盘", "问题诊断"]
            },
            "决策矩阵": {
                "name": "对比评估框架",
                "structure": "选项列举→评判标准→权重分配→得分评估→最优选择",
                "适用": ["多方案对比", "选择决策", "评估排序"]
            },
            "情景分析": {
                "name": "未来预测框架",
                "structure": "当前状态→驱动因素→可能情景→概率评估→应对策略",
                "适用": ["未来展望", "风险预判", "战略规划"]
            }
        }

    def _calculate_viral_potential(self, news_item):
        """
        🔥 Step 2: 计算爆火潜力评分
        评分维度：新鲜度(30%) + 争议性(25%) + 受众覆盖(20%) + 传播速度(15%) + 情绪强度(10%)
        """
        score = 0
        # 🔥 FIX: 兼容 Tavily API 的不同字段名 (title/name, content/snippet)
        title = news_item.get('title') or news_item.get('name') or ''
        content_text = news_item.get('content') or news_item.get('snippet') or news_item.get('description') or ''
        content = (title + ' ' + content_text).lower()
        
        # 1. 新鲜度 (30分) - 基于发布时间
        published_at = news_item.get('published_date', '')
        if published_at:
            # 简单处理：如果有今天的关键词，得高分
            if 'today' in published_at or datetime.datetime.now().strftime('%Y-%m-%d') in published_at:
                score += 30
            else:
                score += 15
        else:
            score += 20  # 默认分
        
        # 2. 争议性 (25分) - 关键词检测
        controversial_words = ['争议', 'controversial', '崩盘', 'crash', '暴涨', 'surge', 
                              '诈骗', 'scam', '起诉', 'lawsuit', '监管', 'regulation']
        controversy_score = sum(5 for word in controversial_words if word in content)
        score += min(25, controversy_score)
        
        # 3. 受众覆盖面 (20分) - 话题热度
        hot_topics = ['bitcoin', 'btc', 'ethereum', 'eth', 'ai', 'solana', 'sec', 'binance']
        coverage_score = sum(5 for topic in hot_topics if topic in content)
        score += min(20, coverage_score)
        
        # 4. 传播速度 (15分) - 来源权威性
        trusted_sources = ['coindesk', 'cointelegraph', 'theblock', 'decrypt']
        source = news_item.get('url', '').lower()
        if any(s in source for s in trusted_sources):
            score += 15
        else:
            score += 8
        
        # 5. 情绪强度 (10分) - 强情感词
        emotion_words = ['惊人', 'shocking', '史无前例', 'unprecedented', '重大', 'major']
        emotion_score = sum(3 for word in emotion_words if word in content)
        score += min(10, emotion_score)
        
        return score

    def _match_framework(self, news_item):
        """
        🔥 Step 3-4: 智能框架匹配
        根据新闻类型自动选择最佳分析框架
        """
        # 🔥 FIX: 兼容不同字段名
        title = news_item.get('title') or news_item.get('name') or ''
        content_text = news_item.get('content') or news_item.get('snippet') or news_item.get('description') or ''
        content = (title + ' ' + content_text).lower()
        
        # 关键词 → 框架映射
        framework_keywords = {
            "5W1H": ["突发", "breaking", "刚刚", "just", "最新", "latest"],
            "PEST": ["趋势", "trend", "展望", "outlook", "未来", "future"],
            "MECE": ["分析", "analysis", "深度", "deep dive", "详解"],
            "SWOT": ["人物", "ceo", "创始人", "founder", "项目", "project"],
            "利益相关者": ["政策", "policy", "监管", "regulation", "法案", "law"],
            "波特五力": ["竞争", "competition", "市场", "market", "行业", "industry"],
            "金字塔原理": ["观点", "opinion", "评论", "commentary"],
            "问题树": ["失败", "failure", "崩盘", "crash", "复盘", "post-mortem"],
            "决策矩阵": ["对比", "comparison", "选择", "choice", "vs"],
            "情景分析": ["预测", "prediction", "展望", "forecast", "可能", "potential"]
        }
        
        # 统计每个框架的匹配度
        match_scores = {}
        for framework, keywords in framework_keywords.items():
            match_scores[framework] = sum(1 for kw in keywords if kw in content)
        
        # 选择匹配度最高的框架
        best_framework = max(match_scores.items(), key=lambda x: x[1])[0]
        
        # 如果所有框架得分都是0，默认使用5W1H
        if match_scores[best_framework] == 0:
            best_framework = "5W1H"
        
        return best_framework

    def _collect_evidence(self, topic, news_item):
        """
        🔥 Step 5: 证据收集与严格筛选
        广泛收集正反面证据 → 时效性检查 → 逻辑性验证 → 可靠性评估
        """
        print("📚 Step 5: 收集和筛选证据...")
        
        # 🔥 FIX: 兼容不同字段名
        title = news_item.get('title') or news_item.get('name') or ''
        
        # 1. 广泛收集（正反面）
        try:
            search_query = f"{topic} {title}"
            evidence_pool = self.tavily.search(
                query=search_query,
                search_depth="advanced",
                max_results=10,
                days=3  # 扩大到3天，确保足够证据
            )
            raw_evidence = evidence_pool.get("results", [])
        except Exception as e:
            print(f"⚠️ 证据收集失败: {e}")
            raw_evidence = [news_item]  # 失败时至少用原新闻
        
        # 2. 时效性检查（删除过时信息）
        valid_evidence = []
        for e in raw_evidence:
            # 简单检查：有发布日期且不是太旧
            pub_date = e.get('published_date', '')
            if pub_date or 'http' in e.get('url', ''):
                valid_evidence.append(e)
        
        # 3. 逻辑性验证（粗筛）
        # 这里简化处理，实际应该检查内容相关性
        logical_evidence = valid_evidence[:8]  # 取前8个最相关的
        
        # 4. 可靠性评估（检查来源）
        reliable_evidence = []
        for e in logical_evidence:
            url = e.get('url', '').lower()
            # 优先来自可信源
            is_trusted = any(source in url for source in ['coindesk', 'cointelegraph', 'theblock', 'decrypt', 'reuters', 'bloomberg'])
            if is_trusted or len(reliable_evidence) < 3:  # 确保至少3条
                reliable_evidence.append(e)
        
        print(f"✅ 证据筛选完成: 原始{len(raw_evidence)}条 → 有效{len(valid_evidence)}条 → 可靠{len(reliable_evidence)}条")
        return reliable_evidence

    def _organize_content(self, evidence, framework, news_item):
        """
        🔥 Step 6: 内容组织（金字塔原理）
        按框架结构组织素材，调节节奏，控制篇幅
        """
        print(f"📐 Step 6: 按 {framework} 框架组织内容...")
        
        framework_info = self.frameworks.get(framework, self.frameworks["5W1H"])
        
        # 🔥 FIX: 兼容不同字段名
        title = news_item.get('title') or news_item.get('name') or ''
        content_text = news_item.get('content') or news_item.get('snippet') or news_item.get('description') or ''
        url = news_item.get('url') or ''
        
        # 构建结构化的素材包
        organized = {
            "框架名称": framework_info["name"],
            "结构": framework_info["structure"],
            "主新闻": {
                "标题": title,
                "内容": content_text,
                "来源": url
            },
            "支撑证据": [
                {
                    "标题": e.get('title') or e.get('name') or '',
                    "摘要": (e.get('content') or e.get('snippet') or e.get('description') or '')[:200],
                    "来源": e.get('url') or ''
                }
                for e in evidence[:3]  # 最多3条支撑
            ]
        }
        
        return organized

    def _check_duplication(self, new_topic):
        """
        去重机制：避免短时间内重复讲同一个新闻
        """
        # 🔥 FIX: 处理空标题情况
        if not new_topic or new_topic.strip() == '':
            print("⚠️ 标题为空，跳过去重检查")
            return False
        try:
            if not os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "w") as f:
                    json.dump([{"topic": new_topic, "time": time.time()}], f)
                return False
            
            with open(HISTORY_FILE, "r") as f: 
                history = json.load(f)
            
            # 清理超过5小时的旧记录
            current_time = time.time()
            valid_history = [h for h in history if current_time - h['time'] < 5 * 3600]
            
            # 查重（关键词匹配 + 相似度）
            is_dup = False
            for h in valid_history:
                if h['topic'] in new_topic or new_topic in h['topic']:
                    is_dup = True
                    break
                # 词汇相似度检测
                old_words = set(re.findall(r'\w+', h['topic'].lower()))
                new_words = set(re.findall(r'\w+', new_topic.lower()))
                if len(old_words & new_words) / max(len(new_words), 1) > 0.5:
                    is_dup = True
                    break
            
            # 如果不重复，更新文件
            if not is_dup:
                valid_history.append({"topic": new_topic, "time": current_time})
                with open(HISTORY_FILE, "w") as f: 
                    json.dump(valid_history, f, ensure_ascii=False, indent=2)
                print(f"✅ 新话题已记录: {new_topic[:50]}...")
            else:
                print(f"⚠️ 话题重复，跳过: {new_topic[:50]}...")
            
            return is_dup
        except Exception as e:
            print(f"⚠️ 去重检查失败: {e}")
            return False

    def _clean_text(self, text):
        """
        🔥 强力去废话正则清洗器（扩展版）
        """
        if not text:
            return ""
        
        # 1. 去掉剧本标记
        text = re.sub(r"[\(\[\【<].*?[\)\]\】>]", "", text)
        
        # 2. 去掉 Markdown 格式
        text = text.replace("*", "").replace("#", "").replace("`", "")
        text = text.replace("_", "").replace("~", "")
        
        # 3. 去掉 AI 习惯性废话（扩展列表）
        bad_phrases = [
            "好的大漂亮", "没问题", "好的", "综上所述", "总之", "总而言之",
            "主持人", "Let's go", "各位听众", "大家好", "观众朋友们",
            "接下来", "那么", "首先", "其次", "最后", "然后",
            "值得注意的是", "需要指出的是", "我们可以看到", "可以发现",
            "根据以上分析", "通过分析", "综合来看",
            "音效", "背景音乐", "掌声", "笑声",
            "我选择", "我认为", "我觉得", "让我们",
            "欢迎收听", "感谢收看", "下期再见"
        ]
        for phrase in bad_phrases:
            text = text.replace(phrase, "")
        
        # 4. 去除不适合朗读的标点符号
        text = re.sub(r'["""''「」『』（）\(\)\[\]【】《》<>]', '', text)
        
        # 5. 规范化标点
        text = re.sub(r'[，,]{2,}', '，', text)
        text = re.sub(r'[。.]{2,}', '。', text)
        text = re.sub(r'[！!]{2,}', '！', text)
        text = re.sub(r'[？?]{2,}', '？', text)
        
        # 6. 去除多余空行
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        # 7. 去除行首序号
        text = re.sub(r'^\s*[\d一二三四五六七八九十]+[、\.\s]+', '', text, flags=re.MULTILINE)
        
        return text.strip()

    def _quality_check(self, draft):
        """
        🔥 Step 7: 质量审核（四重检查）
        检查语义重复、逻辑漏洞、事实准确、时间正确
        """
        print("🔍 Step 7: 质量审核...")
        
        issues = []
        char_count = len(draft)
        
        # 1. 语义重复检查（简单版）
        sentences = re.split(r'[。！？]', draft)
        unique_sentences = set(sentences)
        if len(sentences) - len(unique_sentences) > 3:
            issues.append("检测到较多重复句子")
        
        # 2. 字数检查（更严格的标准）
        print(f"📊 当前字数: {char_count} 字")
        if char_count < 800:
            issues.append(f"内容过短（{char_count}字），目标至少1500字")
        elif char_count >= 800 and char_count < 1200:
            print(f"⚠️ 字数偏少（{char_count}字），理想值1500-2500字")
        elif char_count > 3500:
            issues.append(f"内容过长（{char_count}字），建议控制在2500字以内")
        else:
            print(f"✅ 字数合格（{char_count}字）")
        
        # 3. 检查是否有实质内容
        if "分析" not in draft and "影响" not in draft and "原因" not in draft:
            issues.append("缺少深度分析")
        
        if issues:
            print(f"⚠️ 发现问题: {', '.join(issues)}")
            return False, issues
        else:
            print("✅ 质量审核通过")
            return True, []

    def fetch_news_and_analyze(self):
        """
        🔥 10步专业工作流程（主流程）
        """
        if not self.tavily: 
            return None, "缺少 Tavily Key", False
        
        print("\n" + "="*50)
        print("🎙️ 加密大漂亮 - 10步专业内容生产流程")
        print("="*50)
        
        # Step 1-2: 实时热点追踪与筛选
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"\n📡 Step 1-2: 追踪热点并筛选爆火话题 ({today_str})")
        
        domain_list = [d.strip() for d in self.target_domains.split(",") if d.strip()]
        
        try:
            response = self.tavily.search(
                query=f"crypto blockchain {self.topic} breaking news {today_str}",
                search_depth="advanced",
                include_domains=domain_list if domain_list else None,
                max_results=15,  # 增加到15条，方便筛选
                days=1
            )
            results = response.get("results", [])
            print(f"✅ 搜索到 {len(results)} 条候选新闻")
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return None, f"搜索失败: {e}", False

        # 计算爆火潜力并排序
        scored_results = []
        for item in results:
            score = self._calculate_viral_potential(item)
            scored_results.append((score, item))
        
        scored_results.sort(reverse=True, key=lambda x: x[0])
        print(f"📊 爆火潜力排序完成，Top1得分: {scored_results[0][0] if scored_results else 0}")
        
        # 筛选未讲过的新闻
        selected_news = None
        selected_framework = None
        
        for score, item in scored_results:
            # 🔥 FIX: 兼容不同字段名
            title = item.get('title') or item.get('name') or ''
            if not title:
                print("⚠️ 发现无标题新闻，跳过")
                continue
                
            if not self._check_duplication(title):
                selected_news = item
                # Step 3-4: 智能框架匹配
                selected_framework = self._match_framework(item)
                print(f"✅ 选中头条: {title[:50]}...")
                print(f"🎯 Step 3-4: 匹配框架 → {selected_framework} ({self.frameworks[selected_framework]['name']})")
                break
        
        # 没新闻 → 启用 CMS 备用库
        if not selected_news:
            print("⚠️ 无最新高价值新闻或都已讲过，启用备用话题库...")
            import random
            backup = random.choice(self.backup_topics) if self.backup_topics else "比特币去中心化精神科普"
            print(f"📚 使用备用话题: {backup}")
            return backup, None, True

        # Step 5: 证据收集与筛选
        evidence = self._collect_evidence(self.topic, selected_news)
        
        # Step 6: 内容组织
        organized_content = self._organize_content(evidence, selected_framework, selected_news)
        
        # Step 8-10: AI 生成文案
        print("\n🧠 Step 8-10: AI深度撰写与优化...")
        
        framework_info = self.frameworks[selected_framework]
        
        # 🔥 FIX: 兼容不同字段名
        title = selected_news.get('title') or selected_news.get('name') or ''
        content_text = selected_news.get('content') or selected_news.get('snippet') or selected_news.get('description') or ''
        url = selected_news.get('url') or ''
        
        # 🔥 核心 Prompt - 10步专业流程版
        prompt = f"""
{self.persona}

【分析任务】
你正在使用 **{framework_info['name']}** 进行深度分析。

框架结构: {framework_info['structure']}

【原始新闻】
标题：{title}
内容：{content_text}
来源：{url}

【支撑证据】
{chr(10).join([f"- {e['标题']}" for e in organized_content['支撑证据']])}

【创作要求 - 严格执行】

1. **框架应用**：
   - 严格按照 {selected_framework} 框架的结构展开
   - 每个环节都要有实质性分析，不是简单罗列
   - 逻辑链条要完整，环环相扣

2. **深度挖掘**：
   - 不能只复述新闻，必须有独到见解
   - 挖掘背后的深层原因和影响
   - 提出有价值的预测或建议
   - 每个分析点至少展开3-5句话，不要一笔带过
   - 用具体案例和数据支撑你的观点

3. **口语化表达**：
   - 句子要短，平均15字以内
   - 像和朋友聊天一样自然
   - 适合女性主持人的语气
   - 带点幽默和个性

4. **内容控制**：
   - 字数：1500-2500字（目标8-15分钟播报时长）
   - 节奏：有快有慢，有重点有展开
   - 结构：清晰的开头、中间、结尾
   - 深度：充分展开每个分析点，不要简略概括

5. **严禁事项**：
   - 不要输出"我选择了XX框架"等元语言
   - 不要用"好的""没问题""综上所述"
   - 不要出现(音效)、[动作]等剧本标记
   - 不要用引号、括号等不适合朗读的符号
   - 只用逗号、句号、问号、感叹号

6. **语气风格**：
   - 专业但不死板
   - 犀利但不偏激
   - 知性但不高冷
   - 有观点有态度

⚠️ **重要提醒**：
- 目标字数：1500-2500字（约8-15分钟播报时长）
- 如果字数不足1500字，将被退回重写
- 充分展开分析，不要简略概括
- 每个论点都要有足够的论证支撑

🔴 **严格字数要求 - 必须遵守！**：
- 最少1500字，理想2000字以上
- 每个框架环节至少200-300字
- 不要写成简短的新闻稿，要写成深度分析长文
- 参考示例：一个完整的分析应该像一篇深度报道文章

💡 **如何达到字数要求**：
1. 每个论点都要有：观点陈述 + 事实支撑 + 数据引用 + 影响分析
2. 多用具体例子：不要说"会有影响"，要说"具体会对XX市场造成XX影响，预计XX"
3. 展开时间线：不要只说"发生了"，要说"何时开始、如何发展、现在状况、未来走向"
4. 多角度分析：从投资者、监管者、行业参与者等多个视角分析

现在开始创作，直接输出文案正文（记住：至少1500字！）：
"""
        
        try:
            # 🔥 多次尝试机制：确保生成高质量长内容
            max_attempts = 3
            best_script = None
            best_char_count = 0
            
            for attempt in range(max_attempts):
                print(f"🎨 第 {attempt + 1} 次生成..." if attempt > 0 else "🎨 开始生成内容...")
                
                # 根据尝试次数调整 prompt
                if attempt == 0:
                    current_prompt = prompt
                elif attempt == 1:
                    # 第二次：强调字数要求
                    current_prompt = prompt.replace(
                        "现在开始创作，直接输出文案正文（记住：至少1500字！）：",
                        "🚨🚨🚨 上一次生成失败：字数严重不足！🚨🚨🚨\n\n" +
                        "第二次尝试 - 必须满足以下要求：\n" +
                        "1. 最少1500字，目标2000字以上\n" +
                        "2. 每个框架环节详细展开，至少5-8句话\n" +
                        "3. 不要写简短概括，要写深度长文\n" +
                        "4. 多用具体数据、案例、时间线\n\n" +
                        "现在开始创作，输出至少1500字的完整分析："
                    )
                else:
                    # 第三次：最严厉警告
                    current_prompt = prompt.replace(
                        "现在开始创作，直接输出文案正文（记住：至少1500字！）：",
                        "🔥🔥🔥 最后机会！前两次都失败了！🔥🔥🔥\n\n" +
                        "第三次尝试 - 终极要求：\n" +
                        "📝 必须生成至少1500字的深度分析文章\n" +
                        "📝 每个论点展开至少300字\n" +
                        "📝 像写论文一样详细、像报道一样深入\n" +
                        "📝 不要简略、不要概括、不要省略\n\n" +
                        "示例长度参考：\n" +
                        "- 开头引入：200-300字\n" +
                        "- 每个框架环节：300-400字 × 4-5个环节 = 1200-2000字\n" +
                        "- 结尾总结：200-300字\n" +
                        "总计：1500-2500字\n\n" +
                        "立即开始创作完整的深度分析长文："
                    )
                
                raw_script = self.llm.invoke(current_prompt).content
                print(f"📝 原始生成字数: {len(raw_script)} 字")
                
                clean_script = self._clean_text(raw_script)
                print(f"🧹 清洗后字数: {len(clean_script)} 字")
                
                # 🔥 如果清洗后损失超过30%，使用原始版本
                if len(clean_script) < len(raw_script) * 0.7:
                    print(f"⚠️ 清洗损失过多（{100 - len(clean_script)/len(raw_script)*100:.1f}%），使用原始文本")
                    clean_script = raw_script
                
                # 记录最佳结果
                if len(clean_script) > best_char_count:
                    best_script = clean_script
                    best_char_count = len(clean_script)
                
                # Step 7: 质量审核
                passed, issues = self._quality_check(clean_script)
                
                if passed:
                    print(f"✅ 文案生成完成，共 {len(clean_script)} 字")
                    print("="*50 + "\n")
                    return clean_script, None, False
                else:
                    print(f"❌ 第 {attempt + 1} 次生成未通过审核: {', '.join(issues)}")
                    if attempt < max_attempts - 1:
                        print(f"🔄 将进行第 {attempt + 2} 次尝试...")
            
            # 如果所有尝试都失败，返回最佳结果
            print(f"⚠️ {max_attempts} 次尝试后，使用最佳结果（{best_char_count}字）")
            print("="*50 + "\n")
            return best_script if best_script else clean_script, None, False
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return None, f"生成失败: {e}", False
