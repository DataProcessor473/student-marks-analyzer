🎓 Student Marks Analyzer Pro
<div align="center">
https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white
https://img.shields.io/badge/FastAPI-0.104+-green.svg?style=for-the-badge&logo=fastapi&logoColor=white
https://img.shields.io/badge/Streamlit-1.28+-red.svg?style=for-the-badge&logo=streamlit&logoColor=white
https://img.shields.io/badge/SQLite-3.x-blue.svg?style=for-the-badge&logo=sqlite&logoColor=white
https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge
https://img.shields.io/badge/Version-3.0.0-brightgreen.svg?style=for-the-badge
https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge

</div>
<div align="center"> <h1>🎓 Student Marks Analyzer Pro</h1> <p><strong>Advanced AI-Powered Academic Performance Analysis Platform</strong></p> <p> <a href="#-quick-start">Quick Start</a> • <a href="#-features">Features</a> • <a href="#-technology-stack">Tech Stack</a> • <a href="#-installation">Installation</a> • <a href="#-usage">Usage</a> • <a href="#-contributing">Contributing</a> </p> <br> <p> <strong>🌟 Live Demo:</strong> <a href="https://student-marks-analyzer-faysmbfnqzde8wyr7tgdxy.streamlit.app">https://student-marks-analyzer.streamlit.app</a> • <strong>📚 API Docs:</strong> <a href="https://student-marks-analyzer-vju7.onrender.com/docs">https://student-marks-analyzer-vju7.onrender.com/docs</a> </p> </div>
📋 Table of Contents
🌟 Overview

✨ Features

🏗️ Architecture

🛠️ Technology Stack

📁 Project Structure

🚀 Quick Start

📦 Installation

💻 Usage

📊 Features in Detail

📸 Screenshots

🤝 Contributing

📄 License

👥 Authors

🙏 Acknowledgments

🌟 Overview
Student Marks Analyzer Pro is a comprehensive, AI-powered academic performance analysis platform designed for educational institutions, teachers, and administrators. It provides deep insights into student performance through advanced analytics, machine learning algorithms, and interactive visualizations.

🎯 Key Benefits
Benefit	Description
📊 Data-Driven Decisions	Make informed decisions based on comprehensive analytics
🤖 AI-Powered Insights	Get intelligent recommendations and performance predictions
⏱️ Time-Saving	Automate grade analysis and reporting
🎨 Visual Excellence	Interactive dashboards for better understanding
📈 Scalable Architecture	Handle thousands of student records efficiently
🎯 Target Audience
🏫 Educational Institutions: Schools, colleges, universities

👨‍🏫 Teachers & Professors: Grade management and performance tracking

📊 Administrators: Institutional performance analytics

👨‍🎓 Students: Self-assessment and performance tracking

🔬 Researchers: Academic performance research

