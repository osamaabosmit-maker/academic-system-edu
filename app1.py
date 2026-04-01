import streamlit as st
from docx import Document
import qrcode
import io
import re
import time
import pandas as pd

# --- 1. إعدادات الواجهة والتحكم في الاتجاه (RTL) ---
st.set_page_config(page_title="نظام Edu-AI الذكي", layout="wide")

if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'calculated_time' not in st.session_state:
    st.session_state.calculated_time = 0
if 'student_data' not in st.session_state:
    st.session_state.student_data = {"name": "", "id": ""}

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }
    .stRadio div[role="radiogroup"] { align-items: flex-start !important; direction: rtl !important; }
    .timer-fixed {
        position: fixed; top: 70px; left: 30px; background-color: #d32f2f; color: white;
        padding: 15px 25px; border-radius: 15px; z-index: 9999; font-size: 22px;
        font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 2px solid white;
        direction: ltr !important;
    }
    .q-card { 
        background-color: #ffffff; border-right: 12px solid #1e3a8a; padding: 25px; 
        border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: right !important;
    }
    .result-box {
        background-color: #f0f7ff; border: 2px solid #1e3a8a; padding: 25px;
        border-radius: 15px; margin-top: 20px; text-align: right !important;
    }
    .wrong-msg, .correct-msg { 
        text-align: right !important; direction: rtl !important; padding: 12px; 
        border-radius: 8px; margin-top: 8px; display: block; width: 100%;
    }
    .wrong-msg { color: #b91c1c; background-color: #fef2f2; border: 1px solid #fecaca; }
    .correct-msg { color: #15803d; background-color: #f0fdf4; border: 1px solid #bbf7d0; }
    .main-title { text-align: center !important; color: #1e3a8a; font-size: 38px; font-weight: bold; }
    .sub-title { text-align: center !important; color: #444; font-size: 24px; margin-bottom: 25px; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; width: fit-content; margin-left: auto; margin-right: auto;}
    </style>
    """, unsafe_allow_html=True)


# --- 2. وظائف المعالجة ---
def parse_questions_with_timing(file):
    doc = Document(file)
    raw_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    questions = []
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    current_q = None
    q_pattern = r'^(\d+[\.\-\)]|ما |كيف |لماذا |اذكر |هل |ضع |صح|خطأ|يُعرّف|تعتبر)'

    for line in lines:
        if re.match(q_pattern, line) or line.endswith('؟'):
            current_q = {"question": line, "options": [], "correct": "", "time": 120, "type": "مقالي"}
            questions.append(current_q)
        elif current_q is not None:
            is_correct = "(correct)" in line.lower()
            clean_val = line.replace("(correct)", "").replace("(Correct)", "").strip()
            if clean_val:
                current_q["options"].append(clean_val)
                current_q["type"] = "موضوعي";
                current_q["time"] = 30
                if is_correct: current_q["correct"] = clean_val
    return questions, sum(q['time'] for q in questions)


# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    admin_mode = st.checkbox("وضع المعلم")
    is_authorized = False
    if admin_mode:
        pwd = st.text_input("كلمة السر", type="password")
        if pwd == "admin123":
            is_authorized = True
            st.success("تم تفعيل وضع المعلم ✅")
        elif pwd:
            st.error("كلمة السر غير صحيحة")

    st.write("---")
    uploaded_file = st.file_uploader("ارفع ملف الاختبار (DOCX)", type=['docx'])

    st.write("---")
    qr = qrcode.make("https://edu-ai-zliten.streamlit.app")
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="رابط الدخول السريع", use_container_width=True)

# --- 4. العرض الرئيسي ---
st.markdown("<div class='main-title'>🏆 نظام Edu-AI الأكاديمي الشامل</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>الجامعة الأسمرية الإسلامية | كلية التربية - زليتن</div>", unsafe_allow_html=True)

if not is_authorized and not st.session_state.submitted:
    c1, c2 = st.columns(2)
    with c1: st.session_state.student_data["name"] = st.text_input("اسم الطالب الرباعي:",
                                                                   value=st.session_state.student_data["name"])
    with c2: st.session_state.student_data["id"] = st.text_input("رقم القيد الدراسي:",
                                                                 value=st.session_state.student_data["id"])

can_start = is_authorized or (st.session_state.student_data["name"] != "" and uploaded_file)

if uploaded_file and can_start:
    data, total_time = parse_questions_with_timing(uploaded_file)

    if data:
        if not is_authorized:
            if st.session_state.start_time is None:
                st.session_state.start_time = time.time()
                st.session_state.calculated_time = total_time

            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, int(st.session_state.calculated_time - elapsed))
            if remaining > 0 and not st.session_state.submitted:
                st.markdown(f"<div class='timer-fixed'>⏳ متبقي: {remaining // 60:02d}:{remaining % 60:02d}</div>",
                            unsafe_allow_html=True)

        student_answers = {}
        for i, item in enumerate(data):
            st.markdown(f"<div class='q-card'><b>س {i + 1}: {item['question']}</b></div>", unsafe_allow_html=True)

            if item['options']:
                student_answers[i] = st.radio(f"اختر:", item['options'], key=f"q_{i}", index=None,
                                              disabled=st.session_state.submitted, label_visibility="collapsed")
            else:
                student_answers[i] = st.text_area("إجابتك:", key=f"q_{i}", disabled=st.session_state.submitted)

            if is_authorized and item['options']:
                st.markdown(f"<div class='correct-msg'>💡 الإجابة النموذجية في الملف: {item['correct']}</div>",
                            unsafe_allow_html=True)

            if not is_authorized and st.session_state.submitted and item['options']:
                if student_answers[i] == item['correct']:
                    st.markdown(f"<div class='correct-msg'>✅ إجابة صحيحة: {item['correct']}</div>",
                                unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div class='wrong-msg'>❌ إجابتك: {student_answers[i] if student_answers[i] else 'لم يتم الاختيار'}</div>",
                        unsafe_allow_html=True)
                    st.markdown(f"<div class='correct-msg'>💡 الإجابة الصحيحة هي: {item['correct']}</div>",
                                unsafe_allow_html=True)
            st.write("---")

        if not st.session_state.submitted and not is_authorized:
            if st.button("🚀 تسليم الاختبار واحتساب النتيجة"):
                st.session_state.submitted = True
                st.rerun()

        # --- قسم عرض النتائج والتقرير (تم إصلاحه) ---
        if st.session_state.submitted and not is_authorized:
            correct_count = sum(
                1 for i, q in enumerate(data) if q['options'] and student_answers.get(i) == q['correct'])
            total_obj = sum(1 for q in data if q['options'])
            score_percent = (correct_count / total_obj) * 100 if total_obj > 0 else 0

            grade = "ضعيف"
            if score_percent >= 85:
                grade = "ممتاز"
            elif score_percent >= 75:
                grade = "جيد جداً"
            elif score_percent >= 65:
                grade = "جيد"
            elif score_percent >= 50:
                grade = "مقبول"

            st.markdown(f"""
                <div class='result-box'>
                    <h2 style='text-align:center; color:#1e3a8a;'>📊 تقرير أداء الطالب</h2>
                    <p><b>اسم الطالب:</b> {st.session_state.student_data['name']}</p>
                    <p><b>رقم القيد:</b> {st.session_state.student_data['id']}</p>
                    <hr>
                    <h3 style='text-align:center;'>النتيجة: {correct_count} من {total_obj}</h3>
                    <h1 style='text-align:center; color:#d32f2f;'>{score_percent:.1f}%</h1>
                    <h4 style='text-align:center; color:#1e3a8a;'>التقدير العام: {grade}</h4>
                </div>
            """, unsafe_allow_html=True)

            report_data = {
                "الاسم": [st.session_state.student_data['name']],
                "رقم القيد": [st.session_state.student_data['id']],
                "الدرجة": [f"{correct_count}/{total_obj}"],
                "النسبة": [f"{score_percent:.1f}%"],
                "التقدير": [grade]
            }
            df = pd.DataFrame(report_data)
            csv = df.to_csv(index=False).encode('utf-8-sig')

            st.download_button(
                label="📥 تحميل تقرير النتيجة (CSV)",
                data=csv,
                file_name=f"Result_{st.session_state.student_data['id']}.csv",
                mime="text/csv",
            )
            if score_percent >= 50: st.balloons()
    else:
        st.warning("لم يتم العثور على أسئلة.")
else:
    if not is_authorized:
        st.info("يرجى إدخال البيانات ورفع الملف للبدء.")
    else:
        st.info("وضع المعلم نشط: ارفع الملف للمراجعة.")