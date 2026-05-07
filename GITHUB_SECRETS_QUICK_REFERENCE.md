# GitHub Secrets Quick Reference

Copy and paste these values into GitHub → Settings → Secrets and variables → Actions

---

## 1. AWS_ACCESS_KEY_ID
```
AKIAV7HDFDCOE5JDE45U
```

---

## 2. AWS_SECRET_ACCESS_KEY
```
hosoEmau8FPhol9ekGInsqfTam0wwPzCcCkasObi
```

---

## 3. EC2_HOST
```
54.183.119.39
```

---

## 4. EC2_SSH_KEY
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

## 5. DJANGO_SECRET_KEY

**⚠️ YOU NEED TO GENERATE THIS!**

Run this command on your local machine:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and add it as the secret value.

Example output (DO NOT USE THIS, generate your own):
```
django-insecure-abc123xyz789!@#$%^&*()_+-=[]{}|;:,.<>?
```

---

## 6. EMAIL_HOST_USER
```
alberttyagi123@gmail.com
```

Or use your preferred Gmail address.

---

## 7. EMAIL_HOST_PASSWORD

**⚠️ YOU NEED TO CREATE A GMAIL APP PASSWORD!**

Steps:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (if not already enabled)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and "Other (Custom name)"
5. Enter "SmartRisk" as the name
6. Click "Generate"
7. Copy the 16-character password (format: xxxx xxxx xxxx xxxx)
8. Remove spaces and add it as the secret value

Example (DO NOT USE THIS, generate your own):
```
abcdefghijklmnop
```

---

## ✅ Checklist

Before pushing to GitHub, make sure you've added all 7 secrets:

- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] EC2_HOST
- [ ] EC2_SSH_KEY
- [ ] DJANGO_SECRET_KEY (generated)
- [ ] EMAIL_HOST_USER
- [ ] EMAIL_HOST_PASSWORD (Gmail app password)

---

## 🚀 Next Steps

1. Add all 7 secrets to GitHub (Settings → Secrets and variables → Actions)
2. Push your code to GitHub: `git push origin main`
3. Go to Actions tab to monitor deployment
4. Wait for deployment to complete (5-10 minutes)
5. Access your application at http://54.183.119.39

---

**Last Updated**: May 8, 2026
