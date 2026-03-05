# RingRing - TextNow/Caddy Clone

A modern, feature-rich communication platform with voice calling, video calling, SMS/MMS messaging, and more.

## 🎯 Features

- 📞 **Voice & Video Calling** - High-quality Sinch-powered calls
- 💬 **SMS/MMS Messaging** - Send text messages and media
- 🎬 **GIF Support** - Powered by Klipy API
- 📱 **Phone Number Management** - Search, claim, and manage numbers
- 👥 **Contacts** - Manage your contacts
- 📧 **Voicemail** - Receive and manage voicemails
- 🎨 **Modern UI** - Dark neon "hot, spicy, & classy" 2026 design

## 🛠️ Tech Stack

### Frontend
- React 18
- TailwindCSS
- Capacitor (for Android)
- Sinch Voice/Video SDK

### Backend
- FastAPI (Python)
- MongoDB
- Sinch API (SMS, Voice, Numbers)
- Klipy API (GIFs)

## 📁 Project Structure

```
/app/
├── backend/
│   ├── routes/       # API route modules
│   ├── models/       # Pydantic models
│   ├── utils/        # Utility functions
│   └── server.py     # Main FastAPI app
├── frontend/
│   ├── src/
│   │   ├── pages/    # React pages
│   │   ├── context/  # React context
│   │   └── components/
│   └── android/      # Capacitor Android project
└── test_reports/     # Test results
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Sinch Account (for SMS/Voice/Numbers)
- Klipy API Key (for GIFs)

### Environment Variables

Create `.env` files in both `backend/` and `frontend/` directories:

**Backend `.env`:**
```
MONGO_URL=mongodb://localhost:27017
SINCH_PROJECT_ID=your_project_id
SINCH_SERVICE_PLAN_ID=your_service_plan_id
SINCH_SMS_API_TOKEN=your_sms_token
SINCH_APP_KEY=your_app_key
SINCH_APP_SECRET=your_app_secret
KLIPY_API_KEY=your_klipy_key
JWT_SECRET=your_jwt_secret
```

**Frontend `.env`:**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Installation

1. **Backend:**
```bash
cd backend
pip install -r requirements.txt
python server.py
```

2. **Frontend:**
```bash
cd frontend
yarn install
yarn start
```

## ✅ Testing

The project includes comprehensive test coverage:
- 27/27 backend API tests passing
- Frontend component tests
- End-to-end Playwright tests

Run tests:
```bash
cd backend
pytest tests/
```

## 📱 Android Build

The project includes a Capacitor Android setup:
```bash
cd frontend
yarn build
npx cap sync android
```

See `frontend/android/BUILD_GUIDE.md` for detailed instructions.

## 🎨 Design

The app features a modern "hot, spicy, & classy" 2026 dark neon theme with:
- Glassmorphic UI elements
- Vibrant magenta/pink gradients
- Smooth animations
- Responsive design (desktop & mobile)

## 📄 License

MIT License

## 👨‍💻 Author

Josiah Scalia

---

Built with ❤️ using React, FastAPI, and Sinch
