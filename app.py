import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# Streamlit Page Configuration
st.set_page_config(
    page_title="StudyVibe AI — Placement & Study Companion",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for 3D Flip Card Animation
st.markdown("""
<style>
.flip-card {
  background-color: transparent;
  width: 100%;
  height: 260px;
  perspective: 1000px;
  margin-bottom: 20px;
}

.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  text-align: center;
  transition: transform 0.7s;
  transform-style: preserve-3d;
  cursor: pointer;
}

.flip-card:hover .flip-card-inner {
  transform: rotateY(180deg);
}

.flip-card-front, .flip-card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 10px 20px rgba(0,0,0,0.12);
}

.flip-card-front {
  background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
  color: white;
}

.flip-card-back {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  color: #F8FAFC;
  transform: rotateY(180deg);
  border: 1px solid #334155;
}

.badge-tag {
  background-color: rgba(255, 255, 255, 0.25);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# Helper Function: Extract PDF Text
def extract_pdf_text(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# Helper Function: Gemini API Call
def generate_study_material(text_content, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = f"""
    You are an expert Placement Preparation Mentor for Computer Science students.
    Analyze the following study notes/content and extract 3 key Placement Interview Flashcards and 1 Quiz Question.
    
    Return ONLY a valid JSON object matching this exact structure without markdown code blocks:
    {{
        "flashcards": [
            {{
                "topic": "Topic Name",
                "question": "Placement Question?",
                "english": "Concise English Answer",
                "hinglish": "Simple Hinglish Answer (Hindi written in English with real-life analogy)"
            }}
        ],
        "quiz": {{
            "question": "Placement MCQ Question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Correct Option",
            "english_exp": "English explanation",
            "hinglish_exp": "Hinglish explanation"
        }}
    }}
    
    Study Content:
    {text_content[:4000]}
    """
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3].strip()
        
    return json.loads(raw_text)

# UI Layout Header
st.title("🎓 StudyVibe AI — Placement & Study Companion")
st.caption("Interactive English & Hinglish Flashcards + Placement Quizzes")
st.divider()

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Settings")
    user_api_key = st.text_input("Enter Gemini API Key", type="password")
    lang_choice = st.radio("Explanation Language:", ["Hinglish", "English"], index=0)
    
    st.subheader("📁 Upload Notes")
    uploaded_file = st.file_uploader("Upload PDF Notes", type=["pdf"])

# Session State
if "data" not in st.session_state:
    st.session_state.data = None

# Action Trigger
if uploaded_file and user_api_key:
    if st.sidebar.button("🚀 Generate Flashcards & Quiz"):
        with st.spinner("Analyzing PDF and generating Hinglish Flashcards..."):
            try:
                pdf_text = extract_pdf_text(uploaded_file)
                st.session_state.data = generate_study_material(pdf_text, user_api_key)
                st.sidebar.success("Done!")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

# Render UI Output
if st.session_state.data:
    tab1, tab2 = st.tabs(["🎴 3D Animated Flashcards", "🎯 Placement Quiz Arena"])
    
    with tab1:
        st.subheader("💡 Hover/Tap Cards to Reveal Answer")
        cards = st.session_state.data.get("flashcards", [])
        
        cols = st.columns(len(cards) if len(cards) > 0 else 1)
        for idx, card in enumerate(cards):
            ans_text = card["hinglish"] if lang_choice == "Hinglish" else card["english"]
            with cols[idx]:
                card_html = f"""
                <div class="flip-card">
                  <div class="flip-card-inner">
                    <div class="flip-card-front">
                      <span class="badge-tag">{card['topic']}</span>
                      <h4>{card['question']}</h4>
                      <p style="font-size: 11px; opacity: 0.8; margin-top: 10px;">(Hover to reveal)</p>
                    </div>
                    <div class="flip-card-back">
                      <span class="badge-tag" style="background-color: #3B82F6;">{lang_choice} Mode</span>
                      <p style="font-size: 13px; line-height: 1.4;">{ans_text}</p>
                    </div>
                  </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
    with tab2:
        st.subheader("📝 Placement Practice Quiz")
        quiz = st.session_state.data.get("quiz", {})
        
        if quiz:
            st.write(f"**Q. {quiz['question']}**")
            user_ans = st.radio("Select Option:", quiz["options"])
            
            if st.button("Submit Answer"):
                if user_ans == quiz["answer"]:
                    st.balloons()
                    st.success("🎉 Correct Answer! Excellent!")
                else:
                    st.error(f"❌ Incorrect! Correct answer: **{quiz['answer']}**")
                
                exp = quiz["hinglish_exp"] if lang_choice == "Hinglish" else quiz["english_exp"]
                st.info(f"💡 **Explanation ({lang_choice}):** {exp}")
else:
    st.info("👈 Sidebar mein Gemini API Key daalein aur PDF upload karke 'Generate' button dabayein!")