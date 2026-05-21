/**
 * useTimezoneSync
 * ───────────────
 * Detects the visitor's IANA timezone from the browser and saves it to the
 * backend (POST /api/users/timezone/) once per LOGIN SESSION (not once ever).
 *
 * Re-syncs every time the user logs in (access_token changes) so the server
 * always has an up-to-date timezone for email alert formatting — fixing the
 * bug where ETHUSD/LTCUSD/XAUUSD emails showed UTC instead of local time.
 */

'use client';

import { useEffect, useRef } from 'react';
import { getApiUrl } from './config';

export function useTimezoneSync(accessToken: string | null | undefined) {
  // Track which token we've already synced — re-sync when token changes (new login).
  const lastSyncedToken = useRef<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    // Already synced for THIS token → skip (prevents spamming on every re-render)
    if (lastSyncedToken.current === accessToken) return;

    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!tz) return;

    fetch(`${getApiUrl()}/api/users/timezone/`, {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ timezone: tz }),
    })
      .then((res) => {
        if (res.ok) {
          lastSyncedToken.current = accessToken;
          console.debug(`[SmartRiskFX] Timezone synced: ${tz}`);
        }
      })
      .catch(() => {
        // Non-critical — silently ignore network errors; will retry next render
      });
  }, [accessToken]);
}