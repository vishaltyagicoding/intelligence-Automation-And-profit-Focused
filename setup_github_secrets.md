# 🔐 Quick GitHub Secrets Setup

## Copy-Paste Values for GitHub Secrets

Go to: **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

---

### 1. AWS_ACCESS_KEY_ID
```
AKIAV7HDFDCOE5JDE45U
```

---

### 2. AWS_SECRET_ACCESS_KEY
```
hosoEmau8FPhol9ekGInsqfTam0wwPzCcCkasObi
```

---

### 3. EC2_HOST
```
54.183.119.39
```

---

### 4. EC2_SSH_KEY
```
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAuy1aOAnvchtcrQ1VGdJo+FQEEQZ0mXlMASBfITZnz4ZCaPwy
7JWpyUKnlTxTF/IP2UEz3r19VqEWfPQfqGsULtNN2d8WAdHICkc/LSwd4MTEhKYG
QhfDQVtpGfaS3Oqt2nNRViDni0N+LS3FoIeY+AI6H2+1aAmM42HOKlmLuPV/2hcb
LkbU0zDvHmVTlGx3LhlU5UawVCM/0HlqbQN7YS9zTKyLgemO6eGIG3ax5GBMPfxq
28fXfYhXYmbZtY49igloiioPKxAES8m3mbCJVu2/XNfJf/MndFUXqM+5sQm5FLnj
AbTcy3yC/F0pRd9XC6UsAp3/kieIwmo6+AvJeQIDAQABAoIBACo07dUZGG9IkDtN
eFUcRyNH/qrAI+a/nU3buNfKZto60hrOU8VZcjG54AQc2DfcE4rP0xx06iBwrpt6
iPD3RFPSvglU7qd2YH9A1ZQgEJSwigfHUD3zEcpZDHgYS8GZAZ7yxfJ/9PZIP9l8
KsYqDWpPRj/0dpmBHc3gLhcKniEUh9fTzufc/Q/0Cmsjwuh7b8k2U8e+C2XlFHci
cIbyvgng6F+D1P0Rq7QzL798PsXP0dNv6z/TgH3jUtLyHfYaFWEXc2HksuDprYn/
HoImdpABxAZPtLek7/ws4kZCJYuAzRiyNGDCXvQ5DRjytP8+iRtpuz1Y7j6h23qh
LIDPgEkCgYEA6QRHthuUc+XQHe+cdJ/30rBD14eTmMdJbhLNHpWjJCGujnUNbiRd
s7JCKNXjP6A7pPHRcfJCyqxIfWj1i5LnLjPOzcrcK/RYJxYVictNkoiE2plP9rhK
ENU1JOeuNgSTkX5G5WXhw/I8y5MA1YkqNQvXwP7kK8sEKzOl2tYSlO8CgYEAzaOd
Lg+Lu3Dx6JVDwoGZDQrOk/Q9agJK95r6A2gszhLLK7iKWlyQluW9B7WfHhwd3oBr
KN3meClbjlZY3S9vq3dnzzZ8Q+rwBIEMNLajHcZmmz5SLGLPy2K4utDaWswfQHjo
fdoSFrC2frsGXv96ikjtAQNyHe2X8pjEvKw2GBcCgYBvpW5asgJCOcWq4kjblF4g
o/YNiddNZ4cmZ3nCgr4FLOI/PZRuxpvi4rFScZENxk9tq7PH3eTkyQF+nVCxTHTa
LVaUQfOWV9/48lrlh/SmFiVZvAWVWB2czRtGkH9nQHAYUSHU/ijbQvCgNdI7fhos
Cn2Y6kgXN5HKxVddcB69HwKBgE+B8hTMB++6FJ4jkCZVK1LimcqUxWYGauvfLMlC
bwhiNdG6sSuM3I6rVvHzJAllP5s2tbgAS8qr2u1mr0cdvyRhr25rl5I+9PwY1RpQ
fzLU8fkWGHl23va5PcllVPeEMpUf6mw2c4X4XycSsrzqNHvhBFm+9lFh+rzemjqE
rwmTAoGABt60Bf4viljZ5VIgRPeZ8rnEo0tb8aRn2vLGJlx9uGWJHSg7l9EyTfzo
vg0Zk4W3DVl09vaSV4gHHR+S93d+0Fw0B/U/wUWzicTFGTcTDknTMxR1U4SCX2zX
uun3ZW0SaUuNBHsRG3tIhE3hvxNJoWbR2N1WY8hE9MG46Yts8yM=
-----END RSA PRIVATE KEY-----
```

---

### 5. DJANGO_SECRET_KEY

**Generate a new one:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then paste the generated key.

---

### 6. EMAIL_HOST_USER
```
your-email@gmail.com
```
(Replace with your Gmail address)

---

### 7. EMAIL_HOST_PASSWORD

**Get Gmail App Password:**
1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to **App Passwords**
4. Select **Mail** and **Other (Custom name)**
5. Generate password
6. Copy the 16-character password
7. Paste it here

---

## ✅ Verification Checklist

After adding all secrets, verify:

- [ ] AWS_ACCESS_KEY_ID added
- [ ] AWS_SECRET_ACCESS_KEY added
- [ ] EC2_HOST added
- [ ] EC2_SSH_KEY added (with BEGIN/END lines)
- [ ] DJANGO_SECRET_KEY added
- [ ] EMAIL_HOST_USER added
- [ ] EMAIL_HOST_PASSWORD added

---

## 🚀 Ready to Deploy!

Once all secrets are added:

```bash
git add .
git commit -m "Setup GitHub Actions CI/CD"
git push origin main
```

GitHub Actions will automatically deploy to your EC2 server!

---

## 📊 Monitor Deployment

Go to: **GitHub Repository → Actions**

Watch the deployment progress in real-time!

---

**Made with ❤️ for SmartRisk**
