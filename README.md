# PathForge

PathForge is a Django-based platform for students, built around a set of AI-powered modules that help with career planning, exam/interview prep, and startup idea validation — all powered by Google's Gemini API.

## Features

- **CampusPath AI** — Generates a personalised, week-by-week career roadmap based on your target role, current skills, experience level, and (optionally) your GitHub activity. Tracks progress, skill gaps, and AI-generated insights as you go.
- **CrackAI** — AI module for exam/interview preparation *(in progress)*.
- **VentureIQ** — AI module for startup/business idea assistance *(in progress)*.
- **MindMateAI** — AI module for student mental wellness support *(in progress)*.
- **Accounts** — User registration, login, and profile management.

## Tech Stack

- **Backend:** Python, Django
- **Database:** SQLite (development)
- **AI:** Google Gemini API (`google-generativeai`)
- **Frontend:** HTML, CSS, JavaScript (Django templates)

## Getting Started

### 1. Clone the repository
```bash
git clone <repo-url>
cd StudentVerse/pathforge
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate     # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the `pathforge/` project root.
Check `.env.example` for more.

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Project Structure

```
pathforge/
├── accounts/       # User auth & profiles
├── home/           # Landing page
├── dashboard/      # User dashboard
├── campuspathAI/   # Career roadmap generator (Gemini-powered)
├── crackAI/        # Exam/interview prep module
├── ventureIQ/      # Startup idea module
├── mindmateAI/     # Mental wellness module
├── templates/      # HTML templates
├── static/         # CSS, JS, images
└── media/          # User-uploaded files
```

## Status

🚧 Work in progress — CampusPath AI is functional end-to-end. 
CrackAI, VentureIQ, and MindMateAI are still under development.

## License

This project is for educational purposes.
