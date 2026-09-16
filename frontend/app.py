import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import os
import re
from streamlit_option_menu import option_menu

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Student Marks Analyzer Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
SESSION_TIMEOUT_MINUTES = 30

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    'theme': 'light',
    'token': None,
    'refresh_token': None,
    'user': None,
    'logged_in': False,
    'analyze_result': None,
    'last_activity': None,
    'show_change_password': False,
    'show_verify_otp': False,
    'pending_verify_email': None,
    'pending_verify_phone': None,
    'reset_step': 1,
    'reset_identifier': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# THEME
# ============================================================
def apply_theme():
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0e1117; }

        .main-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d1b4e 100%);
            padding: 2.5rem 2rem; border-radius: 20px; color: white;
            margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            position: relative; overflow: hidden;
        }
        .main-header::before {
            content: ''; position: absolute; top: -50%; right: -20%;
            width: 60%; height: 200%; background: rgba(255,255,255,0.05);
            transform: rotate(30deg); pointer-events: none;
        }
        .main-header h1 { font-size: 2.3rem; font-weight: 700; margin: 0; color: white; }
        .main-header p { margin: 0.5rem 0 0 0; opacity: 0.9; color: white; }

        .metric-card {
            background: #1e1e1e; border: 1px solid #2d2d2d;
            padding: 1.5rem; border-radius: 16px; color: #fafafa;
            transition: all 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
        .metric-card .metric-value { color: #fafafa; font-size: 2rem; font-weight: 700; }
        .metric-card .metric-label { color: #a0a0a0; font-size: 0.9rem; }
        .metric-card .metric-icon { font-size: 2rem; margin-bottom: 0.5rem; }

        .recommendation-card {
            background: #1e1e1e; border-left: 4px solid #667eea;
            padding: 1rem 1.5rem; border-radius: 12px;
            margin: 0.5rem 0; color: #fafafa;
            transition: all 0.3s ease;
        }
        .recommendation-card:hover { transform: translateX(4px); }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        }
        section[data-testid="stSidebar"] * { color: #fafafa !important; }

        p, h1, h2, h3, h4, h5, h6, span, div, label, li { color: #fafafa !important; }
        .stTabs [data-baseweb="tab-list"] { background: #1e1e1e; }
        .stTabs [data-baseweb="tab"] { color: #fafafa !important; }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
        }
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background-color: #1e1e1e !important; color: #fafafa !important;
            border-color: #333 !important;
        }
        .stSelectbox > div > div {
            background-color: #1e1e1e !important; color: #fafafa !important;
        }
        .password-strength-bar { height: 8px; border-radius: 4px; margin: 0.5rem 0; }
        .role-badge {
            display: inline-block; padding: 0.3rem 0.8rem;
            border-radius: 20px; font-size: 0.75rem;
            font-weight: 600; text-transform: uppercase;
        }
        .otp-box {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; padding: 1.5rem; border-radius: 12px;
            text-align: center; font-size: 2rem; letter-spacing: 8px;
            font-weight: bold; margin: 1rem 0;
        }
        .info-banner {
            background: rgba(102, 126, 234, 0.15);
            border-left: 4px solid #667eea;
            padding: 1rem 1.5rem; border-radius: 10px;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }

        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem 2rem; border-radius: 20px; color: white;
            margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(102,126,234,0.3);
            position: relative; overflow: hidden;
        }
        .main-header::before {
            content: ''; position: absolute; top: -50%; right: -20%;
            width: 60%; height: 200%; background: rgba(255,255,255,0.08);
            transform: rotate(30deg); pointer-events: none;
        }
        .main-header h1 { font-size: 2.3rem; font-weight: 700; margin: 0; color: white; }
        .main-header p { margin: 0.5rem 0 0 0; opacity: 0.9; color: white; }

        .metric-card {
            background: white; padding: 1.5rem; border-radius: 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border: 1px solid rgba(0,0,0,0.03);
            transition: all 0.3s ease; height: 100%;
        }
        .metric-card:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .metric-card .metric-value { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
        .metric-card .metric-label { font-size: 0.9rem; color: #6b7280; font-weight: 500; }
        .metric-card .metric-icon { font-size: 2rem; margin-bottom: 0.5rem; }

        .recommendation-card {
            background: #f9fafb; padding: 1rem 1.5rem; border-radius: 12px;
            border-left: 4px solid #667eea; margin: 0.5rem 0;
            transition: all 0.3s ease;
        }
        .recommendation-card:hover { background: #f3f4f6; transform: translateX(4px); }

        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 10px;
            font-weight: 500; padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102,126,234,0.4);
        }

        .password-strength-bar { height: 8px; border-radius: 4px; margin: 0.5rem 0; }
        .role-badge {
            display: inline-block; padding: 0.3rem 0.8rem;
            border-radius: 20px; font-size: 0.75rem;
            font-weight: 600; text-transform: uppercase;
        }
        .otp-box {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; padding: 1.5rem; border-radius: 12px;
            text-align: center; font-size: 2rem; letter-spacing: 8px;
            font-weight: bold; margin: 1rem 0;
        }
        .info-banner {
            background: #eff6ff;
            border-left: 4px solid #667eea;
            padding: 1rem 1.5rem; border-radius: 10px;
            margin: 1rem 0;
        }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)


apply_theme()

# ============================================================
# API HELPERS
# ============================================================
def get_auth_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def handle_response(resp, show_error=True):
    if resp is None:
        return None
    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return {}
    elif resp.status_code == 401:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.user = None
        st.error("🔒 Session expired. Please log in again.")
        st.rerun()
    elif resp.status_code == 403:
        if show_error:
            st.error("🚫 Access denied. You don't have permission.")
    elif resp.status_code == 404:
        if show_error:
            st.error("❓ Resource not found")
    elif resp.status_code == 423:
        if show_error:
            st.error("🔒 Account locked")
    elif resp.status_code == 429:
        st.warning("⏱️ Too many requests. Please wait a moment.")
    else:
        if show_error:
            try:
                st.error(f"❌ Error: {resp.json().get('detail', resp.text)}")
            except Exception:
                st.error(f"❌ Error: {resp.text}")
    return None


def api_get(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=15, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {API_URL}")
        return None
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def api_post(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.post(f"{API_URL}{endpoint}", headers=headers, timeout=30, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend")
        return None
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def api_put(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.put(f"{API_URL}{endpoint}", headers=headers, timeout=15, **kwargs)
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def api_delete(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=15, **kwargs)
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


# ============================================================
# UI HELPERS
# ============================================================
def password_strength_meter(password):
    if not password:
        return
    score = 0
    if len(password) >= 8: score += 20
    if len(password) >= 12: score += 10
    if re.search(r"[A-Z]", password): score += 15
    if re.search(r"[a-z]", password): score += 15
    if re.search(r"\d", password): score += 15
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]", password): score += 15
    if len(set(password)) > 6: score += 10
    score = min(score, 100)

    if score < 40:
        color, label = "#ef4444", "Weak"
    elif score < 60:
        color, label = "#f59e0b", "Fair"
    elif score < 80:
        color, label = "#3b82f6", "Good"
    else:
        color, label = "#10b981", "Strong"

    st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                <span>Password Strength</span>
                <span style="color: {color}; font-weight: 600;">{label}</span>
            </div>
            <div class="password-strength-bar" style="background: #e5e7eb;">
                <div style="height: 100%; width: {score}%; background: {color};
                            border-radius: 4px; transition: all 0.3s;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def get_role_badge(role):
    colors = {
        "admin": ("#dc2626", "👑 Admin"),
        "teacher": ("#2563eb", "👨‍🏫 Teacher"),
        "student": ("#10b981", "🎓 Student"),
        "parent": ("#8b5cf6", "👨‍👩‍👧 Parent"),
    }
    bg, label = colors.get(role, ("#6b7280", role))
    return f'<span class="role-badge" style="background: {bg}; color: white;">{label}</span>'


def render_metric(icon, value, label):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)


# ============================================================
# LOGIN / REGISTER / FORGOT PASSWORD
# ============================================================
if not st.session_state.logged_in:
    st.markdown("""
        <div class="main-header" style="text-align: center;">
            <h1>🎓 Student Marks Analyzer Pro</h1>
            <p>Secure Edition v6.0.0 · OTP Verification</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register, tab_forgot = st.tabs(["🔐 Login", "📝 Register", "🔑 Forgot Password"])

        # ============================================================
        # LOGIN TAB
        # ============================================================
        with tab_login:
            st.markdown("### Welcome Back")
            st.caption("Sign in with your username OR email")

            with st.form("login_form"):
                identifier = st.text_input(
                    "Username or Email",
                    placeholder="admin  OR  admin@example.com",
                    help="Enter either your username or your registered email address"
                )
                password = st.text_input("Password", type="password", placeholder="••••••••")

                submitted = st.form_submit_button("🚀 Login", use_container_width=True)

                if submitted:
                    if not identifier or not password:
                        st.warning("⚠️ Please enter both fields")
                    else:
                        with st.spinner("Authenticating..."):
                            try:
                                r = requests.post(
                                    f"{API_URL}/auth/login",
                                    params={
                                        "username": identifier.strip(),
                                        "password": password,
                                    },
                                    timeout=15,
                                )

                                if r.status_code == 200:
                                    d = r.json()
                                    st.session_state.token = d["access_token"]
                                    st.session_state.refresh_token = d.get("refresh_token")
                                    st.session_state.user = d["user"]
                                    st.session_state.logged_in = True
                                    st.session_state.last_activity = datetime.now()
                                    st.success(f"✅ Welcome, {d['user'].get('full_name', d['user']['username'])}!")
                                    time.sleep(0.5)
                                    st.rerun()
                                elif r.status_code == 423:
                                    st.error("🔒 " + r.json().get("detail", "Account locked"))
                                elif r.status_code == 403:
                                    st.error("🚫 " + r.json().get("detail", "Account disabled"))
                                elif r.status_code == 401:
                                    st.error("❌ Invalid username/email or password")
                                elif r.status_code == 429:
                                    st.warning("⏱️ Too many attempts. Wait a minute.")
                                else:
                                    st.error(f"❌ Error: {r.text[:200]}")
                            except requests.exceptions.ConnectionError:
                                st.error("❌ Cannot connect to backend. Is it running?")
                            except Exception as e:
                                st.error(f"❌ {str(e)}")

            st.markdown("---")
            st.info("""
            **🔐 Default Admin Credentials**
            - Username: `admin` **OR** email: `admin@example.com`
            - Password: `Admin@123`

            ⚠️ Change password after first login!
            """)

        # ============================================================
        # REGISTER TAB
        # ============================================================
        with tab_register:
            st.markdown("### Create Account")

            reg_role = st.selectbox(
                "I am a...",
                ["teacher", "student", "parent"],
                key="reg_role_select",
                help="Admin accounts must be created by existing admins"
            )

            with st.form("register_form"):
                new_username = st.text_input(
                    "👤 Username *",
                    placeholder="johndoe",
                    help="3-30 chars, letters/numbers/underscores only"
                )
                new_email = st.text_input(
                    "📧 Email *",
                    placeholder="john@example.com",
                    help="You'll receive a verification OTP here"
                )
                new_phone = st.text_input(
                    "📱 Phone (optional)",
                    placeholder="+91 9876543210",
                    help="Include country code. You'll receive an SMS OTP (console in dev mode)."
                )
                new_fullname = st.text_input("📝 Full Name", placeholder="John Doe")

                col_a, col_b = st.columns(2)
                with col_a:
                    new_password = st.text_input(
                        "🔑 Password *",
                        type="password",
                        placeholder="Min 8 chars",
                        help="8+ chars, uppercase, lowercase, digit, special char"
                    )
                with col_b:
                    confirm_password = st.text_input(
                        "🔑 Confirm *",
                        type="password",
                        placeholder="Repeat password"
                    )

                if new_password:
                    password_strength_meter(new_password)
                    st.caption("💡 8+ chars with uppercase, lowercase, digit, and special char")

                register_submitted = st.form_submit_button("📝 Create Account", use_container_width=True)

                if register_submitted:
                    errors = []
                    if not new_username or len(new_username) < 3:
                        errors.append("Username must be at least 3 characters")
                    elif not re.match(r'^[a-zA-Z0-9_]+$', new_username):
                        errors.append("Username: letters, numbers, underscores only")

                    if not new_email or "@" not in new_email:
                        errors.append("Valid email required")

                    if not new_password or len(new_password) < 8:
                        errors.append("Password must be 8+ characters")
                    elif new_password != confirm_password:
                        errors.append("Passwords don't match")

                    if errors:
                        for e in errors:
                            st.error(f"❌ {e}")
                    else:
                        with st.spinner("Creating account..."):
                            try:
                                payload = {
                                    "username": new_username.lower().strip(),
                                    "email": new_email.strip(),
                                    "phone": new_phone.strip() or None,
                                    "password": new_password,
                                    "full_name": new_fullname or new_username,
                                    "role": reg_role,
                                }
                                r = requests.post(f"{API_URL}/auth/register", json=payload, timeout=15)

                                if r.status_code == 200:
                                    d = r.json()
                                    st.session_state.pending_verify_email = d["email"]
                                    st.session_state.pending_verify_phone = d.get("phone")
                                    st.session_state.show_verify_otp = True
                                    st.success(f"✅ {d['message']}")
                                    st.info("📧 Check your email for the verification OTP. If DEV_MODE, check the backend console.")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                elif r.status_code == 400:
                                    st.error(f"❌ {r.json().get('detail', 'Registration failed')}")
                                elif r.status_code == 429:
                                    st.warning("⏱️ Too many attempts. Wait a minute.")
                                else:
                                    st.error(f"❌ Error: {r.text[:200]}")
                            except Exception as e:
                                st.error(f"❌ {str(e)}")

            # OTP verification section
            if st.session_state.get("show_verify_otp") and st.session_state.get("pending_verify_email"):
                st.markdown("---")
                st.markdown("### 🔐 Verify Your Account")
                st.markdown(f"""
                    <div class="info-banner">
                        📧 OTP sent to <b>{st.session_state.pending_verify_email}</b><br>
                        {f"📱 OTP sent to <b>{st.session_state.pending_verify_phone}</b> (check console in dev mode)" if st.session_state.get('pending_verify_phone') else ""}
                    </div>
                """, unsafe_allow_html=True)

                # Email verification
                st.markdown("#### 📧 Email Verification")
                email_otp = st.text_input("Enter Email OTP", key="email_otp_input",
                                          max_chars=6, placeholder="123456")

                if st.button("✅ Verify Email", key="verify_email_btn", use_container_width=True):
                    if not email_otp:
                        st.warning("Please enter the OTP")
                    else:
                        try:
                            r = requests.post(f"{API_URL}/auth/verify-otp", json={
                                "identifier": st.session_state.pending_verify_email,
                                "otp_code": email_otp.strip(),
                                "purpose": "verification",
                            }, timeout=15)
                            if r.status_code == 200:
                                st.success("✅ Email verified! You can now log in.")
                                st.balloons()
                            else:
                                st.error(r.json().get("detail", "Invalid OTP"))
                        except Exception as e:
                            st.error(f"Error: {e}")

                # Phone verification (if provided)
                if st.session_state.get("pending_verify_phone"):
                    st.markdown("#### 📱 Phone Verification")
                    phone_otp = st.text_input("Enter Phone OTP", key="phone_otp_input",
                                              max_chars=6, placeholder="123456")

                    if st.button("✅ Verify Phone", key="verify_phone_btn", use_container_width=True):
                        if not phone_otp:
                            st.warning("Please enter the OTP")
                        else:
                            try:
                                r = requests.post(f"{API_URL}/auth/verify-otp", json={
                                    "identifier": st.session_state.pending_verify_phone,
                                    "otp_code": phone_otp.strip(),
                                    "purpose": "phone_verification",
                                }, timeout=15)
                                if r.status_code == 200:
                                    st.success("✅ Phone verified!")
                                else:
                                    st.error(r.json().get("detail", "Invalid OTP"))
                            except Exception as e:
                                st.error(f"Error: {e}")

                if st.button("✖️ Close", key="close_verify"):
                    st.session_state.show_verify_otp = False
                    st.rerun()

        # ============================================================
        # FORGOT PASSWORD TAB
        # ============================================================
        with tab_forgot:
            st.markdown("### Reset Your Password")
            st.caption("Enter your email or phone to receive an OTP")

            if st.session_state.reset_step == 1:
                reset_id = st.text_input(
                    "Email or Phone",
                    placeholder="you@example.com  OR  +919876543210",
                    key="reset_identifier_input"
                )

                if st.button("📧 Send OTP", use_container_width=True, key="send_reset_otp"):
                    if not reset_id:
                        st.warning("Please enter your email or phone")
                    else:
                        with st.spinner("Sending OTP..."):
                            try:
                                r = requests.post(f"{API_URL}/auth/send-otp", json={
                                    "identifier": reset_id.strip(),
                                    "purpose": "reset_password",
                                }, timeout=15)
                                if r.status_code == 200:
                                    d = r.json()
                                    st.session_state.reset_identifier = reset_id.strip()
                                    st.session_state.reset_step = 2
                                    st.success(f"✅ {d['message']}")
                                    if d.get("delivery") == "console":
                                        st.info("💡 Check the backend console for the OTP")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(r.json().get("detail", "Failed to send OTP"))
                            except Exception as e:
                                st.error(f"Error: {e}")

            elif st.session_state.reset_step == 2:
                st.markdown(f"""
                    <div class="info-banner">
                        📧 OTP sent to <b>{st.session_state.reset_identifier}</b>
                    </div>
                """, unsafe_allow_html=True)

                otp_code = st.text_input("Enter OTP", max_chars=6, placeholder="123456", key="reset_otp_input")
                new_pw = st.text_input("New Password", type="password", key="reset_new_pw")

                if new_pw:
                    password_strength_meter(new_pw)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Reset Password", use_container_width=True, key="do_reset"):
                        if not otp_code or not new_pw:
                            st.warning("Fill both fields")
                        elif len(new_pw) < 8:
                            st.warning("Password must be 8+ characters")
                        else:
                            try:
                                r = requests.post(f"{API_URL}/auth/reset-password", json={
                                    "identifier": st.session_state.reset_identifier,
                                    "otp_code": otp_code.strip(),
                                    "new_password": new_pw,
                                }, timeout=15)
                                if r.status_code == 200:
                                    st.success("✅ Password reset! Please log in.")
                                    st.session_state.reset_step = 1
                                    st.session_state.reset_identifier = None
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(r.json().get("detail", "Reset failed"))
                            except Exception as e:
                                st.error(f"Error: {e}")

                with c2:
                    if st.button("↩️ Back", use_container_width=True, key="reset_back"):
                        st.session_state.reset_step = 1
                        st.rerun()

    st.stop()

# ============================================================
# SESSION TIMEOUT
# ============================================================
if st.session_state.last_activity:
    elapsed = (datetime.now() - st.session_state.last_activity).total_seconds() / 60
    if elapsed > SESSION_TIMEOUT_MINUTES:
        st.warning(f"⏱️ Session expired after {SESSION_TIMEOUT_MINUTES} min of inactivity")
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.user = None
        time.sleep(1)
        st.rerun()

st.session_state.last_activity = datetime.now()

# ============================================================
# CHANGE PASSWORD PAGE
# ============================================================
if st.session_state.show_change_password:
    st.markdown("""
        <div class="main-header">
            <h1>🔑 Change Password</h1>
            <p>Update your account password</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("change_password_form"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")

            if new_pw:
                password_strength_meter(new_pw)

            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
            with c2:
                cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submitted:
                if not old_pw or not new_pw or not confirm_pw:
                    st.error("Please fill all fields")
                elif new_pw != confirm_pw:
                    st.error("New passwords don't match")
                elif len(new_pw) < 8:
                    st.error("Password must be 8+ characters")
                else:
                    resp = api_post("/auth/change-password",
                                    json={"old_password": old_pw, "new_password": new_pw})
                    if resp and resp.status_code == 200:
                        st.success("✅ Password changed!")
                        time.sleep(1)
                        st.session_state.show_change_password = False
                        st.rerun()
                    elif resp and resp.status_code == 400:
                        st.error(resp.json().get("detail", "Error"))

            if cancelled:
                st.session_state.show_change_password = False
                st.rerun()

    st.stop()

# ============================================================
# USER INFO
# ============================================================
user = st.session_state.user
user_role = user.get("role", "teacher")
user_name = user.get("full_name") or user["username"]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: white; margin: 0;">🎓 Pro Analyzer</h2>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.85rem;">v6.0.0</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 10px; margin-bottom: 1rem;">
            <p style="color: white; margin: 0; font-weight: 600;">👤 {user_name}</p>
            <p style="color: rgba(255,255,255,0.7); margin: 0.25rem 0 0 0; font-size: 0.8rem;">@{user['username']}</p>
            <div style="margin-top: 0.5rem;">{get_role_badge(user_role)}</div>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown("**🌙 Dark Mode**")
    with col_b:
        is_dark = st.session_state.theme == 'dark'
        toggled = st.toggle("dark", value=is_dark, key="theme_toggle", label_visibility="collapsed")
        if toggled != is_dark:
            st.session_state.theme = 'dark' if toggled else 'light'
            st.rerun()

    st.markdown("---")

    # Role-based menu
    if user_role == "admin":
        menu_options = [
            "🏠 Dashboard", "📝 Analyze", "📚 Database", "📊 Analytics",
            "📈 Reports", "📅 Attendance", "🔔 Notifications",
            "🔄 Compare", "📉 Trends", "📤 Import/Export",
            "👥 Users", "📋 Audit Log"
        ]
        menu_icons = [
            "house", "pencil-square", "database", "bar-chart",
            "file-earmark-text", "calendar", "bell",
            "arrow-left-right", "graph-up", "cloud-upload",
            "people", "journal-text"
        ]
    elif user_role == "teacher":
        menu_options = [
            "🏠 Dashboard", "📝 Analyze", "📚 Database", "📊 Analytics",
            "📈 Reports", "📅 Attendance", "🔔 Notifications",
            "🔄 Compare", "📉 Trends", "📤 Import/Export"
        ]
        menu_icons = [
            "house", "pencil-square", "database", "bar-chart",
            "file-earmark-text", "calendar", "bell",
            "arrow-left-right", "graph-up", "cloud-upload"
        ]
    elif user_role == "parent":
        menu_options = ["🏠 Dashboard", "👨‍👩‍👧 My Children", "📊 Progress", "📅 Attendance", "🔔 Notifications"]
        menu_icons = ["house", "people", "bar-chart", "calendar", "bell"]
    else:
        menu_options = ["🏠 Dashboard", "📊 My Results", "📉 My Progress", "📅 My Attendance", "🔔 Notifications"]
        menu_icons = ["house", "bar-chart", "graph-up", "calendar", "bell"]

    selected = option_menu(
        menu_title=None,
        options=menu_options,
        icons=menu_icons,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#667eea", "font-size": "1.1rem"},
            "nav-link": {
                "font-size": "0.9rem", "text-align": "left",
                "margin": "0.15rem 0", "padding": "0.6rem 0.8rem",
                "border-radius": "8px", "color": "rgba(255,255,255,0.85)"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white", "font-weight": "500"
            }
        }
    )

    st.markdown("---")

    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            st.success("🟢 System Online")
        else:
            st.error("🔴 System Offline")
    except Exception:
        st.error("🔴 Connection Failed")

    st.markdown("---")

    if st.button("🔑 Change Password", use_container_width=True):
        st.session_state.show_change_password = True
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        try:
            api_post("/auth/logout")
        except Exception:
            pass
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ============================================================
# PAGE: DASHBOARD
# ============================================================
if selected == "🏠 Dashboard":
    st.markdown(f"""
        <div class="main-header">
            <h1>🏠 Welcome, {user_name}!</h1>
            <p>Your personalized dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/stats/overall")
    stats = handle_response(resp) if resp else None

    if stats and "total_students" in stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric("👥", stats["total_students"], "Total Students")
        with c2:
            render_metric("📈", f"{stats['average_of_averages']:.1f}", "Average Score")
        with c3:
            render_metric("✅", f"{stats['pass_rate']:.0f}%", "Pass Rate")
        with c4:
            render_metric("🏆", f"{stats['distinction_rate']:.0f}%", "Distinction")

        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            if stats.get("grade_distribution"):
                st.markdown("### 📊 Grade Distribution")
                gdf = pd.DataFrame({
                    "Grade": list(stats["grade_distribution"].keys()),
                    "Count": list(stats["grade_distribution"].values())
                })
                fig = px.pie(gdf, values="Count", names="Grade", hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if stats.get("top_performers"):
                st.markdown("### 🏆 Top Performers")
                for i, s in enumerate(stats["top_performers"][:5], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
                    st.markdown(f"{medal} **{s['name']}** — {s['average']:.1f}% ({s['grade']})")

        # Recent notifications
        notif_resp = api_get("/notifications", params={"limit": 5})
        notif_data = handle_response(notif_resp, show_error=False) if notif_resp else None
        if notif_data and notif_data.get("count", 0) > 0:
            st.markdown("---")
            st.markdown("### 🔔 Recent Notifications")
            for n in notif_data["notifications"]:
                icon = {"Achievement": "🏆", "Warning": "⚠️", "Success": "✅", "Info": "ℹ️"}.get(n["type"], "📌")
                st.markdown(f"{icon} **{n['type']}** — {n['message']}")
    else:
        st.info("👋 Welcome! Get started by adding students or importing data.")
        if user_role in ["admin", "teacher"]:
            st.markdown("""
            **Quick Start:**
            1. 📝 Go to **Analyze** to add student marks
            2. 📤 Use **Import/Export** for bulk data
            3. 📊 View **Analytics** for insights
            4. 👥 Manage users in **Users** (admin only)
            """)

# ============================================================
# PAGE: ANALYZE
# ============================================================
elif selected == "📝 Analyze":
    st.markdown("""
        <div class="main-header">
            <h1>📝 Analyze Student Performance</h1>
            <p>Enter marks and get AI-powered insights</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        student_name = st.text_input("👤 Student Name *", placeholder="John Doe", key="an_name")

        c1, c2, c3 = st.columns(3)
        with c1:
            semester = st.selectbox("Semester", ["Fall 2024", "Spring 2024", "Summer 2024", "Fall 2023"], key="an_sem")
        with c2:
            batch_year = st.selectbox("Batch Year", ["2024", "2023", "2022", "2021", "2020"], key="an_year")
        with c3:
            department = st.selectbox("Department", [
                "Computer Science", "Mathematics", "Physics", "Chemistry",
                "Biology", "Engineering", "Business"
            ], key="an_dept")

        st.markdown("### 📚 Subject Details")
        st.caption("⚠️ Subject names must be meaningful (e.g., 'Mathematics', 'Physics 101')")
        num_subjects = st.slider("Number of Subjects", 1, 15, 5, key="an_num")

        marks = []
        subject_names = []
        cols = st.columns(3)
        for i in range(num_subjects):
            with cols[i % 3]:
                subj = st.text_input(f"Subject {i+1}", placeholder=f"e.g., Mathematics",
                                     key=f"an_subj_{i}", label_visibility="collapsed")
                mark = st.number_input(f"Marks {i+1}", 0, 100, 0, 1,
                                      key=f"an_mark_{i}", label_visibility="collapsed")
                marks.append(mark)
                subject_names.append(subj or f"Subject {i+1}")

    with col2:
        st.markdown("### ⚙️ Settings")
        passing = st.slider("Passing Threshold", 0, 60, 40, 5, key="an_pass")
        scheme = st.selectbox("Grade Scheme", ["standard", "strict", "lenient"], key="an_scheme")

        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        if sum(marks) > 0:
            avg = sum(marks) / len(marks)
            st.metric("Total", f"{sum(marks):.0f}")
            st.metric("Average", f"{avg:.1f}%")

    if st.button("🚀 Analyze Performance", type="primary", use_container_width=True):
        if sum(marks) == 0:
            st.warning("⚠️ Please enter marks")
        elif not student_name:
            st.warning("⚠️ Please enter student name")
        else:
            with st.spinner("Analyzing..."):
                payload = {
                    "marks": marks,
                    "student_name": student_name,
                    "subject_names": subject_names,
                    "passing_threshold": passing,
                    "grade_scheme": scheme,
                    "semester": semester,
                    "batch_year": batch_year,
                    "department": department
                }
                resp = api_post("/analyze", json=payload)
                data = handle_response(resp) if resp else None
                if data:
                    st.session_state.analyze_result = data
                    st.success("✅ Analysis complete!")
                    st.balloons()

    # Display result
    if st.session_state.analyze_result:
        result = st.session_state.analyze_result
        st.markdown("---")

        grade_color = {
            "A+": "#10b981", "A": "#34d399", "B": "#fbbf24",
            "C": "#f59e0b", "D": "#f97316", "E": "#ef4444", "F": "#dc2626"
        }.get(result["grade"], "#667eea")

        st.markdown(f"""
            <div style="text-align: center; padding: 1rem 0;">
                <h2>Overall Grade</h2>
                <div style="font-size: 3rem; font-weight: 700; padding: 1.5rem 3rem;
                            border-radius: 100px; display: inline-block;
                            background: linear-gradient(135deg, {grade_color}, {grade_color}dd);
                            color: white; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                    {result['grade']} <span style="font-size: 1.5rem;">(GPA: {result['grade_points']})</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric("📊", f"{result['average']:.1f}%", "Average")
        with c2:
            render_metric("📈", f"{result['total_marks']:.0f}", "Total")
        with c3:
            render_metric("🏆", f"{result['highest']:.0f}", "Highest")
        with c4:
            render_metric("✅", f"{result['pass_percentage']:.0f}%", "Pass Rate")

        st.markdown("### 📚 Subject-wise Performance")
        df = pd.DataFrame(result["subject_wise"])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["subject"], y=df["marks"],
            marker_color=df["marks"].apply(lambda x: "#10b981" if x >= passing else "#ef4444"),
            text=df["marks"], textposition="outside"
        ))
        fig.add_hline(y=passing, line_dash="dash", line_color="#f59e0b")
        fig.update_layout(yaxis_range=[0, 105], showlegend=False,
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        if "ai_insights" in result:
            st.markdown("### 🤖 AI Insights")
            t1, t2, t3 = st.tabs(["💪 Strengths", "📈 Recommendations", "🎯 Tips"])
            with t1:
                for s in result["ai_insights"]["strengths"]:
                    st.success(f"**{s['subject']}**: {s['marks']} - {s['level']}")
                if not result["ai_insights"]["strengths"]:
                    st.info("No strengths identified")
            with t2:
                for r in result["ai_insights"]["recommendations"]:
                    st.info(f"**{r['action']}**: {r['details']}")
            with t3:
                for t in result["ai_insights"]["study_tips"]:
                    st.info(f"📌 {t}")

        st.markdown("### 💡 Recommendations")
        for rec in result["recommendations"]:
            st.markdown(f'<div class="recommendation-card">{rec}</div>', unsafe_allow_html=True)

        if st.button("💾 Save Student Record", type="primary", use_container_width=True):
            save_data = {
                "name": result["student_name"],
                "marks": marks,
                "subjects": subject_names,
                "grade": result["grade"],
                "average": result["average"],
                "total_marks": result["total_marks"],
                "timestamp": datetime.now().isoformat(),
                "semester": semester,
                "batch_year": batch_year,
                "department": department
            }
            resp = api_post("/students/save", json=save_data)
            if resp and resp.status_code == 200:
                st.success("✅ Record saved!")
                st.balloons()

# ============================================================
# PAGE: DATABASE
# ============================================================
elif selected == "📚 Database":
    st.markdown("""
        <div class="main-header">
            <h1>📚 Student Database</h1>
            <p>View and manage student records</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/students", params={"limit": 100})
    data = handle_response(resp) if resp else None

    if data and data["count"] > 0:
        st.success(f"📊 Total: {data['count']} students")

        df = pd.DataFrame(data["students"])
        display_df = df.copy()
        if 'marks' in display_df.columns:
            display_df['marks'] = display_df['marks'].apply(
                lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x
            )
        if 'subjects' in display_df.columns:
            display_df['subjects'] = display_df['subjects'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )

        st.dataframe(display_df, use_container_width=True)

        st.markdown("### 📄 Generate Report Card")
        opts = {f"{s['name']} (ID: {s['id']})": s['id'] for s in data["students"]}
        c1, c2 = st.columns([3, 1])
        with c1:
            sel = st.selectbox("Student", list(opts.keys()), key="pdf_sel")
        with c2:
            if st.button("📄 PDF", use_container_width=True):
                sid = opts[sel]
                resp = api_get(f"/students/{sid}/report-card")
                if resp and resp.status_code == 200:
                    st.download_button("💾 Download", data=resp.content,
                                      file_name=f"report_{sid}.pdf", mime="application/pdf")
    else:
        st.info("📋 No students in database")

# ============================================================
# PAGE: ANALYTICS
# ============================================================
elif selected == "📊 Analytics":
    st.markdown("""
        <div class="main-header">
            <h1>📊 Analytics Dashboard</h1>
            <p>Comprehensive insights</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/analytics/dashboard")
    data = handle_response(resp) if resp else None

    if data and data.get("has_data"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric("👥", data["total_students"], "Students")
        with c2:
            render_metric("📈", f"{data['overall_average']:.1f}", "Average")
        with c3:
            render_metric("✅", f"{data['pass_rate']:.1f}%", "Pass Rate")
        with c4:
            render_metric("🏆", f"{data['distinction_rate']:.1f}%", "Distinction")

        st.markdown("---")
        c1, c2 = st.columns(2)

        with c1:
            if data.get("grade_distribution"):
                st.markdown("### 📊 Grades")
                gdf = pd.DataFrame({
                    "Grade": list(data["grade_distribution"].keys()),
                    "Count": list(data["grade_distribution"].values())
                })
                fig = px.pie(gdf, values="Count", names="Grade", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if data.get("grade_ranges"):
                st.markdown("### 📊 Ranges")
                rdf = pd.DataFrame({
                    "Range": list(data["grade_ranges"].keys()),
                    "Count": list(data["grade_ranges"].values())
                })
                fig = px.bar(rdf, x="Range", y="Count", color="Count", color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)

        if data.get("subject_analytics"):
            st.markdown("### 📚 Subject Performance")
            subj_df = pd.DataFrame(data["subject_analytics"])
            fig = px.bar(subj_df, x="subject", y="average", color="average",
                        color_continuous_scale="RdYlGn", text="average")
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig.update_layout(yaxis_range=[0, 105], showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        if data.get("top_performers"):
            st.markdown("### 🏆 Top Performers")
            st.dataframe(pd.DataFrame(data["top_performers"]), use_container_width=True)
    else:
        st.info("📊 No data available. Add students first.")

# ============================================================
# PAGE: REPORTS
# ============================================================
elif selected == "📈 Reports":
    st.markdown("""
        <div class="main-header">
            <h1>📈 Reports & Export</h1>
            <p>Download your data</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        if st.button("📊 Export CSV", use_container_width=True):
            resp = api_get("/export/csv")
            if resp and resp.status_code == 200:
                st.download_button(
                    "💾 Download CSV",
                    data=resp.content,
                    file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    with c2:
        if st.button("📋 Export JSON", use_container_width=True):
            resp = api_get("/export/json")
            if resp and resp.status_code == 200:
                st.download_button(
                    "💾 Download JSON",
                    data=json.dumps(resp.json(), indent=2),
                    file_name=f"students_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

    st.markdown("---")
    st.markdown("### 📊 Statistics Summary")
    resp = api_get("/stats/overall")
    stats = handle_response(resp) if resp else None
    if stats and "total_students" in stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Students", stats["total_students"])
        with c2:
            st.metric("Avg Score", f"{stats['average_of_averages']:.2f}")
        with c3:
            st.metric("Pass Rate", f"{stats['pass_rate']:.1f}%")
        with c4:
            st.metric("Distinction", f"{stats['distinction_rate']:.1f}%")

# ============================================================
# PAGE: ATTENDANCE
# ============================================================
elif selected == "📅 Attendance" or selected == "📅 My Attendance":
    st.markdown("""
        <div class="main-header">
            <h1>📅 Attendance</h1>
            <p>Track and view attendance</p>
        </div>
    """, unsafe_allow_html=True)

    if user_role in ["admin", "teacher"]:
        tab1, tab2, tab3 = st.tabs(["📝 Record", "📊 Stats", "🏫 Overall"])

        with tab1:
            resp = api_get("/students", params={"limit": 500})
            data = handle_response(resp, show_error=False) if resp else None
            students = data.get("students", []) if data else []

            if students:
                c1, c2 = st.columns(2)
                with c1:
                    att_date = st.date_input("Date", datetime.now(), key="att_d")
                with c2:
                    att_subject = st.text_input("Subject (optional)", key="att_s")

                opts = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
                sel = st.selectbox("Student", list(opts.keys()), key="att_sel")

                c1, c2 = st.columns(2)
                with c1:
                    status = st.selectbox("Status", ["Present", "Absent", "Late", "Excused"], key="att_stat")
                with c2:
                    notes = st.text_input("Notes", key="att_note")

                if st.button("📝 Record", type="primary", use_container_width=True):
                    payload = {
                        "student_id": opts[sel],
                        "date": att_date.isoformat(),
                        "status": status,
                        "subject": att_subject or None,
                        "notes": notes or None
                    }
                    resp = api_post("/attendance", json=payload)
                    if resp and resp.status_code == 200:
                        st.success("✅ Recorded!")
                        st.balloons()
            else:
                st.info("No students available")

        with tab2:
            resp = api_get("/students", params={"limit": 500})
            data = handle_response(resp, show_error=False) if resp else None
            students = data.get("students", []) if data else []

            if students:
                opts = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
                sel = st.selectbox("Student", list(opts.keys()), key="stats_sel")

                if st.button("📊 Load Stats", key="stats_btn"):
                    sid = opts[sel]
                    resp = api_get(f"/attendance/{sid}/stats")
                    stats = handle_response(resp) if resp else None
                    if stats:
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.metric("Total", stats.get("total_days", 0))
                        with c2:
                            st.metric("Present", stats.get("present", 0))
                        with c3:
                            st.metric("Absent", stats.get("absent", 0))
                        with c4:
                            st.metric("Rate", f"{stats.get('attendance_rate', 0):.1f}%")

                        if stats.get("total_days", 0) > 0:
                            st.progress(stats["attendance_rate"] / 100)

        with tab3:
            if st.button("📊 Overall Stats"):
                resp = api_get("/attendance/stats/overall")
                data = handle_response(resp) if resp else None
                if data and data.get("total_records", 0) > 0:
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Records", data["total_records"])
                    with c2:
                        st.metric("Present", data["present"])
                    with c3:
                        st.metric("Absent", data["absent"])
                    with c4:
                        st.metric("Rate", f"{data['overall_rate']:.1f}%")
    else:
        st.info("Viewing your attendance summary")
        resp = api_get("/attendance/stats/overall")
        data = handle_response(resp) if resp else None
        if data:
            st.metric("Overall Rate", f"{data.get('overall_rate', 0):.1f}%")

# ============================================================
# PAGE: NOTIFICATIONS
# ============================================================
elif selected == "🔔 Notifications":
    st.markdown("""
        <div class="main-header">
            <h1>🔔 Notifications</h1>
            <p>Your alerts and updates</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("✅ Mark All Read", use_container_width=True):
            resp = api_put("/notifications/mark-all-read")
            if resp and resp.status_code == 200:
                st.success("Done!")
                st.rerun()

    resp = api_get("/notifications", params={"limit": 100})
    data = handle_response(resp) if resp else None

    if data:
        st.info(f"📬 Total: {data['count']} | Unread: {data['unread_count']}")

        for n in data.get("notifications", []):
            icon = {"Achievement": "🏆", "Warning": "⚠️", "Success": "✅", "Info": "ℹ️"}.get(n["type"], "📌")
            dot = "🔵" if not n["is_read"] else "⚪"

            with st.container():
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"{dot} **{icon} {n['type']}** — {n['message']}")
                    st.caption(f"🕐 {n['created_at']}")
                with c2:
                    if not n["is_read"]:
                        if st.button("Read", key=f"r_{n['id']}"):
                            api_put(f"/notifications/mark-read/{n['id']}")
                            st.rerun()
                st.divider()

# ============================================================
# PAGE: COMPARE
# ============================================================
elif selected == "🔄 Compare":
    st.markdown("""
        <div class="main-header">
            <h1>🔄 Compare Students</h1>
            <p>Side-by-side comparison</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/students", params={"limit": 100})
    data = handle_response(resp) if resp else None

    if data and data["count"] >= 2:
        opts = {f"{s['name']} (ID: {s['id']})": s['id'] for s in data["students"]}
        selected_students = st.multiselect(
            "Select students (min 2)",
            list(opts.keys()),
            default=list(opts.keys())[:min(3, len(opts))]
        )

        if len(selected_students) >= 2 and st.button("📊 Compare", type="primary"):
            ids = [opts[s] for s in selected_students]
            resp = api_post("/students/compare", json={"student_ids": ids})
            result = handle_response(resp) if resp else None

            if result:
                st.success(f"🏆 Winner: **{result['winner']['name']}** ({result['winner']['average']:.2f}%)")

                df = pd.DataFrame(result["comparison"])
                st.dataframe(df, use_container_width=True)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[c["name"] for c in result["comparison"]],
                    y=[c["average"] for c in result["comparison"]],
                    marker_color=["#10b981" if c["name"] == result["winner"]["name"] else "#667eea"
                                  for c in result["comparison"]],
                    text=[f"{c['average']:.1f}" for c in result["comparison"]],
                    textposition="outside"
                ))
                fig.update_layout(yaxis_range=[0, 105], showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least 2 students")

# ============================================================
# PAGE: TRENDS
# ============================================================
elif selected == "📉 Trends" or selected == "📉 My Progress":
    st.markdown("""
        <div class="main-header">
            <h1>📉 Performance Trends</h1>
            <p>Track progress over time</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/students", params={"limit": 100})
    data = handle_response(resp) if resp else None

    if data and data["count"] > 0:
        opts = {f"{s['name']} (ID: {s['id']})": s['id'] for s in data["students"]}
        sel = st.selectbox("Select Student", list(opts.keys()), key="tr_sel")

        if st.button("📊 Analyze Trends", type="primary"):
            sid = opts[sel]
            resp = api_get(f"/trends/{sid}")
            result = handle_response(resp) if resp else None

            if result:
                if "error" in result:
                    st.error(result["error"])
                elif "Not enough" in result.get("message", ""):
                    st.warning(result["message"])
                else:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("First", f"{result['first_average']:.2f}")
                    with c2:
                        st.metric("Current", f"{result['current_average']:.2f}")
                    with c3:
                        st.metric("Change", f"{result['improvement']:+.2f}",
                                 delta=f"{result['improvement']:+.2f}")

                    st.markdown(f"### {result['trend_direction']}")

                    if result.get("trends"):
                        df = pd.DataFrame(result["trends"])
                        if "created_at" in df.columns:
                            df["created_at"] = pd.to_datetime(df["created_at"])
                            fig = px.line(df, x="created_at", y="average", markers=True)
                            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PAGE: IMPORT/EXPORT
# ============================================================
elif selected == "📤 Import/Export":
    st.markdown("""
        <div class="main-header">
            <h1>📤 Import & Export</h1>
            <p>Bulk operations</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📥 Import", "📤 Export"])

    with tab1:
        st.markdown("### 📥 Bulk Import Students from CSV")

        c1, c2 = st.columns([3, 1])
        with c2:
            if st.button("📋 Template", use_container_width=True):
                resp = api_get("/students/import-template")
                if resp and resp.status_code == 200:
                    st.download_button("💾 Save Template", data=resp.content,
                                      file_name="template.csv", mime="text/csv")

        csv_help = (
            "**CSV Format:**\n\n"
            "```\n"
            "name,marks,subjects,semester,department,batch_year\n"
            'John Doe,"85,92,78","Mathematics,Physics,English",Fall 2024,CS,2024\n'
            "```\n\n"
            "**Required columns:** `name`, `marks`, `subjects`\n\n"
            "**Optional columns:** `semester`, `department`, `batch_year`\n\n"
            "**Note:** `marks` and `subjects` are comma-separated (wrap in quotes)\n\n"
            "⚠️ Subject names must be meaningful (no gibberish)"
        )
        st.markdown(csv_help)

        uploaded = st.file_uploader("Choose CSV file", type=["csv"])
        if uploaded:
            try:
                preview = pd.read_csv(uploaded)
                st.markdown("**Preview:**")
                st.dataframe(preview.head(10), use_container_width=True)
                st.caption(f"Rows: {len(preview)}")
                uploaded.seek(0)
            except Exception as e:
                st.error(f"Preview failed: {e}")

            if st.button("🚀 Import Now", type="primary", use_container_width=True):
                with st.spinner("Importing..."):
                    try:
                        files = {"file": (uploaded.name, uploaded.getvalue(), "text/csv")}
                        resp = api_post("/students/import-csv", files=files)
                        result = handle_response(resp) if resp else None
                        if result:
                            st.success(result["message"])
                            if result.get("failed"):
                                with st.expander(f"⚠️ {result['failed_count']} failures"):
                                    for e in result["failed"]:
                                        st.write(f"- {e}")
                            st.balloons()
                    except Exception as e:
                        st.error(f"Import failed: {e}")

    with tab2:
        st.markdown("### 📤 Export All Data")
        c1, c2 = st.columns(2)

        with c1:
            if st.button("📊 Download CSV", use_container_width=True, key="exp_csv"):
                resp = api_get("/export/csv")
                if resp and resp.status_code == 200:
                    st.download_button(
                        "💾 Save CSV",
                        data=resp.content,
                        file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

        with c2:
            if st.button("📋 Download JSON", use_container_width=True, key="exp_json"):
                resp = api_get("/export/json")
                if resp and resp.status_code == 200:
                    st.download_button(
                        "💾 Save JSON",
                        data=json.dumps(resp.json(), indent=2),
                        file_name=f"students_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )

# ============================================================
# PAGE: USERS (ADMIN ONLY)
# ============================================================
elif selected == "👥 Users" and user_role == "admin":
    st.markdown("""
        <div class="main-header">
            <h1>👥 User Management</h1>
            <p>Manage accounts, roles, and permissions</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/auth/users")
    data = handle_response(resp) if resp else None

    if data:
        users = data["users"]
        st.metric("Total Users", len(users))

        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔧 Actions")

        opts = {f"{u['username']} ({u['role']})": u['id'] for u in users}
        sel = st.selectbox("Select user", list(opts.keys()), key="admin_sel")
        uid = opts[sel]

        selected_user = next((u for u in users if u["id"] == uid), None)
        current_role = selected_user["role"] if selected_user else "teacher"

        st.info(f"**Current role:** `{current_role}`")

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("🔄 Toggle Active", use_container_width=True):
                resp = api_put(f"/auth/users/{uid}/toggle")
                if resp and resp.status_code == 200:
                    st.success("Status updated")
                    time.sleep(0.5)
                    st.rerun()

        with c2:
            new_role = st.selectbox(
                "New Role",
                ["admin", "teacher", "student", "parent"],
                index=["admin", "teacher", "student", "parent"].index(current_role),
                key="admin_role"
            )
            if st.button("👤 Change Role", use_container_width=True):
                if new_role == current_role:
                    st.warning(f"Already '{new_role}'")
                else:
                    resp = api_put(f"/auth/users/{uid}/role?role={new_role}")
                    if resp and resp.status_code == 200:
                        st.success(resp.json().get("message", "Updated"))
                        time.sleep(0.5)
                        st.rerun()

        with c3:
            if st.button("↩️ Revert Last Change", use_container_width=True, type="secondary"):
                resp = api_put(f"/auth/users/{uid}/revert-role")
                if resp and resp.status_code == 200:
                    st.success(resp.json().get("message", "Reverted"))
                    time.sleep(0.5)
                    st.rerun()
                elif resp and resp.status_code == 400:
                    st.warning(resp.json().get("detail", "No previous change to revert"))

        st.markdown("")
        col_l, col_m, col_r = st.columns([2, 1, 2])
        with col_m:
            if st.button("🗑️ Delete User", use_container_width=True, type="secondary"):
                if uid == user["id"]:
                    st.error("❌ Cannot delete your own account")
                else:
                    resp = api_delete(f"/auth/users/{uid}")
                    if resp and resp.status_code == 200:
                        st.success("User deleted")
                        time.sleep(0.5)
                        st.rerun()

        # Role history
        st.markdown("---")
        st.markdown(f"### 📜 Role Change History — {selected_user['username']}")

        hist_resp = api_get(f"/auth/users/{uid}/role-history")
        hist_data = handle_response(hist_resp, show_error=False) if hist_resp else None

        if hist_data and hist_data.get("history"):
            hist_df = pd.DataFrame(hist_data["history"])
            display_cols = ["created_at", "old_role", "new_role", "changed_by_username"]
            available = [c for c in display_cols if c in hist_df.columns]
            if available:
                hist_df = hist_df[available]
                hist_df.columns = [c.replace("_", " ").title() for c in hist_df.columns]
            st.dataframe(hist_df, use_container_width=True)
            st.caption(f"Total role changes: {len(hist_data['history'])}")
        else:
            st.info("📭 No role changes recorded for this user yet")

# ============================================================
# PAGE: AUDIT LOG (ADMIN ONLY)
# ============================================================
elif selected == "📋 Audit Log" and user_role == "admin":
    st.markdown("""
        <div class="main-header">
            <h1>📋 Audit Log</h1>
            <p>Security and activity tracking</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Activity Log", "🔐 Login Attempts"])

    with tab1:
        resp = api_get("/audit/logs", params={"limit": 200})
        data = handle_response(resp) if resp else None
        if data and data.get("logs"):
            st.dataframe(pd.DataFrame(data["logs"]), use_container_width=True)
        else:
            st.info("No audit logs")

    with tab2:
        resp = api_get("/audit/login-attempts", params={"limit": 200})
        data = handle_response(resp) if resp else None
        if data and data.get("attempts"):
            st.dataframe(pd.DataFrame(data["attempts"]), use_container_width=True)
        else:
            st.info("No login attempts")

# ============================================================
# PAGE: PARENT - MY CHILDREN
# ============================================================
elif selected == "👨‍👩‍👧 My Children" and user_role == "parent":
    st.markdown("""
        <div class="main-header">
            <h1>👨‍👩‍👧 My Children</h1>
            <p>View your children's progress</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/parents/my-children")
    data = handle_response(resp) if resp else None

    if data and data.get("children"):
        for child in data["children"]:
            st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 1rem;">
                    <h3>🎓 {child['name']}</h3>
                    <p><b>Grade:</b> {child['grade']} | <b>Average:</b> {child['average']:.2f}%</p>
                    <p><b>Department:</b> {child.get('department', 'N/A')} | <b>Semester:</b> {child.get('semester', 'N/A')}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👶 No children linked yet. Contact admin.")

# ============================================================
# PAGE: STUDENT - MY RESULTS
# ============================================================
elif selected == "📊 My Results" and user_role == "student":
    st.markdown("""
        <div class="main-header">
            <h1>📊 My Results</h1>
            <p>Your academic performance</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/students", params={"limit": 10})
    data = handle_response(resp) if resp else None

    if data and data["count"] > 0:
        student = data["students"][0]
        st.markdown(f"### 🎓 {student['name']}")

        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric("📊", f"{student['average']:.2f}%", "Average")
        with c2:
            render_metric("🏆", student["grade"], "Grade")
        with c3:
            render_metric("📈", f"{student['total_marks']:.0f}", "Total Marks")

        if student.get("subjects") and student.get("marks"):
            df = pd.DataFrame({"Subject": student["subjects"], "Marks": student["marks"]})
            fig = px.bar(df, x="Subject", y="Marks", color="Marks", color_continuous_scale="RdYlGn")
            fig.update_layout(yaxis_range=[0, 105], showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 No results yet. Contact your teacher.")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #6b7280; padding: 2rem 0;">
        <p>🎓 Student Marks Analyzer Pro v6.0.0 | Secure Edition</p>
        <p style="font-size: 0.8rem;">Logged in as {user_name} ({user_role})</p>
    </div>
""", unsafe_allow_html=True)
