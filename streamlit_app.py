import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import io
import os

st.set_option("client.toolbarMode", "viewer")

st.set_page_config(
    page_title="米盖AI工具集",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f5f8fc;
    }
    
    /* 任务1：标题样式 */
    .brand-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        color: #1a3a5c;
        margin-bottom: 0.25rem;
        margin-top: 0.5rem;
        letter-spacing: -1px;
    }
    
    /* 任务2：副标题样式 */
    .brand-sub {
        text-align: center;
        font-size: 0.75rem;
        color: #8ca3bc;
        font-weight: 400;
        letter-spacing: 0.3px;
        margin-bottom: 2rem;
    }
    
    /* 任务3：标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: white;
        padding: 0.5rem;
        border-radius: 60px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        justify-content: center;
        margin-bottom: 1.5rem;
        border: 1px solid #eef2f8;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
        font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
        color: #5a748e;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #eef4fa;
        color: #2c6280;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #eef4fa 0%, #e6eef8 100%);
        color: #1a5680;
        font-weight: 600;
        border: 1px solid #d0e2f0;
    }
    
    /* 任务4：结果框样式 */
    .result-box {
        background: #eef4fc;
        padding: 1rem 1.2rem;
        border-radius: 18px;
        margin-top: 0.75rem;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #1e3a5f;
        border-left: 4px solid #6c9ebf;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    
    /* 任务5：按钮样式 - 次重要，不抢眼 */
    .stButton button {
        background: #f0f4fa;
        color: #4a6a8a;
        border-radius: 40px;
        border: 1px solid #dce5f0;
        padding: 0.5rem 1.2rem;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.2s ease;
        width: 100%;
        box-shadow: none;
    }
    .stButton button:hover {
        background: #e6edf5;
        border-color: #b8cde0;
        transform: translateY(-1px);
    }
    .stButton button:active {
        transform: translateY(0);
    }
    
    .stTextArea textarea, .stTextInput input {
        border-radius: 16px;
        border: 1px solid #e2eaf2;
        font-size: 0.9rem;
        background: white;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #4a90c4;
        box-shadow: 0 0 0 3px rgba(74, 144, 196, 0.1);
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #8ca3bc;
        font-size: 0.7rem;
        border-top: 1px solid #e8eef4;
        margin-top: 2rem;
    }
    
    .stat-card {
        background: white;
        border-radius: 20px;
        padding: 0.8rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        border: 1px solid #eef2f8;
    }
    .stat-number {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2c6280;
    }
    .stat-label {
        font-size: 0.7rem;
        color: #8ca3bc;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-title">米盖 🤖 AI 大模型工具集</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">文案生成 · 批量生成 · 关键词提取 · 文本摘要 · 文本分类 · 翻译 · 历史记录</div>', unsafe_allow_html=True)

raw_key = os.environ.get("QIANFAN_API_KEY", "")
API_KEY = raw_key.strip() if raw_key else ""

if not API_KEY:
    st.error("请先设置环境变量 QIANFAN_API_KEY")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []
if "single_result" not in st.session_state:
    st.session_state.single_result = ""

PLATFORM_PROMPTS = {
    "小红书": "你是小红书爆款笔记写手。内容需要口语、可以分段、添加emoji。标题3-5个。开头抓人，中间分段,段落数字不规则（每段≤4行），结尾求互动。禁止平台违禁词。加话题标签7-10个。",
    "抖音": "你是抖音爆款脚本写手。前3秒要钩子（反常识/痛点/悬念）。全脚本45秒，短句每句≤10字。分3点以内。结尾强引导评论。标注【画面】和【字幕】位置。封面标题5个（≤15字）。",
    "B站": "你是B站深度脚本写手。语言半口语半书面，别喊麦。前30秒定调+预告+建立信任。正文用章节式（Part1/2/3），设计【弹幕点】。结尾不强求点赞，用'投币是认可'。不喊家人们。",
    "朋友圈": "你是一个35岁的上班族，写朋友圈文案，简单真实。",
    "节日祝福": "你是一个写祝福语的专家，写真挚温暖的祝福语。",
    "现代诗句": "你是一个精通古诗词的诗人，创作古诗。",
    "小学作文": "你是一位北师大毕业、有10年教龄的语文老师。写一篇符合要求的作文。直接输出正文，正文后写-----再写评语。"
}

def call_api(prompt, temperature=0.8, max_tokens=1000):
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": "ernie-speed-pro-128k", "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "生成失败")
    except Exception as e:
        return f"请求失败: {str(e)}"

def generate_copy(product_desc, platform, custom_prompt=""):
    if custom_prompt and custom_prompt.strip():
        user_message = f"{custom_prompt}\n\n要求：{product_desc}"
    else:
        system_prompt = PLATFORM_PROMPTS.get(platform, "写一段文案")
        if platform == "小学作文":
            user_message = f"{system_prompt}\n\n作文要求：{product_desc}"
        else:
            user_message = f"{system_prompt}\n\n{product_desc}"
    return call_api(user_message)

def extract_keywords(text):
    prompt = f"请从以下文本中提取5-10个最重要的关键词，用逗号分隔，只输出关键词：\n\n{text}"
    return call_api(prompt, temperature=0.3, max_tokens=200)

def summarize_text(text, max_length=200):
    prompt = f"请为以下文本生成一段简洁的摘要，控制在{max_length}字以内：\n\n{text}"
    return call_api(prompt, temperature=0.5, max_tokens=500)

def translate(text, target_lang):
    prompt = f"请将以下文本翻译成{target_lang}，只输出翻译结果：\n\n{text}"
    return call_api(prompt, temperature=0.3, max_tokens=1000)

def classify_text(text):
    prompt = f"""请判断以下文本属于哪个类别，只输出类别名称。
可选类别：科技、体育、财经、娱乐、教育、政治、健康、旅游、美食、其他

文本：{text}

类别："""
    return call_api(prompt, temperature=0.3, max_tokens=50)

if st.session_state.history:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(st.session_state.history)}</div><div class="stat-label">总生成次数</div></div>', unsafe_allow_html=True)
    with col2:
        platforms_used = len(set([h.get("平台", "") for h in st.session_state.history]))
        st.markdown(f'<div class="stat-card"><div class="stat-number">{platforms_used}</div><div class="stat-label">使用平台数</div></div>', unsafe_allow_html=True)
    with col3:
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = len([h for h in st.session_state.history if h.get("时间", "").startswith(today)])
        st.markdown(f'<div class="stat-card"><div class="stat-number">{today_count}</div><div class="stat-label">今日生成</div></div>', unsafe_allow_html=True)

