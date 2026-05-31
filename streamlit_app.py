import streamlit as st
import requests
import json

API_KEY = st.secrets.get("QIANFAN_API_KEY", "")

if not API_KEY:
    st.error("请先设置 API Key（在 Settings > Secrets 中添加 QIANFAN_API_KEY）")
    st.stop()

PLATFORM_PROMPTS = {
    "电商": "电商运营专家，写电商营销文案，突出卖点和性价比。",
    "小红书": "小红书博主，写种草笔记，亲切语气，加emoji，带话题标签。",
    "抖音": "抖音带货主播，写口播文案，节奏快、有冲击力。",
    "朋友圈": "朋友圈营销高手，写朋友圈文案，简短有力。",
    "微博": "微博大V，写微博营销文案，带话题。",
    "公众号": "公众号主笔，写公众号文章开头。",
    "知乎": "知乎答主，写知乎风格推荐回答。",
    "快手": "快手主播，写快手口播文案，接地气。",
    "B站": "B站UP主，写B站视频开场口播，年轻化。",
    "视频号": "视频号创作者，写视频号文案，温暖走心。"
}

def generate_copy(product_desc, platform, custom_prompt=""):
    if custom_prompt and custom_prompt.strip():
        system_prompt = custom_prompt.strip()
    else:
        system_prompt = PLATFORM_PROMPTS.get(platform, "营销文案专家")
    
    user_message = f"{system_prompt}\n\n商品：{product_desc}\n\n要求：控制在80字以内。"
    
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": "ernie-speed-pro-128k",
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.8,
        "max_tokens": 300
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"错误: {result.get('error_msg', '未知错误')}"
    except Exception as e:
        return f"请求失败: {str(e)}"

st.set_page_config(page_title="营销文案生成器", page_icon="✍️")
st.title("✍️ 营销文案生成器")
st.markdown("选择平台，输入商品描述，AI自动生成营销文案")

with st.form("my_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        platform = st.selectbox("选择平台", list(PLATFORM_PROMPTS.keys()))
        product = st.text_area("商品描述", placeholder="例如：智能手环，可测心率、血氧，续航7天", height=100)
    
    with col2:
        custom_prompt = st.text_area("自定义提示词（可选）", placeholder="留空则使用默认", height=100)
    
    submitted = st.form_submit_button("生成文案", type="primary")

if submitted and product:
    with st.spinner("AI 正在生成文案..."):
        result = generate_copy(product, platform, custom_prompt)
    st.markdown("### 📝 生成结果")
    st.write(result)
elif submitted and not product:
    st.warning("请输入商品描述")
