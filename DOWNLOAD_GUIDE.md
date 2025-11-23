# 📥 下载指南 - 加密大漂亮 2.0

## 方法一：复制所有文件内容（推荐）

### 必需的文件（13个）

#### 1. 核心代码文件（4个）
- `app.py`
- `logic_core.py`
- `stream_engine.py`
- `test_functionality.py`

#### 2. 配置文件（3个）
- `requirements.txt`
- `.env.example`
- `.gitignore`

#### 3. 可执行脚本（1个）
- `start.sh`

#### 4. 文档文件（5个）
- `README.md`
- `QUICKSTART.md`
- `CHANGELOG.md`
- `PROJECT_SUMMARY.md`
- `INDEX.md`

### 下载步骤

1. **在本地创建项目文件夹**
   ```bash
   mkdir crypto-beauty
   cd crypto-beauty
   ```

2. **创建子目录**
   ```bash
   mkdir assets temp archive_videos
   ```

3. **复制每个文件的内容**
   - 打开每个文件（在沙盒中查看）
   - 复制内容
   - 在本地创建同名文件并粘贴

4. **设置可执行权限**（Mac/Linux）
   ```bash
   chmod +x start.sh
   chmod +x test_functionality.py
   ```

## 方法二：使用 Git（如果可用）

如果项目在 Git 仓库中：
```bash
git clone <repository-url>
cd crypto-beauty
```

## 方法三：逐个文件下载

在沙盒环境中，你可以：
1. 使用 `Read` 工具查看文件内容
2. 复制到本地对应文件
3. 保持相同的文件名和目录结构

## 验证下载完整性

下载完成后，在本地运行：
```bash
# 检查文件数量
ls -1 *.py *.sh *.txt *.md | wc -l
# 应该显示 13

# 运行测试
python3 test_functionality.py
```

## 本地环境要求

- Python 3.8+
- FFmpeg 和 FFprobe
- 网络连接

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动应用

```bash
./start.sh
# 或
streamlit run app.py
```

访问：http://localhost:8501

---

有问题查看 `README.md` 或 `QUICKSTART.md`
