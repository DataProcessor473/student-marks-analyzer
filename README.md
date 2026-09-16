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
<div align="center"> <h1>🎓 Student Marks Analyzer Pro</h1> <p><strong>Advanced AI-Powered Academic Performance Analysis Platform</strong></p> <p> <a href="#-quick-start">Quick Start</a> • <a href="#-features">Features</a> • <a href="#-technology-stack">Tech Stack</a> • <a href="#-installation">Installation</a> • <a href="#-usage">Usage</a> </p> <br> <p> <strong>🌟 Live Demo:</strong> <a href="https://student-marks-analyzer-faysmbfnqzde8wyr7tgdxy.streamlit.app">https://student-marks-analyzer.streamlit.app</a> • <strong>📚 API Docs:</strong> <a href="https://student-marks-analyzer-vju7.onrender.com/docs">https://student-marks-analyzer-vju7.onrender.com/docs</a> </p> </div>
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

🤝 Contributing

📄 License

👥 Authors

🌟 Overview
Student Marks Analyzer Pro is a comprehensive, AI-powered academic performance analysis platform designed for educational institutions, teachers, and administrators.

🎯 Key Benefits
Benefit	Description
📊 Data-Driven Decisions	Make informed decisions based on comprehensive analytics
🤖 AI-Powered Insights	Get intelligent recommendations and performance predictions
⏱️ Time-Saving	Automate grade analysis and reporting
🎨 Visual Excellence	Interactive dashboards for better understanding
🎯 Target Audience
🏫 Educational Institutions: Schools, colleges, universities

👨‍🏫 Teachers & Professors: Grade management and performance tracking

📊 Administrators: Institutional performance analytics

👨‍🎓 Students: Self-assessment and performance tracking

✨ Features
🤖 AI-Powered Features
Smart Analysis: AI-driven performance evaluation with actionable insights

Anomaly Detection: Automatically identify exceptional or concerning performance patterns

Performance Predictions: Predict future performance based on historical trends

Personalized Recommendations: Customized study tips and improvement strategies

Strengths/Weaknesses Analysis: Identify student's strong and weak subjects

📊 Analytics & Reporting
Comprehensive Dashboards: Real-time analytics with interactive visualizations

Grade Distribution: Visual representation of grade distribution across cohorts

Subject Analysis: Identify hardest and easiest subjects

Department Analytics: Compare performance across departments

Export Reports: Generate reports in CSV and JSON formats

Statistical Analysis: Mean, median, standard deviation, quartiles

📚 Database Management
CRUD Operations: Complete Create, Read, Update, Delete functionality

Advanced Filtering: Filter students by grade, semester, department, and more

Search Capabilities: Quick search by student name

Pagination: Efficient handling of large datasets

Data Export: Export data in multiple formats

📅 Attendance Management
Attendance Tracking: Record and track student attendance

Attendance Analytics: Visual attendance trends and statistics

Automated Notifications: Alerts for absences and late arrivals

🔔 Notification System
In-App Notifications: Real-time alerts and updates

Achievement Recognition: Automatic acknowledgment of outstanding performance

Warning System: Proactive alerts for at-risk students

🏗️ Architecture
System Architecture


















Data Flow
Database Schema


























































