# Email Verification & Password Reset Setup Guide

## 📧 Overview
This system implements secure email verification and password reset functionality with 4-digit OTP codes sent to real email addresses.

## ✨ Features Implemented

### Backend
- ✅ Email verification with 4-digit OTP (expires in 10 minutes)
- ✅ OTP resend functionality with rate limiting
- ✅ Forgot password with reset OTP
- ✅ Password reset with OTP verification
- ✅ Beautiful HTML email templates
- ✅ Login blocked for unverified users
- ✅ Automatic welcome email after verification

### Frontend
- ✅ Email verification page with 4 separate OTP input boxes
- ✅ Forgot password flow (email → OTP → new password)
- ✅ Auto-focus and paste support for OTP inputs
- ✅ Resend OTP with 60-second cooldown
- ✅ Beautiful gradient UI with animations
- ✅ Automatic redirects after verification/reset

## 🛠️ Setup Instructions

### 1. Install Backend Dependencies

Prefer the pip-tools workflow (recommended) — see the "Recommended dependency workflow" section below. If you want a quick one-off install for development, install packages with a version of `aiosmtplib` that is compatible with `fastapi-mail` (fastapi-mail requires `aiosmtplib<3.0`). For example:

```bash
cd /home/aizr/SCOMED/Chattera
# quick dev install (use venv)
python3 -m pip install --upgrade pip
python3 -m pip install fastapi-mail==1.4.1 aiosmtplib==2.3.2
```

### 2. Configure Email (Gmail Example)

#### Option A: Gmail with App Password (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Soceyo Backend"
   - Copy the 16-character password

3. **Update `.env` file**:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Soceyo
```

#### Option B: SendGrid (Alternative)

1. Create free account at https://sendgrid.com
2. Generate API key
3. Update `.env`:
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=your-verified-sender@domain.com
SMTP_FROM_NAME=Soceyo
```

### 3. Start Backend

```bash
cd /home/aizr/SCOMED/Chattera
python3 -m uvicorn app.main:app --reload
```

### 4. Start Frontend

```bash
cd /home/aizr/SCOMED/soceyo-frontend
npm run dev
```

## 🧪 Testing Flow

### Registration & Email Verification

1. **Register a new user**:
   - Go to http://localhost:3000/register
   - Fill in username, email (use a real email you can access), and password
   - Click "Create Account"

2. **Check your email**:
   - You should receive a beautiful email with a 4-digit OTP code
   - Subject: "🔐 Verify Your Email - Soceyo"

3. **Verify email**:
   - You'll be redirected to `/verify-email?email=...`
   - Enter the 4-digit code (you can paste it)
   - Click "Verify Email"
   - You'll receive a welcome email

4. **Login**:
   - Go to http://localhost:3000/login
   - Login with your credentials
   - You should be able to access the app

### Testing Unverified User Block

1. Try to login before verifying email
2. You should see error: "Email not verified"
3. You'll be redirected to verification page

### Forgot Password Flow

1. **Request password reset**:
   - Go to http://localhost:3000/login
   - Click "Forgot password?"
   - Enter your email
   - Click "Send Reset Code"

2. **Check your email**:
   - You should receive an email with a 4-digit reset code
   - Subject: "🔐 Reset Your Password - Soceyo"

3. **Reset password**:
   - You'll be redirected to `/reset-password?email=...`
   - Enter the 4-digit code
   - Enter and confirm your new password
   - Click "Reset Password"

4. **Login with new password**:
   - Go to login page
   - Use your new password

### Resend OTP

1. On verification page, wait for OTP to expire (or just test immediately)
2. Click "Resend Code"
3. Check email for new OTP
4. 60-second cooldown prevents spam

## 📋 API Endpoints

### Authentication
- `POST /api/register` - Register user (sends OTP)
- `POST /api/login` - Login (requires verified email)

### Email Verification
- `POST /api/verify-email` - Verify email with OTP
  ```json
  { "email": "user@example.com", "otp_code": "1234" }
  ```
- `POST /api/resend-otp` - Resend verification OTP
  ```json
  { "email": "user@example.com" }
  ```

### Password Reset
- `POST /api/forgot-password` - Request password reset (sends OTP)
  ```json
  { "email": "user@example.com" }
  ```