tabs = st.tabs(["📝 文案生成", "📁 批量生成", "🔑 关键词提取", "📄 文本摘要", "📂 文本分类", "🌐 翻译", "📜 历史记录"])

# 文案生成
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        platform = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()), key="single_platform")
        if platform == "节日祝福":
            placeholder_text = "例如：春节，发给父母"
        elif platform == "现代诗句":
            placeholder_text = "例如：思乡，五言绝句"
        elif platform == "小学作文":
            placeholder_text = "例如：三年级，我最喜欢的动物，300字"
        elif platform == "小红书":
            placeholder_text = "例如：防晒霜，用了一周真的白了一个度"
        elif platform == "抖音":
            placeholder_text = "例如：这个收纳盒，家里人都说好用"
        elif platform == "B站":
            placeholder_text = "例如：我花1000块买了三款机械键盘，结论是..."
        else:
            placeholder_text = "例如：这个产品真的很好用，推荐给大家"
        product = st.text_area("描述", placeholder=placeholder_text, height=100, key="single_product")
        custom_prompt = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=60, key="single_custom")
        input_len = len(product) if product else 0
        st.markdown(f'<p style="text-align:right; font-size:0.7rem; color:#8ca3bc;">📝 输入字数：{input_len}</p>', unsafe_allow_html=True)
        submitted = st.button("✨ 生成文案", use_container_width=True, key="single_btn")
    with col2:
        st.markdown("### 生成结果")
        if submitted and product:
            with st.spinner("生成中..."):
                result = generate_copy(product, platform, custom_prompt)
            st.session_state.single_result = result
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
            output_len = len(result) if result else 0
            st.markdown(f'<p style="text-align:right; font-size:0.7rem; color:#8ca3bc;">📄 输出字数：{output_len}</p>', unsafe_allow_html=True)
            st.session_state.history.append({
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "类型": "文案生成",
                "平台": platform,
                "输入": product,
                "自定义提示词": custom_prompt if custom_prompt else "无",
                "输出": result
            })
        elif submitted and not product:
            st.info("请输入描述")
        else:
            if st.session_state.single_result:
                st.markdown(f'<div class="result-box">{st.session_state.single_result}</div>', unsafe_allow_html=True)
            else:
                st.info("等待生成...")

