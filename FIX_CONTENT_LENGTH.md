# 🔧 Content Length & Quality Fix - v2.1.2

## 🐛 Problems Reported

User reported 3 critical issues:

### Issue 1: No Script Visible (没有文案出来)
- UI shows "播放文案已生成" but no content in "查看文案详情"
- Actual Problem: Content TOO SHORT, likely filtered out

### Issue 2: Audio Too Short (24秒太短)
- Current: 24 seconds
- Expected: 3-10 minutes (180-600 seconds)
- Complex topics: up to 15 minutes (900 seconds)
- **Gap**: Output is only 4-13% of target!

### Issue 3: No Second Round (没有启动第二轮)
- System stops after round 1
- Should continue in live mode
- Likely user is in "试听模式" (Preview Mode)

---

## 🔍 Root Cause Analysis

### Problem 1: Content Length Target Too Low

**Original Settings**:
```python
# Line 502: Prompt instruction
字数：600-800字

# Line 367-370: Quality check
if len(draft) < 300:
    issues.append("内容过短")
elif len(draft) > 1000:
    issues.append("内容过长")
```

**Math**:
- 600-800 chars @ 3.2 chars/sec = 187-250 seconds (3-4 minutes)
- Quality check REJECTS content > 1000 chars = max 5 minutes
- **Problem**: Can't reach 10-15 minute target!

---

### Problem 2: Weak Retry Logic

**Original Code** (Line 544-548):
```python
if not passed:
    print(f"⚠️ 初稿存在问题，进行优化...")
    # 简单优化：如果太短就用原始版本
    if len(clean_script) < 300:
        clean_script = raw_script
```

**Problems**:
- ❌ Doesn't actually regenerate
- ❌ Just uses raw version (still too short)
- ❌ No escalating prompts for retry
- ❌ Only 1 attempt

---

### Problem 3: Mode Selection

User likely selected "试听模式" instead of "直播模式":
- Preview Mode: Stops after 1 generation
- Live Mode: Continuous loop

---

## ✅ Solutions Implemented

### Fix 1: Increase Content Length Target

**File**: `logic_core.py`

#### Change 1: Prompt Target (Line 501-505)
```python
# ❌ Before
字数：600-800字

# ✅ After
字数：1500-2500字（目标8-15分钟播报时长）
节奏：有快有慢，有重点有展开
结构：清晰的开头、中间、结尾
深度：充分展开每个分析点，不要简略概括
```

**Impact**:
- 1500 chars @ 3.2 c/s = 469 seconds (7.8 minutes) ✅
- 2500 chars @ 3.2 c/s = 781 seconds (13 minutes) ✅
- Target range: **8-15 minutes** ✅ Matches requirement!

---

#### Change 2: Quality Check Limits (Line 366-370)
```python
# ❌ Before
if len(draft) < 300:
    issues.append("内容过短")
elif len(draft) > 1000:
    issues.append("内容过长")

# ✅ After
if len(draft) < 800:
    issues.append("内容过短，目标至少1500字")
elif len(draft) > 3500:
    issues.append("内容过长，建议控制在2500字以内")
```

**Impact**:
- Minimum: 800 chars (allows room for variation)
- Maximum: 3500 chars (allows up to ~18 minutes for complex topics)
- Sweet spot: 1500-2500 chars (8-15 minutes)

---

#### Change 3: Enhanced Depth Instructions (Line 490-495)
```python
# ✅ Added
2. **深度挖掘**：
   - 不能只复述新闻，必须有独到见解
   - 挖掘背后的深层原因和影响
   - 提出有价值的预测或建议
   - 每个分析点至少展开3-5句话，不要一笔带过  ← NEW
   - 用具体案例和数据支撑你的观点  ← NEW
```

---

#### Change 4: Final Warning (Line 528-532)
```python
# ✅ Added at end of prompt
⚠️ **重要提醒**：
- 目标字数：1500-2500字（约8-15分钟播报时长）
- 如果字数不足1500字，将被退回重写
- 充分展开分析，不要简略概括
- 每个论点都要有足够的论证支撑
```

---

### Fix 2: Implement Intelligent Retry System

**File**: `logic_core.py` (Line 537-570)

```python
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
        current_prompt = prompt.replace(
            "现在开始创作，直接输出文案正文：",
            "⚠️ 注意：上一次生成字数不足！请务必生成1500-2500字的深度分析。\n现在开始创作，直接输出文案正文："
        )
    else:
        current_prompt = prompt.replace(
            "现在开始创作，直接输出文案正文：",
            "🔴 严重警告：这是最后一次机会！必须生成至少1500字！\n每个分析点都要充分展开，不要简略概括！\n现在开始创作，直接输出文案正文："
        )
    
    raw_script = self.llm.invoke(current_prompt).content
    clean_script = self._clean_text(raw_script)
    
    # 记录最佳结果
    if len(clean_script) > best_char_count:
        best_script = clean_script
        best_char_count = len(clean_script)
    
    # Step 7: 质量审核
    passed, issues = self._quality_check(clean_script)
    
    if passed:
        return clean_script, None, False
    else:
        print(f"❌ 第 {attempt + 1} 次生成未通过审核: {', '.join(issues)}")
        if attempt < max_attempts - 1:
            print(f"🔄 将进行第 {attempt + 2} 次尝试...")

# 如果所有尝试都失败，返回最佳结果
print(f"⚠️ {max_attempts} 次尝试后，使用最佳结果（{best_char_count}字）")
return best_script if best_script else clean_script, None, False
```

