import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

const SESSION_STORAGE_KEY = 'unirig_session_id';

export interface UseSessionReturn {
  sessionId: string | null;
  createSession: () => string;
  clearSession: () => void;
}

/**
 * Custom hook for session management using localStorage
 * Automatically creates a session ID if one doesn't exist
 */
export const useSession = (): UseSessionReturn => {
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Load session ID from localStorage on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      // Create new session if none exists
      const newSessionId = uuidv4();
      localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
      setSessionId(newSessionId);
    }
  }, []);

  const createSession = (): string => {
    const newSessionId = uuidv4();
    localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    setSessionId(newSessionId);
    return newSessionId;
  };

  const clearSession = () => {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    setSessionId(null);
  };

  return {
    sessionId,
    createSession,
    clearSession,
  };
};
