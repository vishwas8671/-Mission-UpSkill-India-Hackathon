import streamlit as st
import random, json, io, uuid, threading
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
import pyttsx3
import speech_recognition as sr

# ---------------------------
# Roles & Interview Types
ROLES = [
    "Software Engineer", "Product Manager", "Data Analyst", "Backend Developer",
    "Frontend Developer", "ML Engineer", "Data Scientist", "DevOps Engineer",
    "QA Engineer", "System Architect"
]

INTERVIEW_TYPES = ["Technical", "Behavioral", "System Design", "Coding", "Managerial"]

# ---------------------------
# Sample Questions (10 per role per type)
# Populate real questions here
REAL_QUESTIONS = {
    "Software Engineer": {
        "Technical": [
            "Explain OOP concepts.",
            "Difference between SQL and NoSQL.",
            "What is REST API?",
            "Explain MVC architecture.",
            "What is polymorphism?",
            "Describe microservices.",
            "What is a thread?",
            "Explain GET vs POST.",
            "Difference between heap and stack memory.",
            "Explain MVC pattern in web applications."
        ],
        "Behavioral": [
            "Describe a time you overcame a challenge.",
            "Example of teamwork you contributed to.",
            "Tell me about a conflict you resolved.",
            "Describe a time you learned something quickly.",
            "How do you prioritize tasks?",
            "Describe leadership experience.",
            "How do you handle stress?",
            "Example of failure and how you handled it.",
            "Give an example of problem-solving.",
            "Describe a time you adapted to change."
        ],
        "System Design": [
            "Design a URL shortening service.",
            "Design a chat application.",
            "Explain scalability concepts.",
            "Design an e-commerce backend.",
            "How to handle high traffic in web apps?",
            "Design a recommendation system.",
            "Explain caching strategies.",
            "Database sharding explanation.",
            "Design a parking lot system.",
            "Explain load balancing in distributed systems."
        ],
        "Coding": [
            "Write function to reverse a string.",
            "Find max subarray sum.",
            "Check for palindrome in string.",
            "Implement linked list.",
            "Sort array using quicksort.",
            "Find factorial of a number.",
            "Check prime number.",
            "Implement stack using array.",
            "Binary search in sorted array.",
            "Find duplicate numbers in array."
        ],
        "Managerial": [
            "How do you manage team conflicts?",
            "Explain your decision-making process.",
            "How to prioritize projects?",
            "Describe handling missed deadlines.",
            "Motivate a low-performing team member.",
            "How to handle difficult stakeholder?",
            "Explain resource allocation process.",
            "How to manage cross-functional teams?",
            "Handling multiple projects at once.",
            "Experience in leading remote teams."
        ]
    },
    "Data Analyst": {
        "Technical": [
            "Difference between structured and unstructured data?",
            "Explain SQL JOINs.",
            "What is data cleaning?",
            "Handling missing data in datasets?",
            "Difference between correlation and causation?",
            "Explain pivot tables.",
            "What is ETL process?",
            "Explain data normalization.",
            "Difference between OLAP and OLTP.",
            "Explain A/B testing."
        ],
        "Behavioral": [
            "Describe a time you analyzed incomplete data.",
            "Example of insights impacting decisions.",
            "Working under tight deadlines?",
            "Describe teamwork in data project.",
            "Presenting findings to non-technical stakeholders.",
            "How do you handle multiple datasets?",
            "Describe learning a new tool quickly.",
            "Explain a challenging data project.",
            "How do you ensure data accuracy?",
            "Conflict resolution in a data team."
        ],
        "System Design": [
            "Design a data warehouse.",
            "Explain data pipeline architecture.",
            "Handling large datasets efficiently.",
            "How to design analytics dashboard?",
            "Explain indexing strategies.",
            "ETL vs ELT explanation.",
            "Design reporting system for management.",
            "Data lake vs data warehouse.",
            "Explain schema design for analytics.",
            "Handling real-time data streams."
        ],
        "Coding": [
            "SQL query to find duplicates.",
            "Calculate moving average in Python.",
            "Implement basic regression in Python.",
            "Data visualization using matplotlib.",
            "Write Python code to clean data.",
            "Implement pivot table in pandas.",
            "Merge multiple datasets.",
            "Filter data based on condition.",
            "Sort data efficiently.",
            "Find missing values in dataset."
        ],
        "Managerial": [
            "How do you prioritize analytics projects?",
            "Managing cross-department data requests.",
            "Explain handling tight deadlines.",
            "Resource allocation in analytics team.",
            "Decision making based on data insights.",
            "Handling disagreements in team.",
            "Mentoring junior analysts.",
            "Managing stakeholders’ expectations.",
            "Ensuring timely delivery of dashboards.",
            "Experience in leading analytics projects."
        ]
    }
    # Add remaining 8 roles similarly
}

