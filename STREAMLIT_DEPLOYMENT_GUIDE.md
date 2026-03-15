# Streamlit App - Deployment Guide

## For Non-Technical Users to Download Excel Reports

This Streamlit web app makes it **super easy** for non-technical users to:
- Run procurement analysis
- Select any organization ID
- Download Excel reports with a single click
- No Python, no Base64 decoding needed

---

## 🚀 How to Deploy

### **Option 1: Deploy on Streamlit Cloud (EASIEST - Recommended)**

**Time needed:** 5 minutes
**Cost:** FREE

#### Steps:

1. **Push code to GitHub** (already done)
   - Your code is on: `https://github.com/Kritnandan22/PROCUREMENT_AGENT_AI`

2. **Go to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Click "Sign up" or "Sign in with GitHub"

3. **Create new app**
   - Click "Create app"
   - Select Repository: `PROCUREMENT_AGENT_AI`
   - Select Branch: `main`
   - Set Main file path: `streamlit_app.py`

4. **Set environment variable**
   - Click "Advanced settings"
   - Under "Secrets", add:
     ```
     MCP_SERVER_URL = "https://procurement-agent-ai.onrender.com"
     ```
   - Click "Deploy"

5. **Share the link**
   - Streamlit gives you a URL like: `https://your-app-name.streamlit.app`
   - Share this with all users!

---

### **Option 2: Deploy on Render (Alternative)**

**Time needed:** 10 minutes
**Cost:** FREE tier available

#### Steps:

1. **Create new Web Service on Render**
   - Go to: https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect GitHub repository

2. **Configure:**
   - Name: `procurement-streamlit`
   - Environment: `Python 3`
   - Build command: `pip install -r requirements_streamlit.txt`
   - Start command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`

3. **Add environment variable:**
   - In "Environment" tab add:
     - Key: `MCP_SERVER_URL`
     - Value: `https://procurement-agent-ai.onrender.com`

4. **Deploy**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment

5. **Share the link**
   - Render gives you URL like: `https://procurement-streamlit.onrender.com`
   - Share with users!

---

### **Option 3: Run Locally (For Testing)**

**Time needed:** 2 minutes

```bash
# Install dependencies
pip install -r requirements_streamlit.txt

# Set environment variable (optional, can enter in app)
export MCP_SERVER_URL="https://procurement-agent-ai.onrender.com"

# Run the app
streamlit run streamlit_app.py
```

Then open: http://localhost:8501

---

## 📋 What Users See (Step by Step)

### **Screen 1: Configuration**
```
⚙️ Server Configuration (on the left)
└─ MCP Server URL: [text input field]
└─ [Test Connection button]

📊 Procurement Agent (main area)
└─ Select Analysis Parameters
   ├─ Organization: ○ Use Default  ○ Select Specific (with ID input)
   ├─ Workflow: [Dropdown] exception-triage
   ├─ Result Limit: [Slider] 1-100
   └─ Autonomy Level: ○ Level 1 (Read-Only)  ○ Level 2 (Draft PO)

   [▶️ RUN ANALYSIS] (big blue button)
```

### **Screen 2: Results**
```
✅ Analysis completed successfully!

Actions Created: 2
Organization: Default (or your chosen ID)
Autonomy Level: 1
Status: ⚠️ Issues Found

Action Summary
├─ report_insight: 2
├─ flag_maverick_spend: 1
└─ flag_single_source_risk: 0

📥 Download Excel Report
[⬇️ Download Excel Report] ← Click to download to computer

✅ Click button above to download: tutorial_agent_run_20260315_092042.xlsx
📦 File size: 45.2 KB
```

### **Screen 3: Help Tab**
- How to use guide
- All 6 workflows explained
- Tips and troubleshooting

---

## 🎯 User Experience Flow

```
Non-Technical User Opens App
           ↓
Enters MCP Server URL (or it's pre-filled)
           ↓
Selects Organization (default or specific ID)
           ↓
Selects Workflow (6 options with descriptions)
           ↓
Clicks [RUN ANALYSIS]
           ↓
Sees results in 2-5 seconds
           ↓
Clicks [Download Excel Report]
           ↓
File appears in Downloads folder!
           ↓
Opens in Excel, Google Sheets, or LibreOffice
```

---

## ✅ What's Different from Base64 Approach

| Feature | Base64 Method | Streamlit App |
|---------|--------------|--------------|
| **Easy for users?** | ❌ No - need Python/tools | ✅ Yes - just click |
| **Download step** | ❌ Manual decode required | ✅ One click download |
| **Select org ID?** | ❌ Not in UI | ✅ Easy dropdown |
| **See results?** | ❌ Raw JSON | ✅ Nice formatted view |
| **Learning curve** | ❌ Technical | ✅ Zero technical |
| **Mobile friendly?** | ❌ No | ✅ Yes |

---

## 🔧 How It Works Behind the Scenes

```
User clicks [RUN ANALYSIS]
        ↓
Streamlit sends request to MCP Server
        ↓
MCP Server runs procurement agent
        ↓
Returns results + Base64 encoded Excel
        ↓
Streamlit app DECODES Base64 automatically
        ↓
Shows results in nice format
        ↓
Provides download button
        ↓
User gets Excel file directly!
```

**User never sees Base64 - it's all automatic!**

---

## 📊 Support Multiple Organizations

### **How it works:**

1. **Option A: Use Default (Recommended)**
   - App uses default organization from database
   - Users don't need to know their org ID
   - Works for most users

2. **Option B: Select Specific Organization**
   - Users can enter their organization ID
   - Filters analysis to just their org
   - Useful for large companies with multiple divisions

### **Example:**
```
Company: Acme Corp
├─ Organization 1: Manufacturing (Default)
├─ Organization 2: Distribution
└─ Organization 3: Retail

User selects Organization 2 → Gets analysis for Distribution only
```

---

## 🚀 After Deployment

1. **Share the Streamlit URL with users:**
   ```
   "Open this link to run procurement analysis and download reports:"
   https://procurement-streamlit.streamlit.app
   ```

2. **Users need NOTHING installed**
   - No Python
   - No dependencies
   - No Base64 tools
   - Just web browser!

3. **Troubleshooting link to share:**
   - Users visit "Help" tab in the app
   - All common issues explained
   - Self-service troubleshooting

---

## 💾 Server URLs to Use

**MCP Server (Backend):**
```
https://procurement-agent-ai.onrender.com
```

**Streamlit App (Frontend):**
```
https://procurement-streamlit.streamlit.app
(or your custom domain)
```

**Both must be running for the app to work!**

---

## ✨ Benefits for Your Organization

✅ **Zero technical knowledge needed** - Just click buttons
✅ **All organizations supported** - Select any org ID
✅ **Direct Excel downloads** - No decoding, no tools
✅ **Web-based** - Works on any device, any browser
✅ **Free to host** - Streamlit Cloud is free
✅ **Mobile friendly** - Works on phones and tablets
✅ **Real-time** - Results in seconds
✅ **Secure** - Read-only access, no data modifications

---

## 📞 Support

If users have issues:

1. **Check Help tab in app** - Most answers there
2. **Test server connection** - Click "Test Connection" button
3. **Check internet** - Must have network access
4. **Contact IT admin** - For server URL issues

---

## Next Steps

1. Choose deployment option (Streamlit Cloud recommended)
2. Follow deployment steps (5-10 minutes)
3. Test the app
4. Share URL with users
5. Users can immediately start downloading Excel reports!

**That's it! No more Base64 decoding for end users.**
