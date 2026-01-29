import streamlit as st
import google.generativeai as genai

# 화면 설정
st.set_page_config(page_title="나의 AI 앱", page_icon="🤖")
st.title("🤖 팀원과 공유하는 AI 앱")

# API 키 설정 (Streamlit Secrets에서 가져옴)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API 키 설정이 필요합니다. Streamlit Settings > Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

# 모델 설정 (Gemini 1.5 Flash 사용)
model = genai.GenerativeModel('gemini-1.5-flash')

# 대화창 UI
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        response = model.generate_content(prompt)
        st
