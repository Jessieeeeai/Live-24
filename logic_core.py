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
        self.recent_frameworks = []  # 🔥 v2.2: 最近使用的框架历史（框架多样性检查）
        self.topic_outlines = {}  # 🔥 v2.2: 话题大纲缓存
        
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
        
        # 3. 🔥 定义30种深度分析框架 (v2.2扩展版)
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
            },
            # 🔥 新增20种框架 (v2.2)
            "价值链分析": {
                "name": "产业价值框架",
                "structure": "上游供应→核心生产→下游分销→服务支持→价值创造→利润分配",
                "适用": ["产业链分析", "商业模式", "成本结构"]
            },
            "技术成熟度曲线": {
                "name": "技术创新框架",
                "structure": "技术触发→期望膨胀→幻灭低谷→复苏爬升→成熟稳定",
                "适用": ["新技术评估", "创新分析", "投资时机"]
            },
            "商业画布": {
                "name": "商业模式框架",
                "structure": "客户细分→价值主张→渠道通路→客户关系→收入来源→核心资源→关键活动→合作伙伴→成本结构",
                "适用": ["创业项目", "商业模式", "战略转型"]
            },
            "冲突矩阵": {
                "name": "争议对立框架",
                "structure": "正方观点→反方观点→核心冲突→利益分歧→妥协空间→解决路径",
                "适用": ["争议话题", "对立观点", "冲突分析"]
            },
            "路径依赖": {
                "name": "历史演进框架",
                "structure": "初始选择→路径锁定→强化机制→转型障碍→突破可能",
                "适用": ["制度分析", "行业惯性", "变革难题"]
            },
            "网络效应": {
                "name": "平台生态框架",
                "structure": "用户增长→价值提升→网络密度→临界规模→赢家通吃",
                "适用": ["平台经济", "社交网络", "双边市场"]
            },
            "破窗效应": {
                "name": "社会心理框架",
                "structure": "初始信号→心理暗示→行为扩散→规范崩溃→系统失序",
                "适用": ["社会现象", "群体行为", "管理问题"]
            },
            "黑天鹅事件": {
                "name": "极端风险框架",
                "structure": "常态假设→异常出现→冲击分析→连锁反应→应对策略",
                "适用": ["突发危机", "系统风险", "尾部事件"]
            },
            "长尾理论": {
                "name": "市场分布框架",
                "structure": "头部集中→尾部分散→利基市场→规模效应→总量对比",
                "适用": ["市场细分", "小众需求", "互联网经济"]
            },
            "二八定律": {
                "name": "资源集中框架",
                "structure": "核心20%→贡献80%→资源配置→优先级排序→效率优化",
                "适用": ["资源分配", "效率分析", "重点突破"]
            },
            "马斯洛需求": {
                "name": "用户需求框架",
                "structure": "生理需求→安全需求→社交需求→尊重需求→自我实现",
                "适用": ["用户分析", "产品设计", "消费行为"]
            },
            "创新扩散": {
                "name": "传播采纳框架",
                "structure": "创新者→早期采纳→早期大众→晚期大众→落后者",
                "适用": ["产品推广", "市场渗透", "用户增长"]
            },
            "囚徒困境": {
                "name": "博弈论框架",
                "structure": "个体理性→集体困境→信任缺失→合作障碍→制度设计",
                "适用": ["竞争策略", "合作问题", "制度分析"]
            },
            "零和博弈": {
                "name": "竞争对抗框架",
                "structure": "双方对立→利益互斥→策略博弈→均衡点→输赢分析",
                "适用": ["竞争关系", "资源争夺", "政治斗争"]
            },
            "飞轮效应": {
                "name": "增长循环框架",
                "structure": "初始投入→小步积累→动能增强→加速增长→自我强化",
                "适用": ["企业增长", "复利效应", "战略执行"]
            },
            "跨越鸿沟": {
                "name": "市场跨越框架",
                "structure": "早期市场→鸿沟障碍→主流市场→跨越策略→规模化",
                "适用": ["产品市场化", "增长瓶颈", "战略转型"]
            },
            "护城河理论": {
                "name": "竞争优势框架",
                "structure": "规模优势→成本优势→品牌优势→网络效应→转换成本",
                "适用": ["竞争分析", "投资研究", "战略定位"]
            },
            "定位理论": {
                "name": "品牌定位框架",
                "structure": "心智资源→竞争位置→差异化→聚焦策略→品牌认知",
                "适用": ["品牌战略", "市场定位", "营销策略"]
            },
            "双因素理论": {
                "name": "动机激励框架",
                "structure": "保健因素→激励因素→满意度→不满意度→综合效应",
                "适用": ["人才管理", "激励机制", "组织行为"]
            },
            "临界点理论": {
                "name": "拐点突变框架",
                "structure": "渐进累积→临界阈值→突变跃迁→新均衡→不可逆性",
                "适用": ["趋势预判", "社会变革", "市场转折"]
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
        🔥 强力去废话正则清洗器（扩展版 + 防止TTS读出格式标记 + 去除框架元信息）
        """
        if not text:
            return ""
        
        # 0.1 🔥🔥 最高优先级：去除文章开头的框架名称和元信息
        framework_patterns = [
            r'^.*?5W1H.*?[:：\n]',
            r'^.*?PEST.*?[:：\n]',
            r'^.*?SWOT.*?[:：\n]',
            r'^.*?MECE.*?[:：\n]',
            r'^.*?框架.*?[:：\n]',
            r'^.*?分析.*?[:：\n]',
            r'^.*?波特五力.*?[:：\n]',
            r'^.*?金字塔原理.*?[:：\n]',
            r'^.*?利益相关者.*?[:：\n]',
            r'^.*?问题树.*?[:：\n]',
            r'^.*?决策矩阵.*?[:：\n]',
            r'^.*?情景分析.*?[:：\n]',
            r'^【.*?】',  # Remove content in 【】brackets at start
            r'^\s*我选择了.*?[:：。\n]',
            r'^\s*使用.*?框架.*?[:：。\n]',
            r'^\s*采用.*?分析.*?[:：。\n]',
        ]
        for pattern in framework_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # 0.2 🔥 找到第一个中文字符，从那里开始（去除开头的英文字母和数字）
        match = re.search(r'[\u4e00-\u9fff]', text)
        if match:
            first_chinese_pos = match.start()
            # 检查第一个中文字符之前是否全是英文字母、数字、符号
            before_chinese = text[:first_chinese_pos].strip()
            if before_chinese and re.match(r'^[a-zA-Z0-9\s\.\-_:#\[\]【】\(\)（）]+$', before_chinese):
                # 如果开头部分没有实质内容，就从第一个中文字符开始
                text = text[first_chinese_pos:]
        
        # 0.3 🔥 最优先：去除行首的数字序号和字母标记（防止TTS朗读）
        text = re.sub(r'^\s*[\da-zA-Z]+[\.\)、：:]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[一二三四五六七八九十百千]+[\.\)、：:]\s*', '', text, flags=re.MULTILINE)
        
        # 1. 去掉剧本标记和括号内容
        text = re.sub(r"[\(\[\【<].*?[\)\]\】>]", "", text)
        
        # 2. 去掉 Markdown 格式标记
        text = text.replace("*", "").replace("#", "").replace("`", "")
        text = text.replace("_", "").replace("~", "").replace("-", "")
        
        # 2.5 🔥 去除常见的结构标记和框架名称
        structure_markers = [
            "标题：", "引言：", "背景：", "分析：", "结论：",
            "正文：", "开头：", "结尾：", "摘要：", "导语：",
            "第一部分", "第二部分", "第三部分", "第四部分",
            "Step 1", "Step 2", "Step 3", "Step 4", "Step 5",
            "5W1H框架", "PEST框架", "SWOT框架", "MECE框架",
            "波特五力", "金字塔原理", "利益相关者", "问题树", "决策矩阵", "情景分析",
            "我选择", "使用框架", "采用分析", "基于框架",
            "一、", "二、", "三、", "四、", "五、",
            "1、", "2、", "3、", "4、", "5、"
        ]
        for marker in structure_markers:
            text = text.replace(marker, "")
        
        # 3. 去掉 AI 习惯性废话（扩展列表 + 框架元语言）
        bad_phrases = [
            "好的大漂亮", "没问题", "好的", "综上所述", "总之", "总而言之",
            "主持人", "Let's go", "各位听众", "大家好", "观众朋友们",
            "接下来", "那么", "首先", "其次", "最后", "然后",
            "值得注意的是", "需要指出的是", "我们可以看到", "可以发现",
            "根据以上分析", "通过分析", "综合来看",
            "音效", "背景音乐", "掌声", "笑声",
            "我选择", "我认为", "我觉得", "让我们",
            "欢迎收听", "感谢收看", "下期再见",
            "我选择了", "我们选择", "我们使用", "我们采用",
            "使用了", "采用了", "应用了", "基于",
            "框架进行分析", "框架来分析", "分析框架"
        ]
        for phrase in bad_phrases:
            text = text.replace(phrase, "")
        
        # 4. 去除不适合朗读的标点符号
        text = re.sub(r'["""''「」『』（）()【】《》<>\[\]]', '', text)  # noqa: W605
        
        # 5. 规范化标点
        text = re.sub(r'[，,]{2,}', '，', text)
        text = re.sub(r'[。.]{2,}', '。', text)
        text = re.sub(r'[！!]{2,}', '！', text)
        text = re.sub(r'[？?]{2,}', '？', text)
        
        # 6. 去除多余空行和首尾空格
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        # 7. 🔥 再次去除可能残留的序号（更激进）
        text = re.sub(r'^\s*[\d一二三四五六七八九十]+[、\.\s]+', '', text, flags=re.MULTILINE)
        text = re.sub(r'[a-zA-Z]{1,2}\.\s', '', text)  # 去除 "a. " "A. " 等
        
        # 8. 🔥 去除行首的冒号（如果单独出现）
        text = re.sub(r'^[:：]\s*', '', text, flags=re.MULTILINE)
        
        # 9. 🔥🔥 最终检查：如果开头仍有非中文内容（英文单词/数字），强制从第一句话开始
        lines = text.split('\n')
        cleaned_lines = []
        found_real_content = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 如果还没找到真正的内容，检查这一行
            if not found_real_content:
                # 如果这行以中文开头，且不包含框架关键词，认为是真正的内容
                if re.match(r'^[\u4e00-\u9fff]', line):
                    # 检查是否包含框架关键词
                    framework_keywords = ['框架', '5W1H', 'PEST', 'SWOT', 'MECE', '波特五力', 
                                        '金字塔', '利益相关者', '问题树', '决策矩阵', '情景分析',
                                        '我选择', '使用', '采用', '基于']
                    if not any(keyword in line for keyword in framework_keywords):
                        found_real_content = True
                        cleaned_lines.append(line)
                # 否则跳过这行（可能是元信息）
            else:
                # 已经找到真正的内容后，保留所有行
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        return text.strip()

    def _check_semantic_duplication(self, title, threshold=0.6, time_window_hours=24):
        """
        🔥 v2.2 - Step 4: 语义去重检查（60%相似度阈值）
        基于语义相似度，而非简单关键词匹配
        """
        if not os.path.exists(HISTORY_FILE):
            return False  # 无历史，不重复
        
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            return False
        
        # 时间窗口过滤（24小时内）
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_topics = [h for h in history if h.get('timestamp', 0) > cutoff_time]
        
        if not recent_topics:
            return False
        
        # 简化的语义相似度检查（基于词汇重叠）
        title_words = set(title.lower().split())
        for topic in recent_topics:
            old_title = topic.get('topic', '')
            old_words = set(old_title.lower().split())
            
            # 计算Jaccard相似度
            if len(title_words) == 0 or len(old_words) == 0:
                continue
            
            intersection = len(title_words & old_words)
            union = len(title_words | old_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                print(f"⚠️ 去重检测：与 '{old_title[:30]}...' 相似度 {similarity:.1%}（阈值{threshold:.0%}）")
                return True
        
        return False
    
    def _check_framework_diversity(self, current_framework):
        """
        🔥 v2.2 - Step 6: 框架多样性检查
        确保不重复使用同一框架，增加内容多样性
        """
        if current_framework in self.recent_frameworks[-2:]:  # 最近2次
            print(f"⚠️ 框架多样性：{current_framework} 最近使用过，建议更换")
            # 找到下一个可用框架
            for fw in self.frameworks.keys():
                if fw not in self.recent_frameworks[-3:]:
                    print(f"✅ 切换到: {fw}")
                    return fw
        
        # 记录使用历史（最多保留10个）
        self.recent_frameworks.append(current_framework)
        if len(self.recent_frameworks) > 10:
            self.recent_frameworks.pop(0)
        
        return current_framework
    
    def _design_outline(self, topic, framework, news_item):
        """
        🔥 v2.2 - Step 7: 设计文章大纲
        在撰写前先规划结构，确保内容充实
        """
        print("📝 Step 7: 设计内容大纲...")
        
        framework_structure = self.frameworks[framework]['structure']
        sections = framework_structure.split('→')
        
        outline = {
            '引言': {'target_chars': 250, 'desc': '简要介绍事件背景，吸引听众注意'},
            '主体': [],
            '结论': {'target_chars': 250, 'desc': '总结分析，给出观点或预测'}
        }
        
        # 为每个框架环节设计子章节
        for i, section in enumerate(sections):
            outline['主体'].append({
                'section': section,
                'target_chars': 300,  # 每环节目标300字
                'desc': f'详细分析{section}，包含事实、数据、案例'
            })
        
        total_target = 250 + (len(sections) * 300) + 250
        print(f"📊 大纲设计完成：引言(250字) + {len(sections)}个环节({len(sections)*300}字) + 结论(250字) = 约{total_target}字")
        
        self.topic_outlines[topic] = outline
        return outline
    
    def _verify_evidence_timeline(self, evidence_list):
        """
        🔥 v2.2 - Step 11: 验证证据时间线
        确保素材时效性，标记过期内容
        """
        print("⏱️ Step 11: 验证证据时间线...")
        
        verified = []
        outdated = []
        
        for e in evidence_list:
            pub_date = e.get('published_date', '')
            title = e.get('标题') or e.get('title') or e.get('name') or ''
            
            # 简单时效性检查
            is_recent = False
            if pub_date:
                # 如果包含 today, 最近日期等
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                
                if today in pub_date or yesterday in pub_date or 'today' in pub_date.lower():
                    is_recent = True
            
            if is_recent or not pub_date:  # 无日期的保留（可能是最新）
                verified.append(e)
            else:
                outdated.append(title[:30] + '...')
        
        if outdated:
            print(f"⚠️ 发现过时素材 {len(outdated)} 条：{', '.join(outdated[:3])}")
        
        print(f"✅ 保留时效性证据 {len(verified)}/{len(evidence_list)} 条")
        return verified
    
    def _polish_and_audit(self, draft, requirements):
        """
        🔥 v2.2 - Step 14: 润色和审核优化
        后处理：检查并修正质量问题
        """
        print("🔍 Step 14: 润色和审核优化...")
        
        issues = []
        
        # 1. 字数检查
        char_count = len(draft)
        if char_count < 1200:
            issues.append(f"内容偏短（{char_count}字），建议扩充至1500字以上")
        
        # 2. 结构完整性检查
        has_opening = any(word in draft[:200] for word in ['今天', '最近', '这几天', '就在'])
        has_conclusion = any(word in draft[-200:] for word in ['总之', '总的来说', '未来', '预计', '综合'])
        
        if not has_opening:
            issues.append("缺少引入性开场")
        if not has_conclusion:
            issues.append("缺少总结性结论")
        
        # 3. 深度分析检查
        analysis_keywords = ['因为', '原因', '影响', '导致', '意味着', '预计', '分析']
        analysis_count = sum(1 for keyword in analysis_keywords if keyword in draft)
        
        if analysis_count < 5:
            issues.append(f"深度分析不足（仅{analysis_count}处分析词），建议增加因果分析")
        
        if issues:
            print(f"⚠️ 发现 {len(issues)} 个可优化点:")
            for issue in issues:
                print(f"  - {issue}")
            return draft, issues
        else:
            print("✅ 审核通过，内容质量良好")
            return draft, []

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
        🔥 v2.2 - 15步专业工作流程（完整版）
        """
        if not self.tavily: 
            return None, "缺少 Tavily Key", False
        
        print("\n" + "="*60)
        print("🎙️ 加密大漂亮 - 15步专业内容生产流程 v2.2")
        print("="*60)
        
        # 🔥 Step 1: 确认当前准确时间
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        weekday_cn = ['一', '二', '三', '四', '五', '六', '日'][now.weekday()]
        
        print(f"\n⏰ Step 1: 确认当前时间")
        print(f"📅 今天是 {now.year}年{now.month}月{now.day}日 星期{weekday_cn} {time_str}")
        print(f"🌐 时区: UTC+8 (北京时间)")
        
        # 🔥 Step 2: 了解频道定位和历史数据
        print(f"\n📊 Step 2: 频道定位分析")
        print(f"📌 频道主题: {self.topic}")
        print(f"🎯 人设定位: 专业加密货币分析师")
        print(f"📚 框架库: {len(self.frameworks)} 种分析框架")
        print(f"🔄 最近使用框架: {', '.join(self.recent_frameworks[-3:]) if self.recent_frameworks else '无'}")
        
        # 🔥 Step 3: 实时追踪热点
        print(f"\n🔍 Step 3: 实时热点追踪 ({today_str})")
        
        domain_list = [d.strip() for d in self.target_domains.split(",") if d.strip()]
        
        try:
            # 增强搜索查询，包含明确的时间上下文
            response = self.tavily.search(
                query=f"crypto blockchain {self.topic} latest breaking news {today_str} today",
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
        
        # 🔥 Step 4: 选题去重检查（60%语义相似度阈值）
        print(f"\n🚫 Step 4: 选题去重检查（24小时内，60%阈值）")
        
        for score, item in scored_results:
            # 🔥 FIX: 兼容不同字段名
            title = item.get('title') or item.get('name') or ''
            if not title:
                print("⚠️ 发现无标题新闻，跳过")
                continue
            
            # 使用新的语义去重检查
            is_duplicate = self._check_semantic_duplication(title, threshold=0.6, time_window_hours=24)
            
            if not is_duplicate and not self._check_duplication(title):
                selected_news = item
                
                # 🔥 Step 5: 智能匹配分析框架
                print(f"\n📈 Step 5: 智能框架匹配")
                selected_framework = self._match_framework(item)
                print(f"🎯 初步匹配 → {selected_framework} ({self.frameworks[selected_framework]['name']})")
                
                # 🔥 Step 6: 框架多样性检查
                print(f"\n🔄 Step 6: 框架多样性检查")
                selected_framework = self._check_framework_diversity(selected_framework)
                
                print(f"✅ 选中头条: {title[:50]}...")
                print(f"✅ 最终框架: {selected_framework} ({self.frameworks[selected_framework]['name']})")
                break
            else:
                print(f"⏭️ 跳过重复话题: {title[:40]}...")
        
        # 没新闻 → 启用 CMS 备用库
        if not selected_news:
            print("⚠️ 无最新高价值新闻或都已讲过，启用备用话题库...")
            import random
            backup = random.choice(self.backup_topics) if self.backup_topics else "比特币去中心化精神科普"
            print(f"📚 使用备用话题: {backup}")
            return backup, None, True

        # 🔥 Step 7: 设计文章大纲
        title = selected_news.get('title') or selected_news.get('name') or ''
        outline = self._design_outline(title, selected_framework, selected_news)
        
        # 🔥 Step 8: 广泛收集证据素材
        print(f"\n📚 Step 8: 广泛收集证据素材")
        evidence = self._collect_evidence(self.topic, selected_news)
        
        # 🔥 Step 9: 严格筛选素材（已在_collect_evidence中实现）
        print(f"\n⚡ Step 9: 严格筛选素材（完成）")
        
        # 🔥 Step 10: 按框架组织素材
        print(f"\n📖 Step 10: 按框架组织素材")
        organized_content = self._organize_content(evidence, selected_framework, selected_news)
        
        # 🔥 Step 11: 验证素材时间线
        all_evidence = organized_content.get('支撑证据', []) + organized_content.get('反驳证据', [])
        verified_evidence = self._verify_evidence_timeline(all_evidence)
        organized_content['支撑证据'] = [e for e in organized_content['支撑证据'] if e in verified_evidence]
        
        # 🔥 Step 13: 撰写文案（原Step 8-10）
        print("\n✍️ Step 13: AI深度撰写文案...")
        
        framework_info = self.frameworks[selected_framework]
        
        # 🔥 FIX: 兼容不同字段名
        title = selected_news.get('title') or selected_news.get('name') or ''
        content_text = selected_news.get('content') or selected_news.get('snippet') or selected_news.get('description') or ''
        url = selected_news.get('url') or ''
        
        # 🔥 核心 Prompt - v2.2 15步专业流程版（增强时间上下文）
        prompt = f"""
{self.persona}

⏰ **当前时间上下文**：
今天是 {now.year}年{now.month}月{now.day}日 星期{weekday_cn} {time_str}
时区：UTC+8 (北京时间)

重要：你的分析必须基于最新时间，使用"今天"、"最近"、"刚刚"等词时要准确。

【分析任务】
你正在使用 **{framework_info['name']}** 进行深度分析。

【内容大纲】（严格遵循）
{chr(10).join([f"- 引言：{outline['引言']['desc']} ({outline['引言']['target_chars']}字)"] + 
              [f"- {s['section']}：{s['desc']} ({s['target_chars']}字)" for s in outline['主体']] +
              [f"- 结论：{outline['结论']['desc']} ({outline['结论']['target_chars']}字)"])}

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
   - 🚫 不要输出任何框架名称、元信息、分析说明
   - 🚫 不要输出"我选择了XX框架""使用XX分析"等元语言
   - 🚫 不要输出序号、标题、章节号（如"一、""1.""第一部分"）
   - 🚫 不要输出任何英文字母、数字编号、代码、标记
   - 🚫 不要用"好的""没问题""综上所述"等废话
   - 🚫 不要出现(音效)、[动作]、【说明】等剧本标记
   - 🚫 不要用引号、括号、书名号等不适合朗读的符号
   - ✅ 只用逗号、句号、问号、感叹号
   - ✅ 直接开始讲故事，像播音员一样自然流畅

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

🎙️ **最终输出格式要求**：
- 直接输出播音稿，第一个字就是正文内容
- 不要任何标题、序号、章节、框架说明
- 不要任何英文、数字标记、代码格式
- 像新闻主播一样，直接开始讲述
- 流畅自然，听众能直接理解

示例开头（正确）：
"比特币价格今天突破五万美元大关，这是继去年十一月以来的首次突破..."

示例开头（错误）：
"❌ 一、事件概述 ❌"
"❌ 【5W1H框架分析】 ❌"
"❌ 1. Background ❌"

现在开始创作，直接输出纯文案正文（至少1500字，无任何标记）：
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
                
                # 🔥 Step 14: 润色和审核优化
                polished_script, polish_issues = self._polish_and_audit(clean_script, outline)
                
                # 基础质量审核
                passed, basic_issues = self._quality_check(polished_script)
                
                # 🔥 Step 15: 审核有问题，就修改问题
                if passed and not polish_issues:
                    print(f"\n✅ Step 15: 内容审核通过！")
                    print(f"📊 最终字数: {len(polished_script)} 字")
                    print(f"⏱️ 预计播报时长: {len(polished_script)/3:.1f} 秒 ({len(polished_script)/3/60:.1f} 分钟)")
                    print("="*60 + "\n")
                    return polished_script, None, False
                else:
                    all_issues = basic_issues + polish_issues
                    print(f"\n⚠️ Step 15: 发现问题需要修正")
                    print(f"❌ 第 {attempt + 1} 次生成未通过审核: {', '.join(all_issues)}")
                    if attempt < max_attempts - 1:
                        print(f"🔄 将进行第 {attempt + 2} 次尝试，针对性改进...")
                    
                    # 更新最佳结果
                    if len(polished_script) > best_char_count:
                        best_script = polished_script
                        best_char_count = len(polished_script)
            
            # 如果所有尝试都失败，返回最佳结果
            print(f"\n⚠️ {max_attempts} 次尝试后，使用最佳结果（{best_char_count}字）")
            print("="*60 + "\n")
            return best_script if best_script else clean_script, None, False
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return None, f"生成失败: {e}", False
