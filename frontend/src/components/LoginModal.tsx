import React, { useState, useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import type { Language } from '../types';
import { getTranslation } from '../i18n';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { username: string; role: string; token: string }) => void;
  lang: Language;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onLoginSuccess,
  lang,
}) => {
  const t = getTranslation(lang);
  const [tab, setTab] = useState<'password' | 'qr'>('password');

  // Username/Password state
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('Admin@123456');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // QR Login state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [qrSecondsLeft, setQrSecondsLeft] = useState<number>(120);
  const [qrStatus, setQrStatus] = useState<string>('pending');
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Initialize or refresh QR session
  const initQRSession = async () => {
    try {
      const res = await fetch('/api/v1/auth/qr/session', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setQrSecondsLeft(data.expires_in_seconds || 120);
        setQrStatus('pending');

        if (canvasRef.current) {
          QRCode.toCanvas(canvasRef.current, data.qr_payload, {
            width: 190,
            margin: 1,
            color: {
              dark: '#0f172a',
              light: '#f8fafc',
            },
          });
        }
      }
    } catch {
      // Offline fallback canvas
      if (canvasRef.current) {
        QRCode.toCanvas(canvasRef.current, 'molido://auth/qr?demo=1', {
          width: 190,
          margin: 1,
          color: { dark: '#0f172a', light: '#f8fafc' },
        });
      }
    }
  };

  // Switch to QR tab triggers session generation
  useEffect(() => {
    if (tab === 'qr' && isOpen) {
      initQRSession();
    }
  }, [tab, isOpen]);

  // QR Session countdown timer & status polling
  useEffect(() => {
    if (tab !== 'qr' || !sessionId || !isOpen) return;

    const timer = setInterval(() => {
      setQrSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setQrStatus('expired');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/auth/qr/status/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          setQrStatus(data.status);
          if (data.status === 'approved' && data.token) {
            clearInterval(pollInterval);
            clearInterval(timer);
            onLoginSuccess({
              username: data.token.username,
              role: data.token.role,
              token: data.token.access_token,
            });
            onClose();
          }
        }
      } catch {
        // Polling retry
      }
    }, 1500);

    return () => {
      clearInterval(timer);
      clearInterval(pollInterval);
    };
  }, [tab, sessionId, isOpen, onLoginSuccess, onClose]);

  if (!isOpen) return null;

  // Handle password submission
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (res.ok) {
        const data = await res.json();
        onLoginSuccess({
          username: data.username,
          role: data.role,
          token: data.access_token,
        });
        onClose();
      } else {
        setErrorMsg(t.loginFailed);
      }
    } catch {
      // Demo fallback if backend is offline
      if (username === 'admin' && password === 'Admin@123456') {
        onLoginSuccess({
          username: 'admin',
          role: 'admin',
          token: 'demo_token_123',
        });
        onClose();
      } else {
        setErrorMsg(t.loginFailed);
      }
    } finally {
      setLoading(false);
    }
  };

  // Simulate mobile scan & authorization
  const handleSimulateMobileScan = async () => {
    if (!sessionId) return;
    try {
      await fetch(`/api/v1/auth/qr/simulate-approve/${sessionId}`, { method: 'POST' });
    } catch {
      onLoginSuccess({
        username: 'admin',
        role: 'admin',
        token: 'simulated_qr_token',
      });
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-dialog"
        style={{ maxWidth: '440px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <div className="modal-title">🔐 {t.login}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {t.loginSubtitle}
            </div>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Tab Toggle */}
        <div className="tab-nav-panel">
          <button
            type="button"
            className={`tab-nav-btn ${tab === 'password' ? 'active' : ''}`}
            onClick={() => setTab('password')}
          >
            🔑 {t.usernameLoginTab}
          </button>
          <button
            type="button"
            className={`tab-nav-btn ${tab === 'qr' ? 'active' : ''}`}
            onClick={() => setTab('qr')}
          >
            📱 {t.qrLoginTab}
          </button>
        </div>

        <div className="modal-body">
          {/* Default Credentials Notice Callout */}
          <div
            style={{
              padding: '10px 12px',
              background: 'rgba(37, 99, 235, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '6px',
              fontSize: '12px',
            }}
          >
            <div style={{ fontWeight: 600, color: '#60a5fa', marginBottom: '4px' }}>
              💡 {t.defaultCredentialsNotice}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
              • {t.adminUser}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
              • {t.adminPass}
            </div>
          </div>

          {/* TAB 1: Password Login */}
          {tab === 'password' ? (
            <form onSubmit={handlePasswordLogin} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">{t.username}</label>
                <input
                  type="text"
                  className="form-input"
                  style={{ fontFamily: 'var(--font-mono)' }}
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">{t.password}</label>
                <input
                  type="password"
                  className="form-input"
                  style={{ fontFamily: 'var(--font-mono)' }}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              {errorMsg && (
                <div style={{ color: '#ef4444', fontSize: '12px', fontWeight: 500 }}>
                  ✕ {errorMsg}
                </div>
              )}

              <button
                type="submit"
                className="btn btn-primary"
                style={{ marginTop: '8px', width: '100%', padding: '10px' }}
                disabled={loading}
              >
                {loading ? '...' : t.submitLogin}
              </button>
            </form>
          ) : (
            /* TAB 2: QR Code Login */
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', maxWidth: '320px' }}>
                {t.qrInstructions}
              </div>

              {/* QR Code Container */}
              <div
                style={{
                  background: '#ffffff',
                  padding: '12px',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
                  position: 'relative',
                }}
              >
                <canvas ref={canvasRef} style={{ display: 'block' }} />

                {qrStatus === 'scanned' && (
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'rgba(15, 23, 42, 0.85)',
                      borderRadius: '8px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#34d399',
                      fontSize: '13px',
                      fontWeight: 600,
                    }}
                  >
                    <span>✓ Scanned!</span>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>Awaiting confirmation...</span>
                  </div>
                )}
              </div>

              {/* Timer & Refresh */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px' }}>
                <span style={{ color: 'var(--text-muted)' }}>{t.qrExpiry}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: qrSecondsLeft < 20 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                  {Math.floor(qrSecondsLeft / 60)}:{(qrSecondsLeft % 60).toString().padStart(2, '0')}
                </span>
                {qrSecondsLeft === 0 && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '2px 8px', fontSize: '11px' }}
                    onClick={initQRSession}
                  >
                    🔄 {t.qrRefresh}
                  </button>
                )}
              </div>

              {/* Instant Simulator Action */}
              <button
                type="button"
                className="btn btn-secondary"
                style={{ width: '100%', borderColor: 'var(--border-active)', color: '#60a5fa' }}
                onClick={handleSimulateMobileScan}
              >
                {t.qrSimulateScan}
              </button>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            {t.cancel}
          </button>
        </div>
      </div>
    </div>
  );
};