✨ Features
🤖 AI-Powered Features
Feature	Description	Status
Smart Analysis	AI-driven performance evaluation with actionable insights	✅
Anomaly Detection	Automatically identify exceptional or concerning performance patterns	✅
Performance Predictions	Predict future performance based on historical trends	✅
Personalized Recommendations	Customized study tips and improvement strategies	✅
Strengths/Weaknesses Analysis	Identify student's strong and weak subjects	✅
📊 Analytics & Reporting
Feature	Description	Status
Comprehensive Dashboards	Real-time analytics with interactive visualizations	✅
Grade Distribution	Visual representation of grade distribution across cohorts	✅
Subject Analysis	Identify hardest and easiest subjects	✅
Department Analytics	Compare performance across departments	✅
Export Reports	Generate reports in CSV and JSON formats	✅
Statistical Analysis	Mean, median, standard deviation, quartiles	✅
📚 Database Management
Feature	Description	Status
CRUD Operations	Complete Create, Read, Update, Delete functionality	✅
Advanced Filtering	Filter students by grade, semester, department, and more	✅
Search Capabilities	Quick search by student name	✅
Pagination	Efficient handling of large datasets	✅
Data Export	Export data in multiple formats	✅
📅 Attendance Management
Feature	Description	Status
Attendance Tracking	Record and track student attendance	✅
Attendance Analytics	Visual attendance trends and statistics	✅
Automated Notifications	Alerts for absences and late arrivals	✅
🔔 Notification System
Feature	Description	Status
In-App Notifications	Real-time alerts and updates	✅
Achievement Recognition	Automatic acknowledgment of outstanding performance	✅
Warning System	Proactive alerts for at-risk students	✅
Read/Unread Tracking	Track notification status	✅
🎨 User Experience
Feature	Description	Status
Modern UI	Professional, responsive design with smooth animations	✅
Mobile Responsive	Full functionality on all devices	✅
Interactive Charts	Dynamic visualizations with Plotly	✅
🏗️ Architecture
System Architecture Diagram
text
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                            │
│                    (Streamlit Frontend)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Analyze  │  │ Database │  │Analytics │  │ Reports  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐                                  │
│  │Attendance│  │Notifications│                               │
│  └──────────┘  └──────────┘                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                           │
│                    (FastAPI Backend)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│  │
│  │  │ Analysis │  │ Database │  │  Stats   │  │  Export  ││  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘│  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ AI Engine│  │ Notify   │  │Attendance│             │  │
│  │  └──────────┘  └──────────┘  └──────────┘             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ SQLite
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                  │
│                     (SQLite Database)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Students │  │Attendance│  │Notifications│  │ Trends  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
Data Flow Diagram
text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  Streamlit  │────▶│   FastAPI   │────▶│   SQLite    │
│   Input     │     │  Frontend   │     │   Backend   │     │  Database   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │                    │
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Student    │     │  API        │     │  AI         │     │  Stored     │
│  Data &     │────▶│  Request    │────▶│  Analysis   │────▶│  Results    │
│  Marks      │     │  (HTTP)     │     │  Engine     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Visual     │◀────│  JSON       │◀────│  AI         │◀────│  Retrieved  │
│  Results    │     │  Response   │     │  Insights   │     │  Data       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
Database Schema
text
┌─────────────────────────────────────────────────────────────────┐
│                         students                               │
├─────────────────────────────────────────────────────────────────┤
│ id INTEGER PRIMARY KEY                                        │
│ name TEXT NOT NULL                                            │
│ marks TEXT NOT NULL (JSON)                                    │
│ subjects TEXT NOT NULL (JSON)                                 │
│ grade TEXT NOT NULL                                           │
│ average REAL NOT NULL                                         │
│ total_marks REAL NOT NULL                                     │
│ timestamp TEXT NOT NULL                                       │
│ created_at TIMESTAMP                                          │
│ semester TEXT                                                 │
│ batch_year TEXT                                               │
│ department TEXT                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1
                              │
                              │ *
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       attendance                               │
├─────────────────────────────────────────────────────────────────┤
│ id INTEGER PRIMARY KEY                                        │
│ student_id INTEGER (FK)                                       │
│ date TEXT NOT NULL                                            │
│ status TEXT NOT NULL (Present/Absent/Late/Excused)            │
│ subject TEXT                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1
                              │
                              │ *
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     notifications                              │
├─────────────────────────────────────────────────────────────────┤
│ id INTEGER PRIMARY KEY                                        │
│ student_id INTEGER (FK)                                       │
│ message TEXT NOT NULL                                         │
│ type TEXT (Warning/Info/Success/Achievement)                  │
│ is_read INTEGER DEFAULT 0                                     │
│ created_at TIMESTAMP                                          │
└─────────────────────────────────────────────────────────────────┘
🛠️ Technology Stack
Backend
Technology	Version	Purpose
FastAPI	0.104+	REST API Framework
Python	3.8+	Programming Language
SQLite	3.x	Database
NumPy	1.24+	Numerical Computing
Pandas	2.1+	Data Processing
Pydantic	2.5+	Data Validation
Uvicorn	0.24+	ASGI Server
Frontend
Technology	Version	Purpose
Streamlit	1.28+	Web Framework
Plotly	5.18+	Interactive Visualizations
Altair	5.2+	Statistical Visualizations
Pandas	2.1+	Data Manipulation
Streamlit-Option-Menu	0.3+	Enhanced Navigation
Additional Libraries
Library	Purpose
Requests	HTTP Client
Python-Multipart	Form Data Handling
OpenPyXL	Excel Export
XlsxWriter	Excel File Creation
ReportLab	PDF Generation
📁 Project Structure
text
student-marks-analyzer/
│
├── 📂 backend/                          # FastAPI Backend
│   ├── 📄 main.py                       # Main application (428 lines)
│   ├── 📄 migrate_db.py                 # Database migration utility
│   └── 📄 student_marks.db              # SQLite database (auto-generated)
│
├── 📂 frontend/                         # Streamlit Frontend
│   └── 📄 app.py                        # Main application (800+ lines)
│
├── 📄 requirements.txt                  # Python dependencies
├── 📄 .gitignore                        # Git ignore rules
├── 📄 LICENSE                           # MIT License
└── 📄 README.md                         # Project documentation
Detailed File Descriptions
File	Description	Lines
backend/main.py	FastAPI application with 18 API endpoints, AI-powered analysis, database operations	~428
backend/migrate_db.py	Database schema migration and update utility	~30
frontend/app.py	Streamlit UI with 6 tabs, interactive charts, AI insights display	~800+
requirements.txt	All Python package dependencies	~90
.gitignore	Excludes cache, database, and environment files	~100
LICENSE	MIT License	~20
README.md	Project documentation	~400
🚀 Quick Start
Prerequisites
Python 3.8+ - Download

