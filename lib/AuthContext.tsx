'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  manual_subscription?: string;  // 'activated' or 'deactivated'
  trial_status?: string;  // 'active' or 'inactive'
  subscription_status: {
    plan: string;
    status: string;
    is_active: boolean;
    days_remaining: number;
    trial_end?: string;  // ISO timestamp for precise countdown
    hours_remaining?: number;
    minutes_remaining?: number;
    trial_status?: string;  // 'active' or 'inactive'
  } | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  setAuthData: (userData: User, token: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  // Real-time subscription status check (every 5 seconds)
  useEffect(() => {
    if (!user) return;

    const checkSubscriptionStatus = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      try {
        const res = await fetch('/api/users/check-auth/', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (res.ok) {
          const data = await res.json();
          const newUser = data.user;
          
          // Check if subscription status changed
          const oldIsActive = user.subscription_status?.is_active;
          const newIsActive = newUser.subscription_status?.is_active;
          
          // If subscription was deactivated by admin
          if (oldIsActive && !newIsActive) {
            setUser(newUser);
            const currentPath = window.location.pathname;
            if (currentPath === '/dashboard' || currentPath === '/history' || currentPath.startsWith('/asset/')) {
              alert('⚠️ Your subscription has been deactivated. Please contact support.');
              router.push('/subscription');
            }
          }
          // If subscription was activated by admin
          else if (!oldIsActive && newIsActive) {
            setUser(newUser);
            const currentPath = window.location.pathname;
            if (currentPath === '/subscription') {
              alert('🎉 Your subscription has been activated! You now have full access.');
              router.push('/dashboard');
            }
          }
          // Update user data even if status didn't change (for countdown updates)
          else {
            setUser(newUser);
          }
        }
      } catch (error) {
        console.error('Subscription status check failed:', error);
      }
    };

    // Check immediately
    checkSubscriptionStatus();

    // Check every 5 seconds for real-time updates
    const interval = setInterval(checkSubscriptionStatus, 5000);

    return () => clearInterval(interval);
  }, [user?.subscription_status?.is_active, router]);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/users/check-auth/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/users/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (!data.success) {
      throw new Error(data.error || 'Login failed');
    }

    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    setUser(data.user);
    
    // Show welcome message
    alert(`Welcome back, ${data.user.full_name || data.user.email}! 🎉`);
    
    router.push('/dashboard');
  };

  const register = async (formData: any) => {
    const res = await fetch('/api/users/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    const data = await res.json();

    if (!data.success) {
      // Parse backend validation errors into human-friendly messages
      if (data.errors && typeof data.errors === 'object') {
        const messages: string[] = [];

        const fieldLabels: Record<string, string> = {
          email: 'Email',
          username: 'Username',
          password: 'Password',
          password2: 'Confirm Password',
          first_name: 'First Name',
          last_name: 'Last Name',
          non_field_errors: '',
        };

        const technicalToFriendly: Record<string, string> = {
          'This password is too common.': 'Please choose a stronger password — avoid common words like "password123".',
          'This password is entirely numeric.': 'Password must include letters, not just numbers.',
          'This field may not be blank.': 'This field cannot be empty.',
          'This field is required.': 'This field is required.',
          'Enter a valid email address.': 'Please enter a valid email address.',
          'A user with that email already exists.': 'This email is already registered. Try logging in instead.',
          'A user with this email already exists.': 'This email is already registered. Try logging in instead.',
          'A user with that username already exists.': 'This username is already taken. Please choose another.',
          'A user with this username already exists.': 'This username is already taken. Please choose another.',
          'This password is too short. It must contain at least 8 characters.': 'Password must be at least 8 characters long.',
          'The two password fields didn\'t match.': 'Passwords do not match. Please re-enter.',
          'Password fields didn\'t match.': 'Passwords do not match. Please re-enter.',
          'Ensure this field has no more than 150 characters.': 'This field is too long (max 150 characters).',
          'Ensure this field has no more than 254 characters.': 'This field is too long (max 254 characters).',
          'Username must be at least 3 characters long.': 'Username must be at least 3 characters long.',
          'Username is too long (max 150 characters).': 'Username is too long (max 150 characters).',
          'Email address is too long (max 254 characters).': 'Email address is too long (max 254 characters).',
          'First name is too long (max 150 characters).': 'First name is too long (max 150 characters).',
          'Last name is too long (max 150 characters).': 'Last name is too long (max 150 characters).',
        };

        for (const [field, errors] of Object.entries(data.errors)) {
          const errorList = Array.isArray(errors) ? errors : [errors];
          const label = fieldLabels[field] ?? field;

          for (const err of errorList) {
            const friendly = technicalToFriendly[err as string] ?? (err as string);
            messages.push(label ? `${label}: ${friendly}` : friendly);
          }
        }

        throw new Error(messages.join('\n'));
      }
      throw new Error(data.error || 'Registration failed. Please try again.');
    }

    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    setUser(data.user);
    
    // Show success message with trial info
    alert(`🎉 Welcome to NeuralTrade, ${data.user.full_name || data.user.email}!\n\n✅ Your account has been created successfully!\n🎁 You have 3 days of FREE access to all features.\n📊 Start exploring AI-powered trading signals now!\n\nEnjoy your trial! 🚀`);
    
    router.push('/dashboard');
  };

  const logout = async () => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      try {
        await fetch('/api/users/logout/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout failed:', error);
      }
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    router.push('/');
  };

  const setAuthData = (userData: User, token: string) => {
    setUser(userData);
    localStorage.setItem('access_token', token);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      isAuthenticated: !!user,
      setAuthData,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
