# Production Deployment Guide - Render.com

## Prerequisites

- GitHub account
- Render.com account (free tier available)
- Groq API key (or other LLM provider key)

---

## Step 1: Prepare Your Repository

### 1.1 Create .env.example (already done)

The `.env.example` file is already created. Never commit your actual `.env` file!

### 1.2 Commit and Push to GitHub

```bash
cd c:\laragon\www\task-assit
git add .
git commit -m "Production ready deployment"
git push origin main
```

---

## Step 2: Deploy on Render

### 2.1 Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the `task-assit` repository

### 2.2 Configure Service Settings

- **Name**: `task-assistant` (or your preferred name)
- **Region**: Choose closest to you (e.g., Oregon, Frankfurt)
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan**: Free (or paid for better performance)

### 2.3 Add Environment Variables

Click **"Advanced"** and add these environment variables:

#### Required Variables:

```
PYTHON_VERSION=3.11.0
DATABASE_URL=sqlite+aiosqlite:///./task_assistant.db
SECRET_KEY=[Click "Generate" button - Render will create a secure key]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
LLM_PROVIDER=grok
GROK_API_KEY=[Your Groq API key]
DEBUG=false
ALLOWED_ORIGINS=https://your-app-name.onrender.com
WS_HEARTBEAT_INTERVAL=30
RATE_LIMIT_PER_MINUTE=60
AUTH_RATE_LIMIT_PER_15MIN=5
```

#### Optional API Keys (add if needed):

```
ANTHROPIC_API_KEY=[Your Anthropic key]
OPENAI_API_KEY=[Your OpenAI key]
GEMINI_API_KEY=[Your Google Gemini key]
```

**Important**: Replace `your-app-name` in `ALLOWED_ORIGINS` with your actual Render app name!

### 2.4 Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Once deployed, you'll get a URL like: `https://your-app-name.onrender.com`

---

## Step 3: Post-Deployment Configuration

### 3.1 Update ALLOWED_ORIGINS

After deployment, update the `ALLOWED_ORIGINS` environment variable:

1. Go to your service in Render Dashboard
2. Click **"Environment"** tab
3. Edit `ALLOWED_ORIGINS` to: `https://your-actual-app-name.onrender.com`
4. Save (this will trigger a redeploy)

### 3.2 Test Your Application

1. Visit your Render URL
2. Register a new account
3. Test creating tasks via chat
4. Verify WebSocket connection works
5. Check Dashboard, Tasks, and Analytics views

---

## Step 4: Verify Production Health

### Health Check Endpoint

```bash
curl https://your-app-name.onrender.com/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "Task Assistant"
}
```

### Check API Documentation

Visit: `https://your-app-name.onrender.com/docs`

---

## Common Issues & Solutions

### Issue 1: Application Crashes on Startup

**Solution**: Check Render logs

- Go to service → **"Logs"** tab
- Look for error messages
- Common causes:
  - Missing environment variables
  - Database connection issues
  - Import errors

### Issue 2: WebSocket Not Connecting

**Solution**:

- Ensure your app uses `wss://` (secure WebSocket)
- Check browser console for errors
- Verify CORS settings in `ALLOWED_ORIGINS`

### Issue 3: Database Not Persisting

**Solution**: Render free tier uses ephemeral filesystem

- Consider upgrading to paid plan with persistent disk
- Or migrate to PostgreSQL (recommended for production)

### Issue 4: CORS Errors

**Solution**:

- Update `ALLOWED_ORIGINS` to include your Render domain
- Format: `https://your-app-name.onrender.com` (no trailing slash)
- Multiple origins: separate with commas

### Issue 5: LLM API Errors

**Solution**:

- Verify API key is correct in environment variables
- Check API quota/limits
- Review Render logs for error details

---

## Upgrading to PostgreSQL (Recommended)

### Why PostgreSQL?

- Better for production
- Persistent data storage
- Better performance
- ACID compliance

### Steps:

1. **Create PostgreSQL Database on Render**:
   - Dashboard → **"New +"** → **"PostgreSQL"**
   - Name it (e.g., `task-assistant-db`)
   - Free tier available

2. **Update Environment Variable**:

   ```
   DATABASE_URL=postgresql+asyncpg://[connection-string-from-render]
   ```

3. **Update requirements.txt**:

   ```
   asyncpg==0.29.0
   psycopg2-binary==2.9.9
   ```

4. **Redeploy**

---

## Monitoring & Maintenance

### View Logs

- Render Dashboard → Your Service → **"Logs"**
- Real-time log streaming
- Filter by date/time