pip - Python package manager (comes with Python)

Git - Version control (optional)

One-Minute Setup
bash
# Clone the repository
git clone https://github.com/DataProcessor473/student-marks-analyzer.git
cd student-marks-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
streamlit run frontend/app.py
Access the Application
🌐 Frontend: http://localhost:8501

📚 API Documentation: http://localhost:8000/docs

🏥 Health Check: http://localhost:8000/health

📦 Installation
Option 1: Standard Installation (Recommended)
bash
# 1. Clone the repository
git clone https://github.com/DataProcessor473/student-marks-analyzer.git
cd student-marks-analyzer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
# Backend
cd backend
uvicorn main:app --reload --port 8000

# Frontend (in new terminal)
streamlit run frontend/app.py
Option 2: One-Click Setup (Linux/Mac)
bash
chmod +x setup.sh
./setup.sh
Option 3: One-Click Setup (Windows)
cmd
setup.bat
Option 4: Docker Installation
bash
# Build the Docker image
docker build -t student-analyzer .

# Run the container
docker run -p 8000:8000 -p 8501:8501 student-analyzer
💻 Usage
📝 Analyzing Student Performance
Navigate to the Analyze tab in the sidebar

Enter student information:

Student Name

Semester (e.g., Fall 2024)

Batch Year (e.g., 2024)

Department

Add subject details:

Number of subjects (1-15)

Subject names

Marks for each subject (0-100)

Configure analysis settings:

Passing threshold (0-60)

Grade scheme (Standard/Strict/Lenient)

Click Analyze Performance

View comprehensive results:

Overall grade and GPA

Subject-wise performance

AI-powered insights

Recommendations

Anomaly detection

Optionally, save the record to database

📚 Managing Student Database
Navigate to the Database tab

View all student records with pagination

Search for specific students by name

Apply filters:

Grade (A+, A, B, C, D, E, F)

Semester

Department

Minimum Average

Export data to CSV or JSON

Delete records when needed

📊 Viewing Analytics
Navigate to the Analytics tab

View key metrics:

Total Students

Average Score

Pass Rate

Distinction Rate

Explore grade distribution charts

Analyze subject performance

Review top performers

Track department-wise statistics

📅 Tracking Attendance
Navigate to the Attendance tab

Select a student from the dropdown

Record attendance:

Date

Status (Present/Absent/Late/Excused)

Subject (optional)

Click Record Attendance

View attendance history and trends

Monitor attendance statistics

📊 Features in Detail
🤖 AI-Powered Analysis
The system uses advanced algorithms to provide intelligent insights:

python
# Example of AI Insights Response
{
    "strengths": [
        {"subject": "Mathematics", "marks": 95, "level": "Excellent"},
        {"subject": "Physics", "marks": 88, "level": "Excellent"}
    ],
    "weaknesses": [
        {"subject": "Chemistry", "marks": 45, "level": "Needs Improvement"}
    ],
    "recommendations": [
        {
            "priority": "High",
            "action": "Focus on Chemistry",
            "details": "Additional tutoring recommended"
        }
    ],
    "predictions": [
        "📈 Showing positive performance trend"
    ],
    "study_tips": [
        "Join study groups for collaborative learning"
    ],
    "improvement_potential": 35.5
}
📊 Statistical Analysis
Metric	Description	Formula
Average	Mean score across all subjects	Σ(x) / n
Median	Middle value of marks	Sorted data[n/2]
Standard Deviation	Measure of performance consistency	√(Σ(x-μ)²/n)
Variance	Spread of marks	Σ(x-μ)²/n
Quartiles	Q1, Q2, Q3 values	25th, 50th, 75th percentile
Range	Difference between highest and lowest	max - min
Pass Percentage	Percentage of subjects passed	(passed/total) × 100
Distinction Rate	Percentage of A/A+ students	(distinction/total) × 100
🎯 Grade Schemes
Grade	Standard	Strict	Lenient
A+	90-100	93-100	85-100
A	80-89.99	85-92.99	70-84.99
B	70-79.99	75-84.99	60-69.99
C	60-69.99	65-74.99	50-59.99
D	50-59.99	55-64.99	40-49.99
E	40-49.99	45-54.99	30-39.99
F	0-39.99	0-44.99	0-29.99
📸 Screenshots
<div align="center">
📝 Analysis Dashboard
<img src="https://via.placeholder.com/800x400/667eea/ffffff?text=Analysis+Dashboard" alt="Analysis Dashboard" width="80%">
📊 Analytics View
<img src="https://via.placeholder.com/800x400/764ba2/ffffff?text=Analytics+View" alt="Analytics View" width="80%">
📚 Database Management
<img src="https://via.placeholder.com/800x400/667eea/ffffff?text=Database+Management" alt="Database Management" width="80%"></div>
🤝 Contributing
We welcome contributions! Here's how you can help:

