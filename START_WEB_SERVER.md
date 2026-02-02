# 🌐 Web Server Startup Guide

## Quick Start

### Option 1: Run Flask App Directly
```bash
py app.py
```

### Option 2: Use Flask Command
```bash
flask --app app run
```

## Access the Web Interface

Once the server starts, open your browser and go to:

**http://localhost:5000**

or

**http://127.0.0.1:5000**

## Features

The web interface provides:

1. **📝 Job Description Input**
   - Paste or type job descriptions
   - Real-time validation

2. **🔍 Analysis & Processing**
   - Automatic job analysis
   - CV customization
   - Cover letter generation
   - Match score calculation

3. **📊 Results Display**
   - Match score visualization
   - Detailed breakdown
   - Download links for CV and Cover Letter

4. **📄 Document Downloads**
   - One-click download for CV
   - One-click download for Cover Letter
   - Files saved in `output/` directory

## Server Status

The server will display:
- ✅ Component initialization status
- 🚀 Server startup confirmation
- 📱 Localhost URL
- 🛑 Stop instructions (Ctrl+C)

## Troubleshooting

### Port Already in Use
If port 5000 is busy, you can change it in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change port number
```

### API Key Not Found
Make sure your `.env` file contains:
```
DEEPSEEK_API_KEY=your_key_here
```

### Profile Not Found
Ensure `data/master_profile.json` exists and is valid JSON.

## Stopping the Server

Press **Ctrl+C** in the terminal where the server is running.

---

**Enjoy your web-based job application agent!** 🚀
