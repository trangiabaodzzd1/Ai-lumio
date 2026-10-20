import os
import io
import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# ==========================================
# LUMIO AI — PERSONAL LEARNING ASSISTANT
# ==========================================
st.set_page_config(
    page_title="Lumio AI | Gia sư thông minh",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

API_KEY = get_secret("GEMINI_API_KEY")
MODEL = get_secret("GEMINI_MODEL", "gemini-3.8-flash")

# ==========================================
# DESIGN
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}
.stApp {
    background:
      radial-gradient(ellipse at 0% 0%, #6366f115, transparent 38%),
      var(--background-color);
}
.block-container {
    max-width: 1120px;
    padding-top: 1.7rem;
    padding-bottom: 3rem;
}
.hero {
    padding: 30px;
    border-radius: 24px;
    color: white;
    background: linear-gradient(120deg,#111827,#3730a3 60%,#087e8b);
    margin-bottom: 24px;
    border: 1px solid #ffffff20;
}
.hero h1 {font-size: clamp(28px,4vw,42px);font-weight:800;margin:8px 0}
.hero p {color:#dbeafe;margin:0}
.eyebrow {font-size:11px;letter-spacing:2px;color:#c4b5fd;font-weight:700}
div[data-testid="stChatMessage"] {
    border:1px solid #64748b30;
    border-radius:18px;
    padding:14px;
}
div.stButton>button {
    border-radius:12px;
    font-weight:600;
    min-height:42px;
}
div[data-testid="stMetric"] {
    border:1px solid #64748b35;
    padding:12px;
    border-radius:14px;
}
footer {visibility:hidden}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document" not in st.session_state:
    st.session_state.document = ""
if "pending" not in st.session_state:
    st.session_state.pending = None

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("# ✨ Lumio AI")
    st.caption("YOUR PERSONAL AI TUTOR")
    st.divider()

    grade = st.selectbox(
        "🎓 Trình độ",
        ["THCS", "THPT", "Đại học", "Tiểu học", "Tự học / Đi làm"],
        index=1,
    )

    subject = st.selectbox(
        "📚 Môn học",
        [
            "Tất cả môn học", "Toán", "Vật lý", "Hóa học",
            "Sinh học", "Ngữ văn", "Tiếng Anh", "Lịch sử",
            "Địa lý", "Tin học / Lập trình"
        ],
    )

    mode = st.selectbox(
        "🧠 Chế độ học",
        [
            "Gia sư thông minh",
            "Giải bài từng bước",
            "Ôn thi cấp tốc",
            "Tóm tắt kiến thức",
            "Tạo đề trắc nghiệm",
            "Luyện tiếng Anh",
            "Nghiên cứu chuyên sâu",
        ],
    )

    web_on = st.toggle("🌐 Tìm kiếm Google", value=True)

    st.divider()
    st.markdown("### 📄 Tài liệu học tập")
    uploaded = st.file_uploader(
        "Tải lên PDF hoặc TXT",
        type=["pdf", "txt"],
    )

    if uploaded:
        try:
            if uploaded.name.lower().endswith(".pdf"):
                pdf = PdfReader(io.BytesIO(uploaded.getvalue()))
                content = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
            else:
                content = uploaded.getvalue().decode(
                    "utf-8", errors="replace"
                )

            st.session_state.document = content[:25000]
            st.success("Đã đọc tài liệu!")
        except Exception as e:
            st.error(f"Không đọc được tài liệu: {e}")

    if st.button("🗑️ Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending = None
        st.rerun()

    st.divider()
    st.caption("Powered by Google Gemini")

# ==========================================
# HEADER
# ==========================================
st.markdown("""
<div class="hero">
  <div class="eyebrow">PERSONAL LEARNING INTELLIGENCE</div>
  <h1>Học thông minh hơn cùng Lumio ✨</h1>
  <p>Hiểu sâu kiến thức · Giải bài từng bước · Khám phá tri thức mới</p>
</div>
""", unsafe_allow_html=True)

a, b, c = st.columns(3)
a.metric("🎯 Chế độ", mode)
b.metric("📖 Môn học", subject)
c.metric("🌐 Internet", "Đã bật" if web_on else "Đã tắt")

# ==========================================
# QUICK ACTIONS
# ==========================================
st.markdown("### 💡 Bạn muốn học gì hôm nay?")
cols = st.columns(4)

prompts = [
    "Giải thích một kiến thức khó",
    "Lập kế hoạch ôn thi 7 ngày",
    "Tạo 10 câu trắc nghiệm",
    "Tóm tắt kiến thức trọng tâm",
]

for i, label in enumerate(prompts):
    if cols[i].button(label, use_container_width=True):
        st.session_state.pending = label
        st.rerun()

# ==========================================
# INSTRUCTIONS
# ==========================================
def build_instructions():
    instruction = f"""
Bạn là Lumio, một gia sư AI xuất sắc, thân thiện, kiên nhẫn,
giải thích rõ ràng và khuyến khích học sinh tự suy nghĩ.

Ngôn ngữ mặc định: tiếng Việt.
Trình độ người học: {grade}.
Môn học ưu tiên: {subject}.
Chế độ hiện tại: {mode}.

QUY TẮC:
1. Giải thích từ cơ bản đến nâng cao, phù hợp trình độ.
2. Toán, Lý, Hóa: ghi dữ kiện, công thức, từng bước,
   đơn vị, kết quả và kiểm tra tính hợp lý.
3. Lập trình: đưa code dễ hiểu và hướng dẫn chạy.
4. Văn học: phân tích luận điểm, dẫn chứng và cách lập luận.
5. Trắc nghiệm: đưa câu hỏi, các lựa chọn, đáp án và giải thích.
6. Ôn thi: chia kiến thức theo chủ đề, mức độ ưu tiên và lịch học.
7. Không bịa nguồn, số liệu, đường dẫn hay trích dẫn.
8. Khi tìm kiếm web, hãy tổng hợp từ nguồn phù hợp và
   nêu rõ thông tin nào có thể đã thay đổi.
9. Giúp người học hiểu cách làm, không chỉ đưa đáp án.
10. Trình bày Markdown rõ ràng; dùng LaTeX khi cần.

Nếu có tài liệu người dùng tải lên, ưu tiên dựa vào nội dung
tài liệu. Phân biệt rõ nội dung tài liệu với kiến thức bên ngoài.

TÀI LIỆU NGƯỜI DÙNG:
{st.session_state.document[:25000]}
"""
    return instruction

# ==========================================
# CITATIONS FROM GOOGLE SEARCH
# ==========================================
def get_sources(response):
    sources = []
    seen = set()

    try:
        for candidate in response.candidates or []:
            metadata = candidate.grounding_metadata
            if not metadata:
                continue

            for chunk in metadata.grounding_chunks or []:
                web = getattr(chunk, "web", None)
                if web and web.uri and web.uri not in seen:
                    seen.add(web.uri)
                    sources.append({
                        "title": web.title or web.uri,
                        "url": web.uri,
                    })
    except Exception:
        pass

    return sources

# ==========================================
# CHAT HISTORY
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):
            with st.expander("🔎 Nguồn tham khảo"):
                for src in message["sources"]:
                    st.markdown(f"- [{src['title']}]({src['url']})")

# ==========================================
# CHAT INPUT
# ==========================================
pending = st.session_state.pending
typed = st.chat_input("Hỏi Lumio bất cứ điều gì...")

if typed:
    prompt = typed
    st.session_state.pending = None
elif pending:
    prompt = pending
    st.session_state.pending = None
else:
    prompt = None

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        if not API_KEY:
            answer = (
                "🔑 Bạn chưa thêm GEMINI_API_KEY. "
                "Hãy tạo key tại https://aistudio.google.com/apikey "
                "và thêm vào Secrets trên Streamlit Cloud."
            )
            placeholder.warning(answer)
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": [],
            })
        else:
            try:
                client = genai.Client(api_key=API_KEY)

                history = []
                for msg in st.session_state.messages[-17:]:
                    history.append(types.Content(
                        role="user" if msg["role"] == "user" else "model",
                        parts=[types.Part.from_text(text=msg["content"])],
                    ))

                config_args = {
                    "system_instruction": build_instructions(),
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                }

                if web_on:
                    config_args["tools"] = [
                        types.Tool(
                            google_search=types.GoogleSearch()
                        )
                    ]

                config = types.GenerateContentConfig(**config_args)

                with st.spinner("Lumio đang suy nghĩ..."):
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=history,
                        config=config,
                    )

                answer = response.text or "AI chưa tạo được câu trả lời."
                sources = get_sources(response)

                placeholder.markdown(answer)

                if sources:
                    with st.expander("🌐 Nguồn tham khảo từ Google"):
                        for src in sources:
                            st.markdown(f"- [{src['title']}]({src['url']})")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            except Exception as e:
                st.error(
                    "Chưa gọi được Gemini. Hãy kiểm tra API key, "
                    "model, kết nối mạng và hạn mức API."
                )
                st.caption(f"Chi tiết lỗi: {e}")

st.divider()
st.caption(
    "Lumio AI • Hãy kiểm tra nguồn tham khảo với thông tin quan trọng. "
    "AI đôi khi có thể trả lời sai."
)