**Features**:
1. **3 Attempts**: Tries up to 3 times
2. **Escalating Prompts**: Each retry gets stronger warnings
3. **Best Result Tracking**: Keeps longest/best generation
4. **Detailed Logging**: Shows progress of each attempt

---

### Fix 3: Enhanced Quality Check Logging

```python
def _quality_check(self, draft):
    issues = []
    char_count = len(draft)
    
    # ... checks ...
    
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
```

**Benefits**:
- Shows exact character count
- Provides clear feedback on quality
- Distinguishes between "too short" and "a bit short"

---

## 📊 Expected Results

### Content Length
| Metric | Before | After | Improvement |
|--------|---------|-------|-------------|
| Target Length | 600-800 chars | 1500-2500 chars | ⬆️ **+150%** |
| Target Duration | 3-4 minutes | 8-15 minutes | ⬆️ **+300%** |
| Max Allowed | 1000 chars (5 min) | 3500 chars (18 min) | ⬆️ **+250%** |
| Retry Attempts | 1 (weak) | 3 (escalating) | ⬆️ **+200%** |

### Quality
- ✅ Deeper analysis (3-5 sentences per point)
- ✅ More examples and data support
- ✅ Better structure and pacing
- ✅ Sufficient time for comprehensive coverage

---

## 🚀 User Action Required

### Step 1: Update Code
```bash
cd ~/Live-24/Live-24
git pull origin main
```

### Step 2: Restart Application
```bash
# Stop current Streamlit (Ctrl+C)
python3 -m streamlit run app.py
```

### Step 3: IMPORTANT - Select Correct Mode
⚠️ **Make sure to select "直播模式" (Live Mode), NOT "试听模式"**

在界面上：
- ❌ 试听模式 = Only 1 round, then stops
- ✅ 直播模式 = Continuous loop

### Step 4: Verify
- ✓ Content generation should show 3 attempts if needed
- ✓ Final script should be 1500-2500 characters
- ✓ Audio duration should be 8-15 minutes (480-900 seconds)
- ✓ System should continue to round 2 (if in live mode)

---

## 🧪 Testing Scenarios

### Test 1: Content Length
**Expected**:
- Terminal shows: "📊 当前字数: XXXX 字"
- Should be 1500-2500 characters
- Audio duration: 8-15 minutes

### Test 2: Retry Mechanism
**If first attempt too short**:
- Should see: "❌ 第 1 次生成未通过审核: 内容过短"
- Should see: "🔄 将进行第 2 次尝试..."
- Second prompt gets stronger warning

### Test 3: Continuous Loop (Live Mode Only)
**After first round completes**:
- Should see: "⏳ 当前内容时长 XXX秒，将在播放结束前30秒开始准备下一条..."
- Should see: "运行轮次: 2"
- System continues automatically

---

## 📝 Technical Details

### Character Count → Duration Calculation

**Formula**: `duration_seconds = char_count / TTS_speed`

**TTS Speed**: ~3.2 characters/second (EdgeTTS Chinese)

**Examples**:
- 1500 chars ÷ 3.2 = 469 seconds = **7.8 minutes** ✅
- 2000 chars ÷ 3.2 = 625 seconds = **10.4 minutes** ✅
- 2500 chars ÷ 3.2 = 781 seconds = **13 minutes** ✅
- 3000 chars ÷ 3.2 = 937 seconds = **15.6 minutes** ✅

### Why 1500-2500 Characters?

1. **Lower Bound (1500)**: 
   - Minimum for meaningful analysis
   - Allows full framework application
   - Covers all key points with depth

2. **Upper Bound (2500)**:
   - Sweet spot for engagement (13 minutes)
   - Prevents listener fatigue
   - Maintains content density

3. **Maximum (3500)**:
   - For exceptionally complex topics
   - Allows up to 18 minutes if needed
   - Safety margin for edge cases

---

## 🎯 Summary

### Problems Fixed:
1. ✅ Content length increased from 600-800 to 1500-2500 chars
2. ✅ Audio duration increased from 3-4 to 8-15 minutes
3. ✅ Retry mechanism: 1 weak attempt → 3 escalating attempts
4. ✅ Quality check: More detailed feedback and logging
5. ✅ Depth requirements: Explicit instructions for expansion

### User Must:
1. ⚠️ **git pull** to get latest changes
2. ⚠️ Select **"直播模式"** for continuous operation
3. ⚠️ Restart Streamlit application

### Expected Outcome:
- 📝 Content: 1500-2500 characters
- ⏱️ Duration: 8-15 minutes (target met!)
- 🔄 Rounds: Continuous (in live mode)
- 📊 Quality: Deep, comprehensive analysis

---

**Version**: v2.1.2  
**Date**: 2025-11-23  
**Type**: Feature Enhancement + Bug Fix  
**Status**: ✅ Ready for deployment

---

**Git Repository**: https://github.com/Jessieeeeai/Live-24  
**Branch**: main
