/**
 * Device Fingerprinting Hook
 * ===========================
 * Uses FingerprintJS to generate unique device identifiers
 * for trial abuse prevention
 */

import { useState, useEffect } from 'react';
import FingerprintJS from '@fingerprintjs/fingerprintjs';

interface DeviceFingerprintResult {
  deviceId: string | null;
  loading: boolean;
  error: string | null;
  confidence: number;
}

/**
 * Custom hook to get device fingerprint
 * 
 * @returns {DeviceFingerprintResult} Device fingerprint data
 */
export function useDeviceFingerprint(): DeviceFingerprintResult {
  const [deviceId, setDeviceId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0);

  useEffect(() => {
    let mounted = true;

    const getFingerprint = async () => {
      try {
        // Initialize FingerprintJS
        const fp = await FingerprintJS.load();

        // Get visitor identifier
        const result = await fp.get();

        if (mounted) {
          setDeviceId(result.visitorId);
          setConfidence(result.confidence.score);
          setLoading(false);

          // Log for debugging (remove in production)
          console.log('🔍 Device Fingerprint:', {
            visitorId: result.visitorId,
            confidence: result.confidence.score,
            components: Object.keys(result.components).length,
          });
        }
      } catch (err: any) {
        console.error('❌ Fingerprint error:', err);
        
        if (mounted) {
          setError(err.message || 'Failed to generate device fingerprint');
          setDeviceId('unknown'); // Fallback for privacy mode
          setLoading(false);
        }
      }
    };

    getFingerprint();

    return () => {
      mounted = false;
    };
  }, []);

  return { deviceId, loading, error, confidence };
}

/**
 * Get device fingerprint synchronously (for immediate use)
 * 
 * @returns {Promise<string>} Device fingerprint ID
 */
export async function getDeviceFingerprint(): Promise<string> {
  try {
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    return result.visitorId;
  } catch (error) {
    console.error('❌ Failed to get device fingerprint:', error);
    return 'unknown';
  }
}

/**
 * Check device trial eligibility with backend
 * 
 * @param {string} deviceId - Device fingerprint ID
 * @returns {Promise<object>} Trial eligibility info
 */
export async function checkDeviceEligibility(deviceId: string): Promise<{
  success: boolean;
  trial_allowed: boolean;
  reason: string;
  suspicious?: boolean;
  risk_score?: number;
}> {
  try {
    const response = await fetch('/api/users/check-device/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ device_id: deviceId }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('❌ Device eligibility check failed:', error);
    return {
      success: false,
      trial_allowed: true, // Default to allowing on error
      reason: 'Unable to verify device eligibility',
    };
  }
}