🛠️ Technology Stack
Backend
Technology	Version	Purpose
FastAPI	0.104+	REST API Framework
Python	3.8+	Programming Language
SQLite	3.x	Database
NumPy	1.24+	Numerical Computing
Pandas	2.1+	Data Processing
Pydantic	2.5+	Data Validation
Frontend
Technology	Version	Purpose
Streamlit	1.28+	Web Framework
Plotly	5.18+	Interactive Visualizations
Pandas	2.1+	Data Manipulation
Streamlit-Option-Menu	0.3+	Enhanced Navigation
Additional Libraries
Library	Purpose
Requests	HTTP Client
Python-Multipart	Form Data Handling
OpenPyXL	Excel Export
XlsxWriter	Excel File Creation
📁 Project Structure
text
student-marks-analyzer/
│
├── 📂 backend/                          # FastAPI Backend
│   ├── 📄 main.py                       # Main application (428 lines)
│   └── 📄 migrate_db.py                 # Database migration utility
│
├── 📂 frontend/                         # Streamlit Frontend
│   └── 📄 app.py                        # Main application (800+ lines)
│
├── 📄 requirements.txt                  # Python dependencies
├── 📄 .gitignore                        # Git ignore rules
├── 📄 LICENSE                           # MIT License
└── 📄 README.md                         # Project documentation
API Endpoints
Method	Endpoint	Description
GET	/	API home with version and features
POST	/analyze	Analyze marks with AI insights
POST	/analyze/batch	Analyze multiple students
GET	/students	Get all students with pagination
GET	/students/{id}	Get student by ID
POST	/students/save	Save student record
PUT	/students/update/{id}	Update student record
DELETE	/students/delete/{id}	Delete student record
GET	/students/search	Search students by name
GET	/students/filter	Filter students by criteria
GET	/stats/overall	Overall statistics
GET	/stats/grade-distribution	Grade distribution
GET	/stats/subject-analysis	Subject-wise analysis
POST	/attendance	Record attendance
GET	/attendance/{student_id}	Get attendance records
GET	/notifications	Get notifications
PUT	/notifications/mark-read/{id}	Mark notification as read
GET	/export/csv	Export data to CSV
GET	/export/json	Export data to JSON
GET	/health	Health check endpoint
🚀 Quick Start
Prerequisites
Python 3.8+ - Download

pip - Python package manager

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
Option 1: Standard Installation
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
Option 2: Docker Installation
bash
# Build the Docker image
docker build -t student-analyzer .

# Run the container
docker run -p 8000:8000 -p 8501:8501 student-analyzer
💻 Usage
📝 Analyzing Student Performance
Navigate to the Analyze tab

Enter student information (name, semester, department)

Add subject names and marks

Configure analysis settings (passing threshold, grade scheme)

Click Analyze Performance

View comprehensive results:

Overall grade and GPA

Subject-wise performance

AI-powered insights

Recommendations

Anomaly detection

📚 Managing Student Database
Navigate to the Database tab

View all student records with pagination

Search for specific students

Apply filters (grade, semester, department)

Delete records when needed

Export data to CSV or JSON

📊 Viewing Analytics
Navigate to the Analytics tab

View key metrics and statistics

Explore grade distribution charts

Analyze subject performance

Review top performers

📊 Features in Detail
🤖 AI-Powered Analysis
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
    ]
}
🎯 Grade Schemes
Grade	Standard	Strict	Lenient
A+	90-100	93-100	85-100
A	80-89.99	85-92.99	70-84.99
B	70-79.99	75-84.99	60-69.99
C	60-69.99	65-74.99	50-59.99
D	50-59.99	55-64.99	40-49.99
E	40-49.99	45-54.99	30-39.99
F	0-39.99	0-44.99	0-29.99
🤝 Contributing
We welcome contributions! Here's how you can help:

🐛 Reporting Bugs
Check if the bug already exists in Issues

Create a new issue with clear title, description, and steps to reproduce

💡 Suggesting Features
Check if the feature already exists or is planned

Create a feature request with clear description and use cases

🔧 Pull Requests
Fork the repository

Create a feature branch: git checkout -b feature/amazing-feature

Make your changes

Commit with clear message: git commit -m "feat: Add amazing feature"

Push to your fork: git push origin feature/amazing-feature

Open a Pull Request

📝 Commit Guidelines
Prefix	Usage
feat:	New feature
fix:	Bug fix
docs:	Documentation update
style:	Code style update
refactor:	Code refactoring
perf:	Performance improvement
test:	Add/update tests
chore:	Maintenance tasks
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
🙏 Acknowledgments
FastAPI Team - For the amazing framework

Streamlit Team - For the incredible frontend library

Open Source Community - For all the tools and libraries

Educational Institutions - For inspiring this project

<div align="center"> <p>Made with ❤️ by the Student Marks Analyzer Team</p> <p> <a href="#top">⬆️ Back to Top</a> • <a href="https://github.com/DataProcessor473/student-marks-analyzer/issues">Report Bug</a> • <a href="https://github.com/DataProcessor473/student-marks-analyzer/issues">Request Feature</a> </p> <p> <strong>⭐ Star us on GitHub if you find this project useful!</strong> </p> <br>
<sub>Built with 🐍 Python, ⚡ FastAPI, and 📊 Streamlit</sub>

</div>
