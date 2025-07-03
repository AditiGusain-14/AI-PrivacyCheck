import streamlit as st
import json
import os
import hashlib
import re
import streamlit.components.v1 as components
from ai_engine import chat_with_ai

# ----- Config -----
st.set_page_config(page_title="AI PrivacyCheck", layout="centered")
USER_DATA_FILE = "users.json"
CHAT_HISTORY_DIR = "chat_histories"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# ----- Initialize Session State -----
def init_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "chat_sessions": {},
        "current_session": None,
        "show_actions": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ----- Utilities -----
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored, provided):
    return stored == hash_password(provided)

def get_user_chat_path(username):
    return os.path.join(CHAT_HISTORY_DIR, f"{username}_chat.json")

def load_chat_history(username):
    path = get_user_chat_path(username)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_chat_history(username, chats):
    path = get_user_chat_path(username)
    with open(path, "w") as f:
        json.dump(chats, f)

def show_meter(score):
    percent = min(max(score, 0), 100)
    if percent < 40:
        color = "#2ecc71"
        label = "Safe"
    elif percent < 70:
        color = "#f39c12"
        label = "Moderate Risk"
    else:
        color = "#e74c3c"
        label = "Dangerous"

    html_code = f"""
    <div style='text-align:center; padding: 10px;'>
        <div style='width: 100%; background-color: #eee; border-radius: 8px; overflow: hidden;'>
            <div style='width: {percent}%; background-color: {color}; padding: 10px 0; color: white; font-weight: bold;'>
                {percent}/100 - {label}
            </div>
        </div>
        <div style='font-size: 14px; color: #888; margin-top: 4px;'>Privacy Risk Score</div>
    </div>
    """
    components.html(html_code, height=70)

# ----- Auth Pages -----
def signup():
    st.subheader("Sign Up")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    if st.button("Create Account"):
        if username in users:
            st.error("Username already exists.")
        else:
            users[username] = hash_password(password)
            with open(USER_DATA_FILE, "w") as f:
                json.dump(users, f)
            st.success("Account created. Please log in.")

def login():
    st.subheader("Log In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        if username in users and verify_password(users[username], password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.chat_sessions = load_chat_history(username)
            if st.session_state.chat_sessions:
                st.session_state.current_session = list(st.session_state.chat_sessions.keys())[0]
        else:
            st.error("Invalid credentials.")

# ----- Main Chat App -----
def main_app():
    username = st.session_state.username
    chat_sessions = st.session_state.chat_sessions

    st.sidebar.title(f"👤 {username}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.chat_sessions = {}
        st.session_state.current_session = None
        st.rerun()

    st.sidebar.markdown("### 💾 Sessions")
    for key in list(chat_sessions.keys()):
        with st.sidebar.container():
            cols = st.columns([0.6, 0.2, 0.2])
            with cols[0]:
                if st.button(key, key=f"select_{key}"):
                    st.session_state.current_session = key
            with cols[1]:
                if st.button("✏️", key=f"rename_{key}"):
                    st.session_state.show_actions = key
            with cols[2]:
                if st.button("❌", key=f"delete_{key}"):
                    del chat_sessions[key]
                    if st.session_state.current_session == key:
                        st.session_state.current_session = None
                    save_chat_history(username, chat_sessions)
                    st.rerun()
        if st.session_state.show_actions == key:
            new_name = st.text_input(f"Rename {key}", key=f"input_{key}")
            if new_name and new_name != key:
                chat_sessions[new_name] = chat_sessions.pop(key)
                st.session_state.current_session = new_name
                st.session_state.show_actions = None
                save_chat_history(username, chat_sessions)
                st.rerun()

    if st.sidebar.button("🆕 New Chat"):
        st.session_state.current_session = None

    st.title("🛡️ AI PrivacyCheck")
    st.caption("Chat with your digital privacy advisor.")

    st.markdown("📷 **Upload screenshot (JPG/PNG)**")
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Screenshot", use_container_width=True)
        with st.chat_message("user"):
            st.markdown("Uploaded a screenshot for analysis.")
        with st.chat_message("assistant"):
            st.markdown("Analyzing screenshot for privacy risks...")
            dummy_reply = "**Risk Score:** 72\n\n**Privacy Summary:**\nThe screenshot contains visible tabs, personal email ID, and browser history. Avoid sharing such screenshots online."
            st.markdown(dummy_reply)
            score_match = re.search(r"\*\*Risk Score:\*\* (\d+)", dummy_reply)
            if score_match:
                score = int(score_match.group(1))
                show_meter(score)
            summary_match = re.search(r"\*\*Privacy Summary:\*\*\n(.*)", dummy_reply, re.DOTALL)
            if summary_match:
                st.markdown("### 🔐 Privacy Recommendations")
                st.markdown(summary_match.group(1).strip())

        if st.session_state.current_session is None:
            session_name = "Screenshot Analysis"
            st.session_state.current_session = session_name
            chat_sessions[session_name] = []
        chat_sessions[st.session_state.current_session].append({"role": "user", "content": "Uploaded a screenshot for analysis."})
        chat_sessions[st.session_state.current_session].append({"role": "assistant", "content": dummy_reply})
        save_chat_history(username, chat_sessions)

    session = chat_sessions.get(st.session_state.current_session, [])
    for msg in session:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            score_match = re.search(r"\*\*Risk Score:\*\* (\d+)", msg["content"])
            if score_match:
                show_meter(int(score_match.group(1)))

    if user_input := st.chat_input("Ask me anything about online safety..."):
        if st.session_state.current_session is None:
            session_name = user_input[:20] + "..." if len(user_input) > 20 else user_input
            st.session_state.current_session = session_name
            chat_sessions[session_name] = []

        current_session = chat_sessions[st.session_state.current_session]
        current_session.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        reply = chat_with_ai(current_session)
        current_session.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
            score_match = re.search(r"\*\*Risk Score:\*\* (\d+)", reply)
            if score_match:
                show_meter(int(score_match.group(1)))
            summary_match = re.search(r"\*\*Privacy Summary:\*\*\n(.*)", reply, re.DOTALL)
            if summary_match:
                st.markdown("### 🔐 Privacy Recommendations")
                st.markdown(summary_match.group(1).strip())
        save_chat_history(username, chat_sessions)

# ----- Entry Point -----
init_state()
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

if not st.session_state.logged_in:
    st.title("🔐 AI PrivacyCheck")
    option = st.radio("Choose an option", ["Login", "Sign Up"])
    if option == "Login":
        login()
    else:
        signup()
else:
    main_app()
