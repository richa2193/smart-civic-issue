# Smart Civic Issue Reporting & Resolution System

A professional, production-quality web application built with Django, Bootstrap 5, and Vanilla JavaScript that enables citizens to report civic issues and allows government departments to manage and resolve them efficiently.

## Features

- **Role-Based Access Control:** Distinct dashboards for Citizens, Department Officers, and Admins.
- **Email OTP Verification:** Secure registration and password reset flows using one-time passwords sent via email.
- **Google Maps Integration:** Pinpoint issue locations dynamically on a map with auto-address resolution.
- **Auto-Assignment Logic:** Complaints are automatically routed to the correct department based on the selected category.
- **Real-Time Analytics:** Interactive charts built with Chart.js to monitor department performance and global platform statistics.
- **Premium UI/UX:** Responsive, aesthetic interface built purely with HTML5, CSS3, and Bootstrap 5 without any frontend frameworks. Includes image previews, skeleton loaders, and modern animations.

## Folder Structure

```
Project/
├── backend/                  # Django backend
│   ├── manage.py             
│   ├── config/               # Project settings & root URLs
│   ├── users/                # Custom User Model & Auth Logic
│   ├── complaints/           # Complaint creation & auto-assign logic
│   ├── departments/          # Department Officer dashboards
│   ├── dashboard/            # Admin dashboards & analytics
│   ├── media/                # Uploaded issue evidence
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Environment variables (Credentials)
│   └── db.sqlite3            # SQLite database
│
├── frontend/                 # Static & Templates
│   ├── css/
│   │   └── style.css         # Premium custom styling
│   ├── js/
│   │   └── app.js            # Image previews, loaders, toasts
│   └── *.html                # Django Templates (base, home, login, etc.)
└── README.md
```

## Requirements

Ensure you have the following installed:
- Python 3.10+
- pip (Python package manager)

## Installation & Setup

1. **Clone the repository or navigate to the project directory:**
   ```bash
   cd Project/backend
   ```

2. **Set up a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Update the `.env` file in the `backend/` directory with your real credentials:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key
   
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   
   GOOGLE_MAPS_API_KEY=YOUR_ACTUAL_GOOGLE_MAPS_API_KEY
   ```
   > **Note:** For Gmail, you must generate an "App Password" to bypass 2FA.

5. **Database Migration:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser (Optional Admin):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Server:**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000` in your browser.

## Screenshots Section
*(Add screenshots of the Home Page, Citizen Dashboard, Report Form with Map, and Admin Analytics here)*

## Future Scope

- **Push Notifications:** Integrate Firebase or WebSockets for real-time alerts.
- **Mobile Application:** Build a dedicated mobile client interacting with Django REST APIs.
- **AI Triage:** Automatically categorize complaints using image recognition before assigning to a department.
- **Upvote System:** Allow citizens to upvote existing issues to prioritize departmental action (Model already designed for it).

## License

This project is licensed under the MIT License.