- `POST /api/reset-password` - Reset password with OTP
  ```json
  {
    "email": "user@example.com",
    "otp_code": "1234",
    "new_password": "newpassword123"
  }
  ```

## 🎨 Email Templates

Three beautiful HTML email templates are included:

1. **Verification Email** (Purple gradient)
   - 4-digit OTP code
   - 10-minute expiry notice
   - Professional design

2. **Password Reset Email** (Red gradient)
   - 4-digit reset code
   - Security warning
   - 10-minute expiry notice

3. **Welcome Email** (Green gradient)
   - Sent after successful verification
   - Feature highlights
   - Call-to-action button

## 🔒 Security Features

- ✅ OTPs expire after 10 minutes
- ✅ OTPs are cleared after use
- ✅ Password reset tokens are one-time use
- ✅ Argon2 password hashing
- ✅ Rate limiting on resend (60-second cooldown)
- ✅ HTTPS/TLS for email transmission
- ✅ No email enumeration (same response for valid/invalid emails on forgot password)

## 🐛 Troubleshooting

### Email not sending

1. **Check SMTP credentials**:
   ```bash
   # Test Python script
   python3 -c "
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print('✅ SMTP connection successful!')
   server.quit()
   "
   ```

2. **Check backend logs**:
   - Look for email-related errors in uvicorn console
   - Check for "Failed to send email" messages

3. **Gmail specific issues**:
   - Ensure 2FA is enabled
   - Use App Password, not regular password
   - Check "Less secure app access" is NOT enabled (use App Password instead)

### OTP not working

1. **Check OTP expiry**:
   - OTPs expire after 10 minutes
   - Request a new one if expired

2. **Check database**:
   - Verify user has `otp_code` and `otp_expires_at` fields
   - Check Neo4j browser for user properties

### Frontend errors

1. **API connection issues**:
   - Ensure backend is running on http://localhost:8000 (or configured URL)
   - Check CORS settings in backend

2. **Redirect issues**:
   - Verify email is being passed in URL parameters
   - Check browser console for errors

## � Recommended dependency workflow (best practice)

Use a minimal top-level dependency file (`requirements.in`) and generate a pinned `requirements.txt` using `pip-tools` so your deployments are reproducible and avoid manual transitive-pinning conflicts.

1. Install pip-tools in your development venv:

```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install pip-tools
```

2. Edit `requirements.in` (this repo includes one at the project root listing direct deps).

3. Generate a fully pinned `requirements.txt`:

```bash
# from project root (inside an activated venv)
pip-compile requirements.in --output-file requirements.txt
```

4. Sync your venv to the pinned file (optional, replaces env packages):

```bash
pip-sync requirements.txt
```

Notes:
- Keep `requirements.in` minimal (only direct dependencies). Commit both `requirements.in` and the generated `requirements.txt`.
- Avoid manually pinning transitive dependencies in `requirements.in`; let the resolver pick compatible versions.
- Run `python -m pip check` after installs to detect conflicts.

## �📝 Database Schema Changes

The `User` model now includes:

```python
is_verified = StringProperty(default="false")  # "true" or "false"
otp_code = StringProperty(required=False)  # 4-digit OTP
otp_expires_at = DateTimeProperty(required=False)  # Expiry timestamp
reset_token = StringProperty(required=False)  # Password reset OTP
reset_token_expires_at = DateTimeProperty(required=False)  # Reset expiry
```

## 🚀 Production Considerations

1. **Email Service**:
   - Use SendGrid, AWS SES, or Mailgun for production
   - Configure proper SPF, DKIM, and DMARC records
   - Set up email templates in the service

2. **Rate Limiting**:
   - Implement Redis-based rate limiting for OTP requests
   - Limit OTP attempts per IP/email

3. **Monitoring**:
   - Track email delivery rates
   - Monitor failed OTP attempts
   - Set up alerts for high failure rates

4. **Security**:
   - Use environment-specific SMTP credentials
   - Rotate API keys regularly
   - Implement CAPTCHA on registration/forgot password

## ✅ Next Steps

1. Install dependencies: `pip install fastapi-mail aiosmtplib`
2. Configure Gmail App Password in `.env`
3. Restart backend server
4. Test registration flow with real email
5. Verify email works end-to-end
6. Test forgot password flow
7. Deploy to production with SendGrid/AWS SES