# 批量生成
with tabs[1]:
    col1, col2 = st.columns([1, 1])
    with col1:
        platform_batch = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()), key="batch_platform")
        uploaded_file = st.file_uploader("上传文件", type=["txt", "xlsx", "xls"], key="batch_file", help="txt（每行一个描述）或 Excel（第一列为描述）")
        st.caption("📌 txt格式：每行一个描述 | Excel格式：第一列为描述")
        custom_prompt_batch = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=60, key="batch_custom")
        batch_submitted = st.button("⚡ 批量生成", use_container_width=True, key="batch_btn")
    with col2:
        st.markdown("### 批量结果")
        if batch_submitted and uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension == 'txt':
                content = uploaded_file.getvalue().decode("utf-8")
                lines = [line.strip() for line in content.split("\n") if line.strip()]
            else:
                df = pd.read_excel(uploaded_file)
                lines = df.iloc[:, 0].dropna().astype(str).tolist()
                lines = [line.strip() for line in lines if line.strip()]
            if lines:
                results = []
                progress_bar = st.progress(0)
                batch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for i, line in enumerate(lines):
                    result = generate_copy(line, platform_batch, custom_prompt_batch)
                    results.append(f"【输入】{line}\n【生成】{result}\n\n")
                    st.session_state.history.append({
                        "时间": batch_time,
                        "类型": "批量生成",
                        "平台": platform_batch,
                        "输入": line,
                        "自定义提示词": custom_prompt_batch if custom_prompt_batch else "无",
                        "输出": result
                    })
                    progress_bar.progress((i + 1) / len(lines))
                full_result = "\n".join(results)
                st.markdown(f'<div class="result-box" style="max-height:400px; overflow-y:auto;">{full_result.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                df_export = pd.DataFrame({"输入": lines, "生成结果": results})
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='批量结果', index=False)
                excel_data = output.getvalue()
                st.download_button("📥 下载结果 (Excel)", data=excel_data, file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("文件中没有有效内容")
        elif batch_submitted and uploaded_file is None:
            st.info("请先上传文件")
        else:
            st.info("等待上传文件...")

# 关键词提取
with tabs[2]:
    kw_text = st.text_area("输入文本", height=200, key="kw_text", placeholder="请粘贴需要提取关键词的文本...")
    if st.button("🔑 提取关键词", use_container_width=True):
        if kw_text.strip():
            with st.spinner("提取中..."):
                result = extract_keywords(kw_text)
            st.success("提取完成")
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("请输入文本")

# 文本摘要
with tabs[3]:
    summary_text = st.text_area("输入文本", height=200, key="summary_text", placeholder="请粘贴需要摘要的长文本...")
    max_len = st.slider("摘要长度（字数）", min_value=20, max_value=500, value=60, step=40)
    if st.button("📄 生成摘要", use_container_width=True):
        if summary_text.strip():
            with st.spinner("生成中..."):
                result = summarize_text(summary_text, max_len)
            st.success("生成完成")
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("请输入文本")

# 文本分类
with tabs[4]:
    classify_text_input = st.text_area("输入文本", height=200, key="classify_text", placeholder="请粘贴需要分类的文本...")
    if st.button("📂 分类", use_container_width=True):
        if classify_text_input.strip():
            with st.spinner("分析中..."):
                result = classify_text(classify_text_input)
            st.success("分析完成")
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("请输入文本")

# 翻译
with tabs[5]:
    LANGUAGES = ["中文", "英文", "泰文", "日文", "韩文", "法文", "德文", "俄文", "西班牙文", "阿拉伯文"]
    col1, col2 = st.columns(2)
    with col1:
        trans_text = st.text_area("原文", height=150, key="trans_text", placeholder="请输入要翻译的文本...")
    with col2:
        target_lang = st.selectbox("目标语言", LANGUAGES, key="target_lang")
    if st.button("🌐 翻译", use_container_width=True):
        if trans_text.strip():
            with st.spinner("翻译中..."):
                result = translate(trans_text, target_lang)
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
        else:
            st.warning("请输入文本")

# 历史记录
with tabs[6]:
    st.markdown("### 📜 生成历史")
    if not st.session_state.history:
        st.info("暂无历史记录，生成文案后会自动保存")
    else:
        df = pd.DataFrame(st.session_state.history)
        columns_order = ["时间", "类型", "平台", "输入", "自定义提示词", "输出"]
        df = df[columns_order]
        st.dataframe(df.tail(20), use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清空历史", key="clear_history"):
                st.session_state.history = []
                st.session_state.single_result = ""
        with col2:
            if st.button("📊 导出历史到 Excel", key="export_excel"):
                if st.session_state.history:
                    df_export = pd.DataFrame(st.session_state.history)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_export.to_excel(writer, sheet_name='生成历史', index=False)
                    excel_data = output.getvalue()
                    st.download_button("📥 下载 Excel", data=excel_data, file_name=f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="download_history")

st.markdown('<div class="footer">实用工具合辑，AI改变生活习惯 (7个平台 | 免费使用)</div>', unsafe_allow_html=True)
