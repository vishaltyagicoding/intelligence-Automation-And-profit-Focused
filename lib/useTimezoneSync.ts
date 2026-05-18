/**
 * useTimezoneSync
 * ───────────────
 * Detects the visitor's IANA timezone from the browser and saves it to the
 * backend (POST /api/users/timezone/) once per session.
 *
 * This ensures:
 *  • Email alert timestamps are shown in the subscriber's local time.
 *  • No manual timezone setting is needed — it's fully automatic.
 */

'use client';

import { useEffect } from 'react';
import { getApiUrl } from './config';

const TZ_SYNC_KEY = 'srfx_tz_synced'; // sessionStorage key

export function useTimezoneSync(accessToken: string | null | undefined) {
  useEffect(() => {
    if (!accessToken) return;

    // Only sync once per browser session to avoid spamming the API
    if (typeof window !== 'undefined' && sessionStorage.getItem(TZ_SYNC_KEY)) return;

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
          sessionStorage.setItem(TZ_SYNC_KEY, tz);
          console.debug(`[SmartRiskFX] Timezone synced: ${tz}`);
        }
      })
      .catch(() => {
        // Non-critical — silently ignore network errors
      });
  }, [accessToken]);
}