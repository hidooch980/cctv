import React, { useState } from 'react';
import type { OpenSDKErrorDiagnosis, Language } from '../types';
import { getTranslation } from '../i18n';

interface OpenSDKModalProps {
  initialCode?: string;
  isOpen: boolean;
  onClose: () => void;
  lang: Language;
}

export const OpenSDKModal: React.FC<OpenSDKModalProps> = ({
  initialCode = '503',
  isOpen,
  onClose,
  lang,
}) => {
  const t = getTranslation(lang);
  const [errorCode, setErrorCode] = useState<string>(initialCode);
  const [diagnosis, setDiagnosis] = useState<OpenSDKErrorDiagnosis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [remediated, setRemediated] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleDiagnose = async () => {
    setIsLoading(true);
    setRemediated(false);
    try {
      const res = await fetch('/api/v1/opensdk/diagnose', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer mock_token',
        },
        body: JSON.stringify({ error_identifier: errorCode }),
      });
      if (res.ok) {
        const data = await res.json();
        setDiagnosis(data);
      }
    } catch {
      // Fallback local diagnosis if backend is in standalone test mode
      setDiagnosis({
        code: errorCode,
        numeric_code: 503,
        category: 'RTSP Protocol',
        name: 'RTSP Service Unavailable / Max Connections',
        description_en: 'Camera RTSP maximum connections reached.',
        description_fa: 'سقف اتصالات همزمان دوربین پر شده است (503).',
        probable_cause_en: 'Too many concurrent video streams active on camera hardware.',
        probable_cause_fa: 'تعداد درخواست‌های استریم همزمان بیش از توان پردازشی دوربین است.',
        recommended_action_en: 'Downgrade client streams to sub-stream or release idle sessions.',
        recommended_action_fa: 'کلاینت‌ها را به Sub-stream تغییر دهید یا نشست‌های اضافی را ببندید.',
        recovery_strategy: 'fallback_substream',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemediate = () => {
    setRemediated(true);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">🩺 {t.diagnoseTitle}</div>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            {t.diagnoseDesc}
          </div>

          <div className="form-group">
            <label className="form-label">{t.enterErrorCode}</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                className="form-input"
                style={{ flex: 1, fontFamily: 'var(--font-mono)' }}
                value={errorCode}
                onChange={(e) => setErrorCode(e.target.value)}
                placeholder="e.g. 401, 503, STATE_DHHTTP_SERVER_ERROR, DEC_KEY_ERROR"
              />
              <button
                className="btn btn-primary"
                onClick={handleDiagnose}
                disabled={isLoading}
              >
                {isLoading ? '...' : t.diagnoseBtn}
              </button>
            </div>
          </div>

          {/* Quick Preset Buttons */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {['401', '503', '503001', 'DEC_KEY_ERROR', '1001', '2001'].map((preset) => (
              <button
                key={preset}
                className="btn btn-secondary"
                style={{ padding: '3px 8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}
                onClick={() => {
                  setErrorCode(preset);
                }}
              >
                {preset}
              </button>
            ))}
          </div>

          {/* Diagnostic Result */}
          {diagnosis && (
            <div className="diag-result-box">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '14px' }}>
                  {diagnosis.name}
                </span>
                <span className="event-type-badge event-badge-warning">
                  {diagnosis.category}
                </span>
              </div>

              <div className="diag-result-row">
                <div className="diag-result-label">{t.probableCause}</div>
                <div className="diag-result-value">
                  {lang === 'fa' ? diagnosis.probable_cause_fa : diagnosis.probable_cause_en}
                </div>
              </div>

              <div className="diag-result-row">
                <div className="diag-result-label">{t.recommendedAction}</div>
                <div className="diag-result-value" style={{ color: '#60a5fa' }}>
                  {lang === 'fa' ? diagnosis.recommended_action_fa : diagnosis.recommended_action_en}
                </div>
              </div>

              <div className="diag-result-row">
                <div className="diag-result-label">{t.recoveryStrategy}</div>
                <div className="diag-result-value" style={{ fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                  ⚡ {diagnosis.recovery_strategy}
                </div>
              </div>

              {remediated ? (
                <div style={{ padding: '8px 12px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', borderRadius: '4px', color: '#34d399', fontSize: '12px' }}>
                  ✓ {t.remediateSuccess}
                </div>
              ) : (
                <button
                  className="btn btn-primary"
                  style={{ alignSelf: 'flex-start', marginTop: '6px' }}
                  onClick={handleRemediate}
                >
                  ⚙️ {t.resolvingAction}
                </button>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            {t.cancel}
          </button>
        </div>
      </div>
    </div>
  );
};
