import React from 'react';
import type { SystemHealth, Language } from '../types';
import { getTranslation } from '../i18n';

interface TopNavProps {
  systemHealth: SystemHealth | null;
  gridMode: 1 | 4 | 9 | 16;
  onGridModeChange: (mode: 1 | 4 | 9 | 16) => void;
  lang: Language;
  onToggleLang: () => void;
  onOpenAddModal: () => void;
  onOpenDiagnoseModal: () => void;
  currentUser: { username: string; role: string } | null;
  onOpenLoginModal: () => void;
  onLogout: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  systemHealth,
  gridMode,
  onGridModeChange,
  lang,
  onToggleLang,
  onOpenAddModal,
  onOpenDiagnoseModal,
  currentUser,
  onOpenLoginModal,
  onLogout,
}) => {
  const t = getTranslation(lang);

  const activeCams = systemHealth?.capacity.active_cameras ?? 4;
  const maxCams = systemHealth?.capacity.max_cameras ?? 100;
  const storagePct = systemHealth?.storage.usage_percentage ?? 24;
  const bitrate = systemHealth?.network.total_inbound_mbps ?? 8.2;

  return (
    <header className="top-nav">
      {/* Brand Section */}
      <div className="brand-section">
        <div className="brand-logo-badge">M</div>
        <div>
          <div className="brand-title">{t.appTitle}</div>
          <div className="brand-subtitle">{t.appSubtitle}</div>
        </div>
      </div>

      {/* Telemetry Chips */}
      <div className="nav-center-metrics">
        <div className="telemetry-chip" title="Active cameras vs maximum licensed hardware capacity">
          <span className="chip-label">{t.capacityMeter}:</span>
          <span className="chip-val" style={{ color: '#10b981' }}>
            {activeCams} / {maxCams}
          </span>
        </div>

        <div className="telemetry-chip" title="Local + Cloud Hybrid Storage Allocation">
          <span className="chip-label">{t.storageMeter}:</span>
          <span className="chip-val">{storagePct}%</span>
        </div>

        <div className="telemetry-chip" title="Live aggregate inbound camera stream bitrate">
          <span className="chip-label">{t.throughputMeter}:</span>
          <span className="chip-val">{bitrate} Mbps</span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="nav-actions">
        {/* Matrix Grid Toggle */}
        <div className="view-grid-toggle">
          <button
            className={`grid-btn ${gridMode === 1 ? 'active' : ''}`}
            onClick={() => onGridModeChange(1)}
            title="Single Camera View"
          >
            {t.grid1}
          </button>
          <button
            className={`grid-btn ${gridMode === 4 ? 'active' : ''}`}
            onClick={() => onGridModeChange(4)}
            title="Quad 4-Camera View"
          >
            {t.grid4}
          </button>
          <button
            className={`grid-btn ${gridMode === 9 ? 'active' : ''}`}
            onClick={() => onGridModeChange(9)}
            title="9-Camera Matrix"
          >
            {t.grid9}
          </button>
          <button
            className={`grid-btn ${gridMode === 16 ? 'active' : ''}`}
            onClick={() => onGridModeChange(16)}
            title="16-Camera Matrix"
          >
            {t.grid16}
          </button>
        </div>

        {/* OpenSDK Diagnostic Tool Button */}
        <button
          className="btn btn-secondary"
          onClick={onOpenDiagnoseModal}
          title="OpenSDK & Stream Error Diagnostics"
        >
          🩺 {t.opensdkDiagnostics}
        </button>

        {/* Add Camera Button */}
        <button className="btn btn-primary" onClick={onOpenAddModal}>
          + {t.addCamera}
        </button>

        {/* Login / User Profile Button */}
        {currentUser ? (
          <button
            className="btn btn-secondary"
            onClick={onLogout}
            title={t.logout}
            style={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: '#34d399' }}
          >
            👤 {currentUser.username} ({t.logout})
          </button>
        ) : (
          <button
            className="btn btn-secondary"
            onClick={onOpenLoginModal}
            title={t.login}
            style={{ borderColor: 'var(--border-active)', color: '#60a5fa' }}
          >
            🔐 {t.login}
          </button>
        )}

        {/* Language Switcher */}
        <button
          className="btn btn-secondary"
          onClick={onToggleLang}
          style={{ fontFamily: 'var(--font-mono)', minWidth: '48px' }}
        >
          {lang === 'en' ? 'FA | فارسی' : 'EN | English'}
        </button>
      </div>
    </header>
  );
};