### Monitor Performance

- Render Dashboard → Your Service → **"Metrics"**
- CPU usage
- Memory usage
- Response times

### Auto-Deploy on Push

- Render automatically deploys when you push to `main` branch
- Disable in Settings if you want manual deploys

---

## Security Best Practices

### ✅ Completed:

- Environment variables for secrets
- `.env` in `.gitignore`
- Secure token generation
- CORS configuration
- Health check endpoint
- Non-root user in Docker

### 🔒 Additional Recommendations:

1. **Use Strong API Keys**: Never share your API keys
2. **Enable HTTPS**: Render does this automatically
3. **Rate Limiting**: Already configured in app
4. **Input Validation**: Already implemented with Pydantic
5. **Regular Updates**: Keep dependencies updated

---

## Cost Optimization (Free Tier)

### Render Free Tier Limits:

- 750 hours/month of runtime
- 512 MB RAM
- Shared CPU
- Spins down after 15 minutes of inactivity
- Cold start: ~30 seconds

### Keep Your App Active:

- Use a uptime monitoring service (UptimeRobot, etc.)
- Ping your health endpoint every 14 minutes
- **Note**: This may consume more of your free hours

---

## Backup & Recovery

### Database Backup (SQLite):

1. Download database file from Render dashboard
2. Or upgrade to PostgreSQL with automated backups

### Code Backup:

- Always in Git repository
- Push regularly to GitHub

---

## Scaling for Production

### When to Upgrade:

- More than 100 concurrent users
- Need faster response times
- Require persistent data storage
- 24/7 uptime required

### Upgrade Path:

1. **Render Starter Plan** ($7/month)
   - 1 GB RAM
   - Always-on service
   - Faster CPU

2. **PostgreSQL Database** ($7/month)
   - Persistent storage
   - Automated backups
   - Better performance

3. **Professional Plan** ($25/month)
   - 4 GB RAM
   - Priority support
   - Multiple regions

---

## Testing Production Deployment

### Pre-Launch Checklist:

- [ ] Health check returns "healthy"
- [ ] User registration works
- [ ] User login works
- [ ] Chat interface loads
- [ ] Tasks can be created
- [ ] WebSocket connects successfully
- [ ] Dashboard shows stats
- [ ] Analytics charts display
- [ ] All API endpoints respond
- [ ] CORS configured correctly
- [ ] Environment variables set
- [ ] Logs show no errors

### Load Testing:

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 https://your-app-name.onrender.com/api/health
```

---

## Support & Resources

### Render Documentation:

- [Render Docs](https://render.com/docs)
- [Python Guide](https://render.com/docs/deploy-python)
- [Environment Variables](https://render.com/docs/environment-variables)

### FastAPI Documentation:

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Deployment](https://fastapi.tiangolo.com/deployment/)

### Groq API:

- [Groq Console](https://console.groq.com/)
- [API Documentation](https://console.groq.com/docs)

---

## Quick Deploy Checklist

```
✅ Push code to GitHub
✅ Create Render web service
✅ Set environment variables
✅ Deploy and wait for build
✅ Update ALLOWED_ORIGINS with actual URL
✅ Test registration and login
✅ Verify WebSocket connection
✅ Test task creation via chat
✅ Check all views work
✅ Monitor logs for errors
```

---

## Example Production URLs

After deployment, your app will have:

- **Frontend**: `https://task-assistant.onrender.com`
- **API Docs**: `https://task-assistant.onrender.com/docs`
- **Health**: `https://task-assistant.onrender.com/api/health`
- **WebSocket**: `wss://task-assistant.onrender.com/api/ws`

---

## Troubleshooting Commands

### Check Service Status:

```bash
curl https://your-app-name.onrender.com/api/health
```

### Test Authentication:

```bash
curl -X POST https://your-app-name.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test123"}'
```

### Check Logs:

- Render Dashboard → Logs tab
- Look for startup errors
- Check for missing environment variables

---

## Next Steps After Deployment

1. **Custom Domain** (Optional):
   - Render Settings → Custom Domain
   - Add your domain (e.g., `taskassistant.com`)
   - Configure DNS records

2. **Monitoring**:
   - Set up uptime monitoring
   - Configure error alerts
   - Track usage metrics

3. **Continuous Deployment**:
   - Already enabled by default
   - Push to `main` → Auto deploy

4. **Database Migrations**:
   - Use Alembic for schema changes
   - Test migrations locally first

---

## Success! 🎉

Your Task Assistant is now live in production!

**Share your deployment URL**: `https://your-app-name.onrender.com`