🐛 Reporting Bugs
Check if the bug already exists in Issues

Create a new issue with:

Clear title and description

Steps to reproduce

Expected vs actual behavior

Screenshots if applicable

Environment details (OS, Python version)

💡 Suggesting Features
Check if the feature already exists or is planned

Create a feature request with:

Clear description of the feature

Use cases and benefits

Mockups or examples (optional)

🔧 Pull Requests
Fork the repository

Create a feature branch:

bash
git checkout -b feature/amazing-feature
Make your changes

Write/update tests

Update documentation

Commit with clear message:

bash
git commit -m "feat: Add amazing feature"
Push to your fork:

bash
git push origin feature/amazing-feature
Open a Pull Request

📝 Commit Guidelines
Prefix	Usage
feat:	New feature
fix:	Bug fix
docs:	Documentation update
style:	Code style update (formatting, linting)
refactor:	Code refactoring
perf:	Performance improvement
test:	Add/update tests
chore:	Maintenance tasks
📋 Code Style
Follow PEP 8 guidelines

Use meaningful variable names

Write docstrings for functions

Add type hints where possible

Keep functions focused and small

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

text
MIT License

Copyright (c) 2024 DataProcessor473

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
👥 Authors
Project Lead
<div align="center"> <table> <tr> <td align="center"> <a href="https://github.com/DataProcessor473"> <img src="https://via.placeholder.com/100/667eea/ffffff?text=DP" width="100px;" alt="DataProcessor473"/> <br /> <sub><b>DataProcessor473</b></sub> </a> <br /> <sub>Project Lead & Developer</sub> </td> </tr> </table> </div>
Contributors
<a href="https://github.com/DataProcessor473/student-marks-analyzer/graphs/contributors"> <img src="https://contrib.rocks/image?repo=DataProcessor473/student-marks-analyzer" /> </a>
🙏 Acknowledgments
FastAPI Team - For the amazing framework

Streamlit Team - For the incredible frontend library

Open Source Community - For all the tools and libraries

Educational Institutions - For inspiring this project

All Contributors - For making this project better

📊 Project Stats
https://img.shields.io/github/stars/DataProcessor473/student-marks-analyzer?style=social
https://img.shields.io/github/forks/DataProcessor473/student-marks-analyzer?style=social
https://img.shields.io/github/watchers/DataProcessor473/student-marks-analyzer?style=social
https://img.shields.io/github/repo-size/DataProcessor473/student-marks-analyzer
https://img.shields.io/github/languages/code-size/DataProcessor473/student-marks-analyzer
https://img.shields.io/github/last-commit/DataProcessor473/student-marks-analyzer

🔮 Roadmap
Version 3.0.0 (Current) ✅
☑ AI-powered analysis
☑ Anomaly detection
☑ Performance predictions
☑ Attendance tracking
☑ Notification system
☑ Professional UI
Version 4.0.0 (Planned)
□ User Authentication System
□ Multiple User Roles (Admin, Teacher, Student)
□ Class/Course Management
□ Advanced Machine Learning Models
□ Real-time Collaboration
□ Mobile App Integration
□ Cloud Deployment Support
□ API Rate Limiting
□ WebSocket Support for Live Updates
Version 4.1.0 (Coming Soon)
□ PDF Report Generation
□ Email Notifications
□ Data Import from Excel/CSV
□ Custom Grade Schemes
□ Student Performance Comparison
□ Bulk Operations
□ Data Visualization Enhancements
📞 Support
📚 Documentation
API Documentation

Streamlit Documentation

FastAPI Documentation

💬 Community
GitHub Issues

Discord Community

Email Support

⭐ Star History
https://api.star-history.com/svg?repos=DataProcessor473/student-marks-analyzer&type=Date

<div align="center"> <p>Made with ❤️ by the Student Marks Analyzer Team</p> <p> <a href="#top">⬆️ Back to Top</a> • <a href="https://github.com/DataProcessor473/student-marks-analyzer/issues">Report Bug</a> • <a href="https://github.com/DataProcessor473/student-marks-analyzer/issues">Request Feature</a> </p> <p> <strong>⭐ Star us on GitHub if you find this project useful!</strong> </p> <br>
<sub>Built with 🐍 Python, ⚡ FastAPI, and 📊 Streamlit</sub>

</div> 
