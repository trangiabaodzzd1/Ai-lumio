
import streamlit as st
import sympy as sp
from ddgs import DDGS
from pypdf import PdfReader
import io
import re
import random
import urllib.parse

st.set_page_config(
    page_title="Lumio AI | No API",
    page_icon="🎓",
    layout="wide"
)

# ===== GIAO DIỆN =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}
.stApp {
    background:
    radial-gradient(ellipse at 0% 0%, #7c3aed18, transparent 40%),
    var(--background-color);
}
.block-container {max-width:1100px;padding-top:2rem}
.hero {
    background:linear-gradient(120deg,#17152e,#4931a5,#087e8b);
    color:white;padding:30px;border-radius:24px;margin-bottom:24px;
}
.hero h1 {font-size:clamp(28px,4vw,42px);font-weight:800}
.hero p {color:#e0e7ff}
div[data-testid="stChatMessage"] {
    border:1px solid #64748b35;border-radius:18px;padding:14px;
}
div.stButton>button {border-radius:12px;min-height:42px}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""

# ===== CÔNG CỤ HỌC TẬP =====
def search_web(query):
    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=6):
            results.append({
                "title": item.get("title", "Trang tham khảo"),
                "url": item.get("href", ""),
                "body": item.get("body", "")
            })
    return results

def solve_math(text):
    x = sp.symbols("x")
    cleaned = text.replace("^", "**")
    cleaned = cleaned.replace("×", "*").replace("÷", "/")
    cleaned = cleaned.replace("−", "-")
    try:
        # Nhận dạng phương trình dạng ax^2+bx+c=0
        patterns = [
            r"([0-9xX\s\+\-\*\/\.\(\)\^]+=[0-9xX\s\+\-\*\/\.\(\)\^]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                equation = match.group(1).replace("X", "x")
                left, right = equation.split("=", 1)
                lhs = sp.sympify(left, locals={"x": x})
                rhs = sp.sympify(right, locals={"x": x})
                result = sp.solve(sp.Eq(lhs, rhs), x)
                steps = sp.expand(lhs-rhs)
                return (
                    "### 🧮 Kết quả giải toán\n\n"
                    f"**Phương trình:** `{equation}`\n\n"
                    f"**Bước 1:** Chuyển vế: `{sp.simplify(steps)} = 0`\n\n"
                    f"**Bước 2:** Giải phương trình theo x.\n\n"
                    f"**Nghiệm tìm được:** `{result}`\n\n"
                    "Hãy thay nghiệm vào phương trình ban đầu để kiểm tra."
                )
    except Exception:
        return None
    return None

def make_quiz(subject, count=10):
    banks = {
        "Toán": [
            ("2 + 3 = ?", ["4", "5", "6", "7"], 1),
            ("12 × 8 = ?", ["86", "92", "96", "108"], 2),
            ("Căn bậc hai của 81 là?", ["7", "8", "9", "10"], 2),
            ("15% của 200 bằng?", ["20", "25", "30", "35"], 2),
            ("2³ bằng?", ["4", "6", "8", "9"], 2),
        ],
        "Tiếng Anh": [
            ("She ___ a student.", ["am", "is", "are", "be"], 1),
            ("Past tense of go?", ["goed", "goes", "went", "gone"], 2),
            ("Opposite of hot?", ["warm", "cold", "heat", "high"], 1),
            ("Plural of child?", ["childs", "childes", "children", "child"], 2),
            ("I have lived here ___ 2020.", ["for", "since", "at", "on"], 1),
        ],
        "Khoa học": [
            ("Hành tinh gần Mặt Trời nhất?", ["Trái Đất", "Sao Kim", "Sao Thủy", "Sao Hỏa"], 2),
            ("Công thức hóa học của nước?", ["CO2", "H2O", "O2", "NaCl"], 1),
            ("Cây hấp thụ khí nào khi quang hợp?", ["O2", "N2", "CO2", "H2"], 2),
            ("Đơn vị đo cường độ dòng điện?", ["Volt", "Ampe", "Watt", "Ohm"], 1),
            ("Cơ quan bơm máu trong cơ thể?", ["Phổi", "Gan", "Tim", "Thận"], 2),
        ],
    }
    bank = banks.get(subject, banks["Khoa học"])
    questions = (bank * ((count // len(bank)) + 1))[:count]
    random.shuffle(questions)
    return questions

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("# ✨ Lumio AI")
    st.caption("NO API KEY • STUDY SMARTER")
    st.divider()

    grade = st.selectbox(
        "🎓 Trình độ",
        ["Tiểu học", "THCS", "THPT", "Đại học", "Tự học"]
    )
    subject = st.selectbox(
        "📚 Môn học",
        ["Tất cả", "Toán", "Vật lý", "Hóa học",
         "Sinh học", "Ngữ văn", "Tiếng Anh", "Tin học"]
    )
    mode = st.selectbox(
        "🧠 Chế độ",
        ["Gia sư học tập", "Giải toán",
         "Tìm kiếm Internet", "Tạo đề trắc nghiệm",
         "Lập kế hoạch học", "Tóm tắt tài liệu"]
    )

    st.divider()
    st.markdown("### 📄 Tài liệu")
    uploaded = st.file_uploader(
        "Tải PDF hoặc TXT", type=["pdf", "txt"]
    )
    if uploaded:
        try:
            if uploaded.name.endswith(".pdf"):
                pdf = PdfReader(io.BytesIO(uploaded.getvalue()))
                st.session_state.doc_text = "\n".join(
                    p.extract_text() or "" for p in pdf.pages
                )[:20000]
            else:
                st.session_state.doc_text = uploaded.getvalue().decode(
                    "utf-8", errors="replace"
                )[:20000]
            st.success("Đã tải tài liệu!")
        except Exception as e:
            st.error(f"Không đọc được file: {e}")

    if st.button("🗑️ Xóa cuộc trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Chạy bằng Python, không cần AI API.")

# ===== TRANG CHÍNH =====
st.markdown("""
<div class="hero">
    <div style="letter-spacing:3px;font-size:11px;color:#c4b5fd">
    YOUR PERSONAL LEARNING SPACE
    </div>
    <h1>Học thông minh hơn cùng Lumio ✨</h1>
    <p>Học tập • Tra cứu web • Luyện thi • Giải bài</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("🎓 Trình độ", grade)
c2.metric("📚 Môn học", subject)
c3.metric("🔑 API key", "Không cần")

st.info(
    "Lumio No API sử dụng công cụ học tập lập trình sẵn. "
    "Đây không phải mô hình ngôn ngữ lớn; câu trả lời mở "
    "cần dựa trên công cụ, dữ liệu và kết quả tìm kiếm."
)

st.markdown("### ⚡ Bắt đầu nhanh")
quick = st.columns(4)
examples = [
    "Giải phương trình x^2 - 5*x + 6 = 0",
    "Tạo đề trắc nghiệm Toán",
    "Tìm kiếm Internet về trí tuệ nhân tạo",
    "Lập kế hoạch học trong 7 ngày",
]
for i, example in enumerate(examples):
    if quick[i].button(example, use_container_width=True):
        st.session_state.quick_prompt = example

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("sources"):
            with st.expander("🌐 Nguồn tham khảo"):
                for s in msg["sources"]:
                    st.markdown(f"- [{s['title']}]({s['url']})")
        
        if msg.get("quiz"):
            for idx, q in enumerate(msg["quiz"]):
                st.markdown(f"**Câu {idx+1}. {q[0]}**")
                st.markdown(" · ".join(
                    f"{'ABCD'[j]}. {v}"
                    for j, v in enumerate(q[1])
                ))
                st.caption(f"Đáp án: {'ABCD'[q[2]]}")

typed = st.chat_input("Nhập câu hỏi học tập...")

if typed:
    prompt = typed
elif st.session_state.get("quick_prompt"):
    prompt = st.session_state.pop("quick_prompt")
else:
    prompt = None

if prompt:
    st.session_state.messages.append({
        "role": "user", "content": prompt
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    answer = ""
    sources = []
    quiz = None
    lower = prompt.lower()

    with st.chat_message("assistant"):
        with st.spinner("Lumio đang xử lý..."):
            if any(k in lower for k in [
                "tìm kiếm", "tra cứu", "internet", "google", "mới nhất"
            ]) or mode == "Tìm kiếm Internet":
                try:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(prompt, max_results=6))
                    if results:
                        answer = "### 🌐 Kết quả tìm kiếm Internet\n\n"
                        answer += (
                            "Đây là các kết quả từ công cụ tìm kiếm. "
                            "Hãy mở nguồn để đọc và xác minh thông tin.\n\n"
                        )
                        for i, r in enumerate(results, 1):
                            title = r.get("title", "Trang web")
                            url = r.get("href", "")
                            body = r.get("body", "")
                            answer += f"**{i}. [{title}]({url})**\n\n{body}\n\n"
                            sources.append({
                                "title": title, "url": url
                            })
                    else:
                        answer = "Không tìm thấy kết quả. Hãy thử từ khóa khác."
                except Exception as e:
                    answer = (
                        "Không kết nối được dịch vụ tìm kiếm. "
                        "Bạn có thể thử lại sau hoặc kiểm tra kết nối mạng.\n\n"
                        f"Chi tiết: `{e}`"
                    )

            elif "trắc nghiệm" in lower or "đề thi" in lower or mode == "Tạo đề trắc nghiệm":
                quiz_subject = (
                    "Toán" if "toán" in lower or subject == "Toán"
                    else "Tiếng Anh" if "anh" in lower or subject == "Tiếng Anh"
                    else "Khoa học"
                )
                quiz = make_quiz(quiz_subject, 10)
                answer = f"### 📝 Đề luyện tập: {quiz_subject}\n\n"
                answer += "\n".join(
                    f"**Câu {i+1}. {q[0]}**\n\n"
                    + "\n".join(
                        f"{'ABCD'[j]}. {v}"
                        for j, v in enumerate(q[1])
                    )
                    for i, q in enumerate(quiz)
                )
                answer += "\n\nĐáp án được lưu bên dưới để bạn tự kiểm tra."

            elif mode == "Giải toán" or re.search(r"\d+\s*[\+\-\*/^=]", prompt):
                result = solve_math(prompt)
                if result:
                    answer = result
                else:
                    answer = (
                        "Mình chưa nhận dạng được phương trình. "
                        "Bạn thử nhập dạng `x^2 - 5*x + 6 = 0` nhé."
                    )

            elif "kế hoạch" in lower or "lịch học" in lower:
                answer = f"""### 🗓️ Kế hoạch học tập 7 ngày

**Trình độ:** {grade}  
**Môn học:** {subject}

- **Ngày 1:** Kiểm tra kiến thức hiện tại, liệt kê phần chưa hiểu.
- **Ngày 2:** Học lý thuyết nền tảng và ghi chú.
- **Ngày 3:** Làm bài tập cơ bản.
- **Ngày 4:** Luyện bài tập mức trung bình.
- **Ngày 5:** Giải bài nâng cao và sửa lỗi.
- **Ngày 6:** Làm đề trong thời gian giới hạn.
- **Ngày 7:** Ôn lại lỗi sai và tự kiểm tra.

Mỗi ngày hãy thử học 2 phiên 25 phút, nghỉ 5 phút giữa các phiên.
Đây là lịch mẫu; hãy điều chỉnh theo thời gian và mục tiêu của bạn.
"""

            elif "tóm tắt" in lower or mode == "Tóm tắt tài liệu":
                if st.session_state.doc_text:
                    text = st.session_state.doc_text
                    sentences = re.split(r"(?<=[.!?])\s+", text)
                    answer = "### 📖 Nội dung tài liệu\n\n"
                    answer += "\n".join(
                        f"- {s.strip()}" for s in sentences[:12] if s.strip()
                    )
                    answer += (
                        "\n\n*Đây là phần trích lọc theo câu, "
                        "chưa phải bản tóm tắt do mô hình AI tạo ra.*"
                    )
                else:
                    answer = "Hãy tải PDF hoặc TXT ở thanh bên trước nhé."

            else:
                result = solve_math(prompt)
                if result:
                    answer = result
                elif st.session_state.doc_text:
                    answer = (
                        "### 📚 Hỗ trợ dựa trên tài liệu\n\n"
                        + st.session_state.doc_text[:5000]
                        + "\n\nHãy hỏi cụ thể hơn để mình trích nội dung phù hợp."
                    )
                else:
                    query = urllib.parse.quote(prompt)
                    answer = f"""### 🎓 Lumio Study Assistant

Mình chưa có mô hình AI ngôn ngữ để tự suy luận câu hỏi mở, nhưng có thể giúp bạn tra cứu và học tập.

**Câu hỏi của bạn:** {prompt}

**Bạn có thể:**
- Chọn chế độ **Tìm kiếm Internet** để tìm tài liệu.
- Chọn **Giải toán** để giải phương trình cơ bản.
- Chọn **Tạo đề trắc nghiệm** để luyện tập.
- Tải PDF/TXT để trích lọc nội dung.

🔎 [Tìm câu hỏi này trên Google](https://www.google.com/search?q={query})
"""

        st.markdown(answer)
        if sources:
            with st.expander("🔗 Nguồn tham khảo"):
                for s in sources:
                    st.markdown(f"- [{s['title']}]({s['url']})")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "quiz": quiz,
    })
