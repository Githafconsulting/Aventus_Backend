# 🚀 Quick Setup Guide for Aventus Backend

Your `.env` file has been created! Follow these steps to complete the setup:

## ✅ Step 1: Get Supabase Database Password

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project: **evphdhrlgpwrwwsfjbxh**
3. Click on **Settings** (gear icon) in the left sidebar
4. Click on **Database**
5. Scroll down to **Connection string** section
6. Click on **URI** tab
7. Copy the password (it's the part after `postgres:` and before `@`)

**Alternative Method:**
1. In Supabase Dashboard > Settings > Database
2. Look for **Database Password**
3. Click **Reset Database Password** if you don't have it
4. Copy the new password

8. Open `.env` file in this directory
9. Replace `[YOUR-DATABASE-PASSWORD]` with your actual password:
   ```
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@db.evphdhrlgpwrwwsfjbxh.supabase.co:5432/postgres
   ```

## ✅ Step 2: Get Resend API Key (Free Email Service)

1. Go to https://resend.com
2. Sign up for a free account (3,000 emails/month)
3. Verify your email
4. Go to **API Keys** section
5. Click **Create API Key**
6. Copy the API key (starts with `re_`)
7. Update `.env` file:
   ```
   RESEND_API_KEY=re_your_actual_key_here
   ```

**For Testing:** You can use `onboarding@resend.dev` as FROM_EMAIL (already set in .env)

**For Production:** Add your own domain and verify it in Resend settings

## ✅ Step 3: Generate Secure SECRET_KEY

Run this command in your terminal:

**Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**Mac/Linux:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and update `.env`:
```
SECRET_KEY=the_generated_key_here
```

## ✅ Step 4: Install Dependencies

```bash
# Make sure you're in the backend directory
cd "C:\Users\papcy\Desktop\Aventus Backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## ✅ Step 5: Verify Configuration

```bash
python check_env.py
```

This will check if all required variables are set correctly.

## ✅ Step 6: Initialize Database

```bash
python seed_db.py
```

This creates the database tables and test admin accounts:
- **Super Admin**: superadmin@aventus.com / superadmin123
- **Admin**: admin@aventus.com / admin123
- **Manager**: manager@aventus.com / manager123

## ✅ Step 7: Run the Server

```bash
python run.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **API Documentation**: http://localhost:8000/redoc

## 🧪 Step 8: Test the API

Open http://localhost:8000/docs in your browser

1. Click **Authorize** button
2. Login with: admin@aventus.com / admin123
3. Test the contractor creation endpoint

## 📧 Email Configuration Notes

### For Development/Testing:
- Use `FROM_EMAIL=onboarding@resend.dev` (already set)
- Emails will work immediately with Resend API key

### For Production:
1. Add your domain in Resend dashboard
2. Add DNS records to verify domain
3. Update `FROM_EMAIL=noreply@yourdomain.com`

## 🔐 Your Supabase Project Info

- **Project URL**: https://evphdhrlgpwrwwsfjbxh.supabase.co
- **Project Ref**: evphdhrlgpwrwwsfjbxh
- **Anon Key**: Already in .env file
- **Database Host**: db.evphdhrlgpwrwwsfjbxh.supabase.co

## 🚨 Common Issues & Solutions

### Issue: "Could not connect to database"
**Solution**:
- Make sure you replaced `[YOUR-DATABASE-PASSWORD]` in .env
- Check if your Supabase project is active
- Verify the password is correct

### Issue: "Failed to send email"
**Solution**:
- Verify RESEND_API_KEY is correct
- Check if you're using `onboarding@resend.dev` for testing
- Make sure your Resend account is verified

### Issue: "ModuleNotFoundError"
**Solution**:
- Activate virtual environment: `venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

### Issue: Port 8000 already in use
**Solution**:
- Change PORT in .env to 8001 or another available port
- Or stop the process using port 8000

## 📝 Quick Command Reference

```bash
# Activate virtual environment
venv\Scripts\activate

# Run server
python run.py

# Seed database
python seed_db.py

# Check environment
python check_env.py

# Install new dependencies
pip install -r requirements.txt

# Deactivate virtual environment
deactivate
```

## 🎯 What's Next?

Once the backend is running:
1. Test the API at http://localhost:8000/docs
2. Integrate with your Next.js frontend
3. Test the complete contractor onboarding flow

## 📚 Documentation

- **API Documentation**: See `API_DOCUMENTATION.md`
- **Full Setup Guide**: See `README.md`
- **Interactive Docs**: http://localhost:8000/docs (when running)

## 🆘 Need Help?

If you encounter any issues:
1. Check the error message in the terminal
2. Verify all environment variables in .env
3. Check if database connection is working
4. Verify Resend API key is valid

---

**Ready to start?** Follow the steps above, and you'll be up and running in minutes! 🚀
