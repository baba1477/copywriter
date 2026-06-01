import streamlit as st
import requests
import json

st.set_page_config(
    page_title="营销文案生成器",
    page_icon="✍️",
    layout="centered"
)

st.markdown("""
<style>
    .title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        color: #1f1f1f;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        border-left: 3px solid #ff4b4b;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .batch-result {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        max-height: 500px;
        overflow-y: auto;
    }
    .stButton button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton button:hover {
        background-color: #e03e3e;
    }
    hr {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

API_KEY = st.secrets.get("QIANFAN_API_KEY", "")
if not API_KEY:
    st.error("请先设置 API Key")
    st.stop()

PLATFORM_PROMPTS = {
    "电商": "电商运营专家，写电商营销文案，突出卖点和性价比。",
    "小红书": "小红书博主，写种草笔记，亲切语气，加emoji，带话题标签。",
    "抖音": "抖音带货主播，写口播文案，节奏快、有冲击力。",
    "朋友圈": "朋友圈营销高手，写朋友圈文案，简短有力。",
    "知乎": "知乎答主，写知乎风格推荐回答。",
    "B站": "B站UP主，写B站视频开场口播，年轻化。"
}

def generate_copy(product_desc, platform, custom_prompt=""):
    if custom_prompt and custom_prompt.strip():
        system_prompt = custom_prompt.strip()
    else:
        system_prompt = PLATFORM_PROMPTS.get(platform, "营销文案专家")
    
    user_message = f"{system_prompt}\n\n商品：{product_desc}\n\n要求：控制在80字以内。"
    
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": "ernie-speed-pro-128k", "messages": [{"role": "user", "content": user_message}], "temperature": 0.8, "max_tokens": 300}
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"错误: {result.get('error_msg', '未知错误')}"
    except Exception as e:
        return f"请求失败: {str(e)}"

# 界面
st.markdown('<p class="title">✍️ 营销文案生成器</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">选择平台，输入商品描述，AI 自动生成文案</p>', unsafe_allow_html=True)

# 创建标签页
tab1, tab2 = st.tabs(["📝 单条生成", "📁 批量生成"])

# ========== 标签页1：单条生成 ==========
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        platform = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()), key="single_platform")
        product = st.text_area("商品描述", placeholder="例如：智能手环，可测心率、血氧，续航7天", height=100, key="single_product")
        custom_prompt = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=60, key="single_custom")
        submitted = st.button("生成文案", type="primary", use_container_width=True, key="single_btn")
    
    with col2:
        st.markdown("### 生成结果")
        if submitted and product:
            with st.spinner("生成中..."):
                result = generate_copy(product, platform, custom_prompt)
            st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
        elif submitted and not product:
            st.info("请输入商品描述")

# ========== 标签页2：批量生成 ==========
with tab2:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        platform_batch = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()), key="batch_platform")
        
        # 文件上传
        uploaded_file = st.file_uploader("上传商品列表（txt文件）", type=["txt"], key="batch_file")
        
        st.caption("📌 文件格式：每行一个商品描述")
        st.caption("📌 示例：\n智能手环，可测心率、血氧\n无线耳机，降噪功能")
        
        custom_prompt_batch = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=60, key="batch_custom")
        batch_submitted = st.button("批量生成", type="primary", use_container_width=True, key="batch_btn")
    
    with col2:
        st.markdown("### 批量结果")
        
        if batch_submitted and uploaded_file is not None:
            # 读取文件内容
            content = uploaded_file.getvalue().decode("utf-8")
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            
            if not lines:
                st.warning("文件中没有有效内容")
            else:
                st.info(f"共 {len(lines)} 条商品，开始生成...")
                
                results = []
                progress_bar = st.progress(0)
                
                for i, line in enumerate(lines):
                    result = generate_copy(line, platform_batch, custom_prompt_batch)
                    results.append(f"【商品】{line}<br>【文案】{result}<br><br>")
                    progress_bar.progress((i + 1) / len(lines))
                
                # 显示结果
                st.markdown(f'<div class="batch-result">{"".join(results)}</div>', unsafe_allow_html=True)
                
                # 提供下载
                download_content = "\n" + "="*50 + "\n\n".join(results)
                st.download_button(
                    label="📥 下载结果",
                    data=download_content,
                    file_name="batch_results.txt",
                    mime="text/plain"
                )
                
        elif batch_submitted and uploaded_file is None:
            st.info("请先上传商品列表文件")

st.divider()
st.caption("使用百度千帆 ERNIE-Speed-Pro-128K 模型 | 6个平台 | 支持批量生成 | 免费使用")
