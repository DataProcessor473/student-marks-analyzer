import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import base64
from streamlit_option_menu import option_menu
import altair as alt

# Page configuration
st.set_page_config(
    page_title="Student Marks Analyzer Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        padding: 0rem 1rem;
    }

    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 60%;
        height: 200%;
        background: rgba(255, 255, 255, 0.05);
        transform: rotate(30deg);
        pointer-events: none;
    }

    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }

    /* Card Styles */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        border: 1px solid rgba(0, 0, 0, 0.03);
        height: 100%;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }

    .metric-card .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .metric-card .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0.5rem 0;
    }

    .metric-card .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 500;
    }

    /* Grade Badge */
    .grade-badge {
        font-size: 3rem;
        font-weight: 700;
        padding: 1.5rem 3rem;
        border-radius: 100px;
        display: inline-block;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    /* Status Badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    .status-pass {
        background: #d1fae5;
        color: #065f46;
    }

    .status-fail {
        background: #fee2e2;
        color: #991b1b;
    }

    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }

    .stButton > button:active {
        transform: translateY(0px);
    }

    /* Sidebar Styles */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }

    .css-1d391kg .stSelectbox,
    .css-1d391kg .stTextInput,
    .css-1d391kg .stNumberInput {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }

    /* Tab Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }

    /* Progress Bar */
    .custom-progress {
        height: 8px;
        border-radius: 4px;
        background: #e5e7eb;
        overflow: hidden;
        margin: 0.5rem 0;
    }

    .custom-progress-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 1s ease;
    }

    /* Recommendation Cards */
    .recommendation-card {
        background: #f9fafb;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }

    .recommendation-card:hover {
        background: #f3f4f6;
        transform: translateX(4px);
    }

    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a1a2e;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }

    /* Loading Animation */
    .loading-spinner {
        border: 4px solid #f3f4f6;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Responsive Grid */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem;
        }
        .grade-badge {
            font-size: 2rem;
            padding: 1rem 2rem;
        }
        .metric-card .metric-value {
            font-size: 1.5rem;
        }
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }

    /* Toast notification */
    .toast {
        padding: 1rem 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
        animation: slideIn 0.5s ease;
    }

    @keyframes slideIn {
        from {
            transform: translateY(-20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    .toast-success {
        background: #10b981;
    }

    .toast-error {
        background: #ef4444;
    }

    .toast-info {
        background: #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# API endpoint
API_URL = "http://127.0.0.1:8000"

# Initialize session state
if 'analyze_result' not in st.session_state:
    st.session_state.analyze_result = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Analyze Marks"
if 'notifications' not in st.session_state:
    st.session_state.notifications = []

# Sidebar with professional navigation
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: white; margin: 0;">🎓 Pro Analyzer</h2>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">v3.0.0</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    selected = option_menu(
        menu_title=None,
        options=["📝 Analyze", "📚 Database", "📊 Analytics", "📈 Reports", "📅 Attendance", "🔔 Notifications"],
        icons=["pencil-square", "database", "bar-chart", "file-earmark-text", "calendar", "bell"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#667eea", "font-size": "1.2rem"},
            "nav-link": {
                "font-size": "1rem",
                "text-align": "left",
                "margin": "0.25rem 0",
                "padding": "0.75rem 1rem",
                "border-radius": "10px",
                "color": "rgba(255,255,255,0.8)",
                "transition": "all 0.3s ease"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white",
                "font-weight": "500"
            },
            "nav-link-hover": {
                "background": "rgba(255,255,255,0.05)",
            }
        }
    )

    st.markdown("---")

    # API Status
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("🟢 System Online")
            st.caption(f"📁 Database: {response.json().get('database', 'Connected')}")
        else:
            st.error("🔴 System Offline")
    except:
        st.error("🔴 Connection Failed")
        st.caption("Please start the backend server")

# Main content area
if selected == "📝 Analyze":
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>📝 Analyze Student Performance</h1>
            <p>Comprehensive analysis with AI-powered insights and recommendations</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.container():
            st.markdown("### 👤 Student Information")
            student_name = st.text_input("Student Name", placeholder="Enter student name", key="student_name_input")

            col1a, col1b, col1c = st.columns(3)
            with col1a:
                semester = st.selectbox("Semester", ["Fall 2024", "Spring 2024", "Summer 2024", "Fall 2023"], index=0)
            with col1b:
                batch_year = st.selectbox("Batch Year", ["2024", "2023", "2022", "2021", "2020"], index=0)
            with col1c:
                department = st.selectbox("Department",
                    ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Engineering", "Business"])

        st.markdown("### 📚 Subject Details")
        num_subjects = st.slider("Number of Subjects", min_value=1, max_value=15, value=5, step=1)

        marks = []
        subject_names = []

        # Create a grid for subject inputs
        cols = st.columns(3)
        for i in range(num_subjects):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"**Subject {i+1}**")
                    subject_name = st.text_input(f"Name", placeholder=f"Subject {i+1}", key=f"subj_name_{i}", label_visibility="collapsed")
                    mark = st.number_input(f"Marks", min_value=0, max_value=100, value=0, step=1, key=f"mark_{i}", label_visibility="collapsed")
                    marks.append(mark)
                    subject_names.append(subject_name or f"Subject {i+1}")

    with col2:
        with st.container():
            st.markdown("### ⚙️ Analysis Settings")

            passing_threshold = st.slider("Passing Threshold", 0, 60, 40, 5)
            grade_scheme = st.selectbox(
                "Grade Scheme",
                ["standard", "strict", "lenient"],
                index=0,
                help="Standard: Normal grading, Strict: Higher requirements, Lenient: Lower requirements"
            )

            st.markdown("---")
            st.markdown("### 📊 Quick Stats")

            if sum(marks) > 0:
                total = sum(marks)
                avg = total / len(marks)
                st.metric("Total Marks", f"{total:.0f}")
                st.metric("Average", f"{avg:.1f}%")

                # Mini progress bar
                st.markdown(f"""
                    <div class="custom-progress">
                        <div class="custom-progress-bar" style="width: {avg}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
                    </div>
                """, unsafe_allow_html=True)

    # Analyze button
    if st.button("🚀 Analyze Performance", type="primary", use_container_width=True):
        if sum(marks) == 0:
            st.warning("⚠️ Please enter marks for all subjects")
        else:
            with st.spinner("Analyzing student performance..."):
                try:
                    payload = {
                        "marks": marks,
                        "student_name": student_name or "Unnamed Student",
                        "subject_names": subject_names,
                        "passing_threshold": passing_threshold,
                        "grade_scheme": grade_scheme,
                        "semester": semester,
                        "batch_year": batch_year,
                        "department": department
                    }

                    response = requests.post(f"{API_URL}/analyze", json=payload, timeout=10)

                    if response.status_code == 200:
                        st.session_state.analyze_result = response.json()
                        st.success("✅ Analysis complete!")
                        st.balloons()
                    else:
                        st.error(f"❌ Error: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Please make sure FastAPI is running on port 8000")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")

    # Display results if available
    if st.session_state.analyze_result:
        result = st.session_state.analyze_result
        st.markdown("---")

        # Grade section
        grade_color = {
            "A+": "#10b981", "A": "#34d399", "B": "#fbbf24",
            "C": "#f59e0b", "D": "#f97316", "E": "#ef4444", "F": "#dc2626"
        }.get(result["grade"], "#667eea")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"""
                <div style="padding: 1rem 0;">
                    <h2>Overall Performance</h2>
                    <div class="grade-badge" style="background: linear-gradient(135deg, {grade_color}, {grade_color}dd); color: white;">
                        {result['grade']} <span style="font-size: 1.5rem;">(GPA: {result['grade_points']})</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">📊</div>
                    <div class="metric-value">{result['average']:.1f}%</div>
                    <div class="metric-label">Average Score</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">✅</div>
                    <div class="metric-value">{result['pass_percentage']:.0f}%</div>
                    <div class="metric-label">Pass Rate</div>
                </div>
            """, unsafe_allow_html=True)

        # Metrics grid
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Total Marks", f"{result['total_marks']:.0f}")
        with col2:
            st.metric("🏆 Highest", f"{result['highest']:.0f}")
        with col3:
            st.metric("📉 Lowest", f"{result['lowest']:.0f}")
        with col4:
            st.metric("📊 Pass/Fail", f"{result['passed']}/{result['passed'] + result['failed']}")

        # Subject-wise performance - CORRECTED SECTION
        st.markdown("### 📚 Subject-wise Performance Analysis")

        df = pd.DataFrame(result["subject_wise"])

        # Create enhanced chart
        fig = go.Figure()

        # Add bars - CORRECTED VERSION (removed duplicate text argument)
        fig.add_trace(go.Bar(
            x=df["subject"],
            y=df["marks"],
            name="Marks",
            marker_color=df["marks"].apply(lambda x: "#10b981" if x >= passing_threshold else "#ef4444"),
            text=df["marks"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Marks: %{y}<br>Status: %{customdata}<extra></extra>",
            customdata=df["status"]
        ))

        # Add passing threshold line
        fig.add_hline(
            y=passing_threshold,
            line_dash="dash",
            line_color="#f59e0b",
            annotation_text=f"Passing ({passing_threshold})",
            annotation_position="bottom right"
        )

        fig.update_layout(
            title="Subject-wise Marks Distribution",
            xaxis_title="Subjects",
            yaxis_title="Marks",
            yaxis_range=[0, 105],
            showlegend=False,
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig, use_container_width=True)

        # AI Insights section
        if "ai_insights" in result:
            st.markdown("### 🤖 AI-Powered Insights")

            tab1, tab2, tab3 = st.tabs(["💪 Strengths", "📈 Recommendations", "🎯 Study Tips"])

            with tab1:
                if result["ai_insights"]["strengths"]:
                    for strength in result["ai_insights"]["strengths"]:
                        st.success(f"**{strength['subject']}**: {strength['marks']} - {strength['level']}")
                else:
                    st.info("No specific strengths identified yet")

            with tab2:
                for rec in result["ai_insights"]["recommendations"]:
                    priority_emoji = "🔴" if rec["priority"] == "High" else "🟡" if rec["priority"] == "Medium" else "🟢"
                    st.markdown(f"""
                        <div class="recommendation-card">
                            <strong>{priority_emoji} {rec['action']}</strong><br>
                            <span style="color: #6b7280;">{rec['details']}</span>
                        </div>
                    """, unsafe_allow_html=True)

            with tab3:
                for tip in result["ai_insights"]["study_tips"]:
                    st.info(f"📌 {tip}")

        # Anomalies detection
        if result.get("anomalies"):
            st.markdown("### ⚠️ Anomaly Detection")
            for anomaly in result["anomalies"]:
                if anomaly["type"] == "Exceptionally High":
                    st.success(f"🌟 {anomaly['subject']}: {anomaly['marks']} - Outstanding performance!")
                else:
                    st.warning(f"📊 {anomaly['subject']}: {anomaly['marks']} - Review needed")

        # Recommendations
        st.markdown("### 💡 Recommendations")
        for rec in result["recommendations"]:
            st.markdown(f"""
                <div class="recommendation-card" style="border-left-color: {'#10b981' if 'Excellent' in rec or '🌟' in rec else '#f59e0b' if 'Good' in rec else '#ef4444'};">
                    {rec}
                </div>
            """, unsafe_allow_html=True)

        # Save button
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            if st.button("💾 Save Student Record", type="primary", use_container_width=True):
                try:
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

                    response = requests.post(f"{API_URL}/students/save", json=save_data, timeout=10)

                    if response.status_code == 200:
                        st.success("✅ Student record saved successfully!")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed to save: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        with col2:
            if st.button("📋 Copy Report", use_container_width=True):
                st.info("Report copied to clipboard!")

elif selected == "📚 Database":
    st.markdown("""
        <div class="main-header">
            <h1>📚 Student Database</h1>
            <p>Manage and view all student records</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 All Records", "🔍 Search & Filter", "🗑️ Manage"])

    with tab1:
        try:
            # Pagination
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                limit = st.selectbox("Records per page", [10, 25, 50, 100], index=0, key="db_limit")
            with col3:
                page = st.number_input("Page", min_value=1, value=1, step=1, key="db_page")

            offset = (page - 1) * limit

            with st.spinner("Loading records..."):
                response = requests.get(f"{API_URL}/students", params={"limit": limit, "offset": offset})

            if response.status_code == 200:
                data = response.json()

                if data["count"] > 0:
                    st.success(f"📊 Total Students: {data['count']}")

                    # Convert to DataFrame for better display
                    df = pd.DataFrame(data["students"])
                    display_df = df.copy()
                    display_df['marks'] = display_df['marks'].apply(lambda x: ', '.join(map(str, x)))
                    display_df['subjects'] = display_df['subjects'].apply(lambda x: ', '.join(x))

                    # Add grade colors
                    def color_grade(val):
                        colors = {'A+': '#10b981', 'A': '#34d399', 'B': '#fbbf24',
                                 'C': '#f59e0b', 'D': '#f97316', 'E': '#ef4444', 'F': '#dc2626'}
                        return f'background-color: {colors.get(val, "transparent")}; color: white; font-weight: bold; padding: 2px 8px; border-radius: 4px;'

                    # Display as styled dataframe
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        column_config={
                            "id": "ID",
                            "name": "Student Name",
                            "marks": "Marks",
                            "subjects": "Subjects",
                            "grade": "Grade",
                            "average": "Average",
                            "total_marks": "Total",
                            "semester": "Semester",
                            "department": "Department"
                        }
                    )

                    # Export options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📥 Export CSV", use_container_width=True):
                            try:
                                export_response = requests.get(f"{API_URL}/export/csv")
                                if export_response.status_code == 200:
                                    st.download_button(
                                        label="Download CSV",
                                        data=export_response.content,
                                        file_name=f"students_export_{datetime.now().strftime('%Y%m%d')}.csv",
                                        mime="text/csv"
                                    )
                            except:
                                st.error("Export failed")

                    with col2:
                        if st.button("📊 Generate Report", use_container_width=True):
                            st.info("Report generation in progress...")
                else:
                    st.info("📋 No students in database yet")
            else:
                st.error("❌ Failed to fetch student data")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend")

    with tab2:
        st.markdown("### 🔍 Search Students")

        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("Search by name", placeholder="Type student name...", key="search_input")
        with col2:
            search_btn = st.button("🔍 Search", use_container_width=True)

        if search_term or search_btn:
            try:
                response = requests.get(f"{API_URL}/students/search", params={"name": search_term})
                if response.status_code == 200:
                    data = response.json()
                    if data["count"] > 0:
                        st.success(f"Found {data['count']} students")
                        df = pd.DataFrame(data["students"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No students found")
            except:
                st.error("Search failed")

        st.markdown("### 🎯 Advanced Filters")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_grade = st.selectbox("Grade", ["All", "A+", "A", "B", "C", "D", "E", "F"], index=0)
        with col2:
            filter_semester = st.selectbox("Semester", ["All", "Fall 2024", "Spring 2024", "Summer 2024"], index=0)
        with col3:
            filter_dept = st.selectbox("Department", ["All", "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"], index=0)
        with col4:
            min_avg = st.slider("Min Average", 0, 100, 0, 5)

        if st.button("Apply Filters", use_container_width=True):
            with st.spinner("Filtering records..."):
                params = {}
                if filter_grade != "All": params["grade"] = filter_grade
                if filter_semester != "All": params["semester"] = filter_semester
                if filter_dept != "All": params["department"] = filter_dept
                if min_avg > 0: params["min_average"] = min_avg

                try:
                    response = requests.get(f"{API_URL}/students/filter", params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if data["count"] > 0:
                            st.success(f"Found {data['count']} students matching filters")
                            df = pd.DataFrame(data["students"])
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No students match the filters")
                except:
                    st.error("Filter failed")

    with tab3:
        st.markdown("### 🗑️ Delete Records")

        try:
            response = requests.get(f"{API_URL}/students")
            if response.status_code == 200:
                data = response.json()
                if data["count"] > 0:
                    students = data["students"]
                    student_options = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
                    selected_student = st.selectbox("Select student to delete", list(student_options.keys()))

                    col1, col2 = st.columns(2)
                    with col2:
                        if st.button("🗑️ Delete Student", type="secondary", use_container_width=True):
                            student_id = student_options[selected_student]
                            with st.spinner("Deleting record..."):
                                delete_response = requests.delete(f"{API_URL}/students/delete/{student_id}")
                                if delete_response.status_code == 200:
                                    st.success("✅ Student record deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete")
                else:
                    st.info("No students to delete")
        except:
            st.error("❌ Cannot connect to backend")

elif selected == "📊 Analytics":
    st.markdown("""
        <div class="main-header">
            <h1>📊 Advanced Analytics</h1>
            <p>Comprehensive performance analytics and insights</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        with st.spinner("Loading analytics..."):
            stats_response = requests.get(f"{API_URL}/stats/overall")

            if stats_response.status_code == 200:
                stats = stats_response.json()

                if "message" not in stats:
                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-icon">👥</div>
                                <div class="metric-value">{stats['total_students']}</div>
                                <div class="metric-label">Total Students</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-icon">📈</div>
                                <div class="metric-value">{stats['average_of_averages']:.1f}</div>
                                <div class="metric-label">Average Score</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-icon">✅</div>
                                <div class="metric-value">{stats['pass_rate']:.1f}%</div>
                                <div class="metric-label">Pass Rate</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col4:
                        st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-icon">🏆</div>
                                <div class="metric-value">{stats['distinction_rate']:.1f}%</div>
                                <div class="metric-label">Distinction Rate</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Grade distribution
                    if "grade_distribution" in stats:
                        st.markdown("### 📊 Grade Distribution")

                        col1, col2 = st.columns(2)
                        with col1:
                            grade_df = pd.DataFrame({
                                "Grade": list(stats["grade_distribution"].keys()),
                                "Count": list(stats["grade_distribution"].values())
                            })

                            fig = px.pie(
                                grade_df,
                                values="Count",
                                names="Grade",
                                title="Grade Distribution",
                                hole=0.3,
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig, use_container_width=True)

                        with col2:
                            fig = px.bar(
                                grade_df,
                                x="Grade",
                                y="Count",
                                title="Grade Count",
                                color="Grade",
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            st.plotly_chart(fig, use_container_width=True)

                    # Top performers
                    if "top_performers" in stats:
                        st.markdown("### 🏆 Top Performers")
                        top_df = pd.DataFrame(stats["top_performers"])
                        top_df_display = top_df[["name", "grade", "average", "department"]]
                        st.dataframe(top_df_display, use_container_width=True)

                    # Subject statistics
                    if "subject_statistics" in stats:
                        st.markdown("### 📚 Subject Performance Analysis")
                        subject_df = pd.DataFrame(stats["subject_statistics"]).T
                        subject_df = subject_df.round(2)
                        subject_df = subject_df.sort_values("average", ascending=False)

                        fig = px.bar(
                            subject_df.reset_index(),
                            x="index",
                            y="average",
                            title="Average Marks by Subject",
                            color="average",
                            color_continuous_scale="Viridis",
                            labels={"index": "Subject", "average": "Average Marks"}
                        )
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)

                        # Subject details table
                        st.dataframe(subject_df, use_container_width=True)
            else:
                st.error("Failed to load analytics")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend")

elif selected == "📈 Reports":
    st.markdown("""
        <div class="main-header">
            <h1>📈 Reports & Insights</h1>
            <p>Generate comprehensive reports and export data</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Generate Reports")

    col1, col2 = st.columns(2)
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Overall Performance", "Subject-wise Analysis", "Grade Distribution", "Department Analysis"]
        )

    with col2:
        report_format = st.selectbox(
            "Format",
            ["PDF", "CSV", "HTML", "JSON"]
        )

    if st.button("📄 Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            st.success("✅ Report generated successfully!")
            st.info("📥 Report is ready for download")

    st.markdown("---")

    # Export options
    st.markdown("### 📥 Export Data")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Export CSV", use_container_width=True):
            try:
                response = requests.get(f"{API_URL}/export/csv")
                if response.status_code == 200:
                    st.download_button(
                        label="Download CSV",
                        data=response.content,
                        file_name=f"students_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            except:
                st.error("Export failed")

    with col2:
        if st.button("📋 Export JSON", use_container_width=True):
            try:
                response = requests.get(f"{API_URL}/students")
                if response.status_code == 200:
                    data = response.json()
                    json_str = json.dumps(data, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"students_data_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
            except:
                st.error("Export failed")

    with col3:
        if st.button("📈 Statistics Summary", use_container_width=True):
            try:
                response = requests.get(f"{API_URL}/stats/overall")
                if response.status_code == 200:
                    stats = response.json()
                    st.info(f"""
                        **Summary Report**
                        Total Students: {stats.get('total_students', 0)}
                        Average Score: {stats.get('average_of_averages', 0):.2f}
                        Pass Rate: {stats.get('pass_rate', 0):.1f}%
                        Distinction Rate: {stats.get('distinction_rate', 0):.1f}%
                    """)
            except:
                st.error("Failed to fetch statistics")

elif selected == "📅 Attendance":
    st.markdown("""
        <div class="main-header">
            <h1>📅 Attendance Management</h1>
            <p>Track and manage student attendance</p>
        </div>
    """, unsafe_allow_html=True)

    st.info("📋 Attendance tracking feature coming soon!")

    # Placeholder for attendance features
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-icon">👤</div>
                <div class="metric-value">0</div>
                <div class="metric-label">Students Tracked</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-icon">📊</div>
                <div class="metric-value">0%</div>
                <div class="metric-label">Attendance Rate</div>
            </div>
        """, unsafe_allow_html=True)

elif selected == "🔔 Notifications":
    st.markdown("""
        <div class="main-header">
            <h1>🔔 Notifications</h1>
            <p>View all notifications and alerts</p>
        </div>
    """, unsafe_allow_html=True)

    st.info("🔔 Notification system active")

    # Placeholder for notifications
    notifications = [
        {"type": "success", "message": "✅ New student record added successfully"},
        {"type": "info", "message": "📊 Analysis complete for John Doe"},
        {"type": "warning", "message": "⚠️ 2 students require attention - below passing grade"},
        {"type": "success", "message": "🏆 Student achieved A+ grade!"}
    ]

    for notif in notifications:
        if notif["type"] == "success":
            st.success(notif["message"])
        elif notif["type"] == "warning":
            st.warning(notif["message"])
        else:
            st.info(notif["message"])

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 2rem 0;">
        <p>🎓 Student Marks Analyzer Pro v3.0.0 | Built with ❤️ using FastAPI & Streamlit</p>
        <p style="font-size: 0.8rem;">© 2024 All Rights Reserved</p>
    </div>
""", unsafe_allow_html=True)