# ---------------------------
def evaluate_answer(answer, mode):
    words = len(answer.split())
    if mode in ["Technical", "Coding", "System Design"]:
        score = min(10, max(4, words//5 + 5))
        feedback = "Good depth." if words > 15 else "Too short. Add clarity/examples."
    else:
        score = min(10, max(5, words//6 + 5))
        feedback = "Good teamwork/structure." if "team" in answer.lower() else "Try STAR format."
    return score, feedback

# ---------------------------
def generate_pdf_bytes(responses, session_id):
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buf)
    elems = []
    elems.append(Paragraph("AI Interview Chatbot - Summary", styles["Title"]))
    elems.append(Spacer(1,12))
    avg = sum([r["score"] for r in responses])/len(responses) if responses else 0
    elems.append(Paragraph(f"Final Score: {avg:.2f}/10", styles["Heading2"]))
    elems.append(Spacer(1,12))
    for i,r in enumerate(responses):
        elems.append(Paragraph(f"Q{i+1}: {r['question']}", styles["Heading3"]))
        elems.append(Paragraph(f"Answer: {r['answer']}", styles["Normal"]))
        elems.append(Paragraph(f"Feedback: {r['feedback']}", styles["Normal"]))
        elems.append(Paragraph(f"Score: {r['score']}/10", styles["Normal"]))
        elems.append(PageBreak())
    doc.build(elems)
    return buf.getvalue()

# ---------------------------
def speak_text(text):
    def run():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run).start()

# ---------------------------
st.set_page_config(page_title="AI Interview Chatbot", layout="centered")
st.title("🤖 Hackathon AI Interview Chatbot")

role = st.sidebar.selectbox("Select Role", ROLES)
itype = st.sidebar.selectbox("Select Interview Type", INTERVIEW_TYPES)

# ---------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:8]
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "last_voice_answer" not in st.session_state:
    st.session_state.last_voice_answer = ""
if "current_combo" not in st.session_state:
    st.session_state.current_combo = ""

# Reset if Role/Type changed
combo = f"{role}_{itype}"
if st.session_state.current_combo != combo:
    st.session_state.shuffled_questions = REAL_QUESTIONS.get(role, {}).get(itype, [])
    st.session_state.q_index = 0
    st.session_state.responses = []
    st.session_state.last_voice_answer = ""
    st.session_state.current_combo = combo

total_qs = len(st.session_state.shuffled_questions)
st.progress(st.session_state.q_index / total_qs if total_qs>0 else 0)

# Retry last answer
if st.session_state.q_index > 0:
    if st.button("Retry Last Answer"):
        st.session_state.q_index -= 1
        st.session_state.responses.pop()
        st.session_state.update({"dummy": random.random()})

# ---------------------------
if st.session_state.q_index < total_qs:
    q = st.session_state.shuffled_questions[st.session_state.q_index]
    st.markdown(f"**Q{st.session_state.q_index+1}: {q}**")

    if st.button("🔊 Play Question"):
        speak_text(q)

    r = sr.Recognizer()
    ans = ""
    if st.button("🎤 Record Answer"):
        with sr.Microphone() as source:
            st.info("Recording... Speak now")
            try:
                audio = r.listen(source, phrase_time_limit=15)
                ans = r.recognize_google(audio)
                st.session_state.last_voice_answer = ans
                st.success(f"You said: {ans}")
            except:
                st.error("Voice not recognized. Type your answer.")

    ans = st.text_area("Your Answer:", value=st.session_state.last_voice_answer,
                       key=f"ans_{st.session_state.q_index}", height=140)

    if st.button("Submit Answer"):
        if not ans.strip():
            st.warning("Enter an answer before submitting.")
        else:
            score, feedback = evaluate_answer(ans, itype)
            st.session_state.responses.append({"question": q, "answer": ans, "score": score, "feedback": feedback})
            st.success(f"Feedback: {feedback}")
            st.info(f"Score: {score}/10")
            st.session_state.q_index += 1
            st.session_state.last_voice_answer = ""
            st.session_state.update({"dummy": random.random()})

# ---------------------------
else:
    st.subheader("✅ Interview Completed!")
    avg = sum([r["score"] for r in st.session_state.responses])/len(st.session_state.responses) if st.session_state.responses else 0
    st.write(f"**Final Score: {avg:.2f}/10**")

    for i,r in enumerate(st.session_state.responses):
        st.write(f"**Q{i+1}:** {r['question']}")
        st.markdown(f"- Answer: {r['answer']}")
        st.markdown(f"- Feedback: {r['feedback']} | Score: {r['score']}/10")
        st.write("---")

    # Download JSON
    st.download_button("Download Report (JSON)", data=json.dumps(st.session_state.responses, indent=2),
                       file_name=f"report_{st.session_state.session_id}.json", mime="application/json")

    # Download PDF
    pdf_bytes = generate_pdf_bytes(st.session_state.responses, st.session_state.session_id)
    st.download_button("Download Report (PDF)", data=pdf_bytes,
                       file_name=f"report_{st.session_state.session_id}.pdf", mime="application/pdf")
