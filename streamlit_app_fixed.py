import streamlit as st
import requests
import json

st.set_page_config(page_title="营销文案生成器", layout="centered")

# ========== 初始化存储 ==========
if "single_result" not in st.session_state:
    st.session_state.single_result = "等待生成..."
if "batch_result" not in st.session_state:
    st.session_state.batch_result = "等待上传文件..."

# ========== API Key 校验 ==========
API_KEY = st.secrets.get("QIANFAN_API_KEY", "")
if not API_KEY:
    st.error("请先设置 API Key")
    st.stop()

# ========== 平台提示词 ==========
PLATFORM_PROMPTS = {
    "电商": "你是一个30岁的电商买家，写真实的购物评价。不要像广告，不要用'性价比之选'这类词。就像跟朋友说：'我买了个xxx，感觉...'。",
    "小红书": "你是一个28岁的普通女生，在小红书分享日常。语气像跟闺蜜聊天，用'我真的会谢''绝绝子'等词但不要堆砌。真实、自然、不浮夸。",
    "抖音": "你是一个25岁的普通人，在抖音分享好物。不要主播喊麦，不要'家人们'。就像朋友聊天，用'我试了''我觉得''我挺喜欢'。",
    "朋友圈": "你是一个35岁的上班族，发朋友圈分享好物。简单真实，不要太长，就像日常记录。",
    "知乎": "你是一个30岁的从业者，在知乎回答问题。专业但不官方，用'我个人觉得''我的经验是'。",
    "B站": "你是一个26岁的UP主，做视频开箱分享。年轻有梗但不低龄，用'兄弟们''咱们'。",
    "短信": "你是一个写祝福语的专家。根据用户描述的节日和对象，写一段真挚、温暖的祝福语。不要太长（控制在80字以内），适合用短信发送。",
    "现代诗句": "你是一个精通古诗词的诗人。根据用户描述的场景、心情或要求，创作一首古诗。可以是五言绝句、七言律诗、宋词等风格。如果用户要求藏头诗或藏尾诗，严格按照要求创作。要求：押韵、有意境、用词典雅。不要超过100字。"
}

# ========== 调用函数 ==========
def generate_copy(product_desc, platform, custom_prompt=""):
    if custom_prompt and custom_prompt.strip():
        user_message = f"{custom_prompt}\n\n场景：{product_desc}"
    else:
        system_prompt = PLATFORM_PROMPTS.get(platform, "写一段文案")
        user_message = f"{system_prompt}\n\n{product_desc}"
    
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": "ernie-speed-pro-128k", "messages": [{"role": "user", "content": user_message}], "temperature": 0.8, "max_tokens": 500}
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"错误: {result.get('error_msg', '未知错误')}"
    except Exception as e:
        return f"请求失败: {str(e)}"

# ========== UI 部分 ==========
st.title("✍️ 营销文案生成器")
st.caption("选择平台，输入描述，AI 自动生成")

tab1, tab2 = st.tabs(["📝 单条生成", "📁 批量生成"])

# ------------------- 单条生成（无 session_state 冲突）-------------------
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        platform = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()), key="single_platform")
        
        if platform == "短信":
            placeholder_text = "例如：春节，发给父母"
        elif platform == "现代诗句":
            placeholder_text = "例如：思乡，五言绝句"
        else:
            placeholder_text = "例如：智能手环，可测心率、血氧"
        
        product = st.text_area("描述", placeholder=placeholder_text, height=100, key="single_product")
        custom_prompt = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=60, key="single_custom")
        submitted = st.button("生成文案", type="primary", use_container_width=True, key="single_btn")

    with col2:
        st.markdown("### 生成结果")
        # 核心改进：不再通过 session_state 修改这个组件，而是直接根据按钮点击刷新整个显示区域
        if submitted and product:
            with st.spinner("生成中..."):
                result = generate_copy(product, platform, custom_prompt)
            st.text_area("", value=result, height=200, key="single_result_display", label_visibility="collapsed")
        else:
            # 如果没有点生成，或者没填内容，就显示等待状态
            st.text_area("", value=st.session_state.single_result, height=200, key="single_result_default", label_visibility="collapsed")

# ------------------- 批量生成（同理）-------------------
with tab2:
    col1, col2 = st.columns([1, 1])
    with col1:
        platform_batch = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()), key="batch_platform")
        uploaded_file = st.file_uploader("上传列表（txt文件）", type=["txt"], key="batch_file")
        custom_prompt_batch = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=60, key="batch_custom")
        batch_submitted = st.button("批量生成", type="primary", use_container_width=True, key="batch_btn")

    with col2:
        st.markdown("### 批量结果")
        if batch_submitted and uploaded_file is not None:
            content = uploaded_file.getvalue().decode("utf-8")
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            if lines:
                results = []
                progress_bar = st.progress(0)
                for i, line in enumerate(lines):
                    result = generate_copy(line, platform_batch, custom_prompt_batch)
                    results.append(f"【输入】{line}\n【生成】{result}\n\n")
                    progress_bar.progress((i + 1) / len(lines))
                full_result = "".join(results)
                st.text_area("", value=full_result, height=300, key="batch_result_display", label_visibility="collapsed")
                st.download_button(label="📥 下载结果", data=full_result, file_name="batch_results.txt", mime="text/plain")
            else:
                st.info("文件中没有有效内容")
        else:
            # 没点生成时显示等待状态
            st.text_area("", value=st.session_state.batch_result, height=300, key="batch_result_default", label_visibility="collapsed")

st.divider()
st.caption("8个平台 | 免费使用")
