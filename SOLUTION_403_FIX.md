# 🔧 Solusi Error 403 di Railway.app

## 📋 **Ringkasan Masalah**
Error 403 "Failed to fetch schedule data" terjadi saat aplikasi deployed di Railway.app tidak dapat mengakses website kuramanime.tel karena:
- Rate limiting oleh server target
- Deteksi bot behavior 
- Headers yang tidak cukup sophisticated
- Tidak ada retry mechanism

## ✅ **Solusi yang Diimplementasikan**

### 1. **Enhanced Request System** (`Config/config.py`)
- **User-Agent Pool**: 15+ User-Agent strings dari berbagai browser
- **Headers Rotation**: Headers yang lebih realistic dengan random referer
- **Retry Mechanism**: Exponential backoff dengan 3 retry attempts
- **Session Management**: Persistent session dengan cookies
- **Anti-Detection**: Random delays dan human-like behavior simulation

### 2. **Improved Error Handling** (`src/parser/Kuramanime/kuramanime.py`)
- **Detailed Error Messages**: Pesan error yang informatif untuk debugging
- **403 Specific Handling**: Deteksi dan handling khusus untuk error 403
- **Response Validation**: Validasi response content sebelum parsing
- **Logging**: Comprehensive logging untuk monitoring

### 3. **Health Check Endpoints** (`src/routes/kuramanime.py`)
- **Health Check**: `/api/krm/health` - Test koneksi ke source
- **403 Test**: `/api/krm/test-403` - Debug endpoint untuk reproduce 403 error

## 🚀 **Cara Deploy dan Testing**

### **Langkah 1: Deploy ke Railway.app**
```bash
# Commit changes
git add .
git commit -m "Fix 403 errors with enhanced request system"

# Push to Railway
git push origin main
```

### **Langkah 2: Testing di Production**
Setelah deploy, test endpoints berikut:

#### **1. Health Check**
```bash
curl https://your-railway-app.railway.app/api/krm/health
```

Expected response:
```json
{
  "status": 200,
  "message": "Health check completed",
  "data": {
    "status": "healthy",
    "response_code": 200,
    "message": "Connection test successful"
  }
}
```

#### **2. 403 Test Endpoint**
```bash
curl https://your-railway-app.railway.app/api/krm/test-403
```

Ini akan menunjukkan detail response dari server target.

#### **3. Original Endpoints**
```bash
# Test schedule endpoint (yang sebelumnya error 403)
curl https://your-railway-app.railway.app/api/krm/schedule/Senin

# Test anime view
curl https://your-railway-app.railway.app/api/krm/view/ongoing

# Test search
-railway-app.railway.app/api/krm/search?querycurl https://your=naruto
```

### **Langkah 3: Monitoring Logs**
Di Railway.app dashboard,查看 logs untuk monitoring:
- Request success rates
- Retry attempts
- Error patterns
- Response codes

## 🔍 **Debugging Tips**

### **Jika Masih Error 403:**

1. **Check Health Endpoint Response**
   ```bash
   curl https://your-railway-app.railway.app/api/krm/health
   ```

2. **Check 403 Test Endpoint**
   ```bash
   curl https://your-railway-app.railway.app/api/krm/test-403
   ```

3. **Monitor Railway Logs**
   - Go to Railway.app dashboard
   - Select your project
   - Go to "Deploy" section
   - Check logs for detailed error messages

### **Jika Error Different:**

#### **Error 429 (Rate Limited)**
- Headers sudah include retry mechanism
- Tunggu beberapa menit sebelum retry
- Check jika ada terlalu banyak requests

#### **Error 502/503 (Server Error)**
- Server target sedang maintenance
- Tunggu beberapa saat
- Check health endpoint nanti

#### **Error Timeout**
- Network connectivity issue
- Server target slow response
- Retry mechanism akan handle ini

## 🛠 **Advanced Configuration**

### **Adjusting Retry Settings**
Di `Config/config.py`, Anda bisa adjust:
```python
retry_strategy = Retry(
    total=3,              # Jumlah retry attempts
    backoff_factor=1,     # Delay multiplier
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
```

### **Adding More User Agents**
Tambahkan User-Agent baru di `USER_AGENTS` list untuk lebih variasi.

### **Adjusting Delays**
Modify delay settings di `request_with_retry` method:
```python
# Base delay untuk retry
delay_base = 1

# Human-like delay range
human_delay = random.uniform(0.5, 2.0)
```

## 📊 **Expected Results**

Setelah implementasi ini:
- ✅ Error 403 berkurang значительно
- ✅ Better error messages untuk debugging
- ✅ Automatic retry untuk transient failures
- ✅ Health monitoring endpoints
- ✅ Comprehensive logging

## 🚨 **Troubleshooting**

### **Jika masih tidak bekerja:**

1. **Check Railway Environment**
   - Pastikan environment variables ter-set dengan benar
   - Check Railway logs untuk errors

2. **Test Locally First**
   ```bash
   # Test locally sebelum deploy
   python main.py
   curl http://localhost:8000/api/krm/health
   ```

3. **Alternative Approach**
   Jika 403 masih terjadi, pertimbangkan:
   - Proxy/VPN untuk Railway.app
   - Different hosting provider
   - API key dari source website (jika tersedia)

## 📞 **Support**

Jika masih ada masalah:
1. Check Railway logs
2. Test health endpoints
3. Provide specific error messages dari logs
4. Include response dari test endpoints

---

**Catatan**: Solusi ini menggunakan teknik anti-detection yang umum untuk web scraping. Selalu pastikan mematuhi Terms of Service dari website yang di-scrape.
