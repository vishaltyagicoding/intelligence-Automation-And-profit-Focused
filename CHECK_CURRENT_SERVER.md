# Check Which Server Your Browser Is Using

## Quick Test

Open browser console (F12) and run:

```javascript
// Check which server you're connected to
fetch('https://smartriskfx.com/api/health/')
  .then(r => r.json())
  .then(data => console.log('Server Response:', data))
  .catch(e => console.error('Error:', e));
```

## Check DNS

Open Command Prompt or PowerShell:

```bash
nslookup smartriskfx.com
```

**Expected Result (AFTER DNS update)**:
```
Server:  UnKnown
Address:  192.168.1.1

Non-authoritative answer:
Name:    smartriskfx.com
Address:  13.250.19.107
```

**Current Result (BEFORE DNS update)**:
```
Name:    smartriskfx.com
Address:  54.183.178.141  ← OLD US SERVER
```

## The Problem

If DNS shows `54.183.178.141`, your browser is STILL connecting to the old US server, which:
- ❌ Cannot access PAXGUSDT (HTTP 451)
- ❌ May have old code
- ❌ May have different WebSocket configuration

## The Solution

**YOU MUST UPDATE DNS RECORDS NOW**

1. Log into your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.)
2. Find DNS management for smartriskfx.com
3. Update A records:
   - smartriskfx.com → 13.250.19.107
   - www.smartriskfx.com → 13.250.19.107
4. Set TTL to 300 seconds (5 minutes)
5. Wait 5-30 minutes for propagation
6. Test again with `nslookup smartriskfx.com`

## After DNS Update

Once DNS points to Singapore server (13.250.19.107):
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Check console - warnings should be MUCH fewer
4. XAUUSD should load without errors
