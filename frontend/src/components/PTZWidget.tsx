import React, { useState } from 'react';
import type { Camera, Language } from '../types';
import { getTranslation } from '../i18n';

interface PTZWidgetProps {
  camera: Camera | null;
  lang: Language;
}

export const PTZWidget: React.FC<PTZWidgetProps> = ({ camera, lang }) => {
  const t = getTranslation(lang);
  const [speed, setSpeed] = useState<number>(0.5);
  const [lastAction, setLastAction] = useState<string>('idle');

  const handlePTZ = async (action: string) => {
    if (!camera) return;
    setLastAction(action);

    try {
      await fetch(`/api/v1/cameras/${camera.id}/ptz`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer mock_token',
        },
        body: JSON.stringify({ action, speed }),
      });
    } catch {
      // Offline fallback handling
    }
  };

  if (!camera || !camera.ptz_supported) {
    return (
      <div className="ptz-widget" style={{ opacity: 0.6 }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {t.ptzControls}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
          {camera ? `${camera.name} does not support PTZ mechanical motors.` : 'Select a PTZ camera from the matrix.'}
        </div>
      </div>
    );
  }

  return (
    <div className="ptz-widget">
      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
        <span style={{ fontSize: '13px', fontWeight: 600 }}>{t.ptzControls}</span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{camera.name}</span>
      </div>

      {/* D-Pad Directional Controls */}
      <div className="ptz-dpad">
        <button className="dpad-btn" title="North-West" onClick={() => handlePTZ('pan_left')}>↖</button>
        <button className="dpad-btn" title="Tilt Up" onClick={() => handlePTZ('tilt_up')}>▲</button>
        <button className="dpad-btn" title="North-East" onClick={() => handlePTZ('pan_right')}>↗</button>

        <button className="dpad-btn" title="Pan Left" onClick={() => handlePTZ('pan_left')}>◀</button>
        <div className="dpad-btn dpad-center" onClick={() => handlePTZ('stop')}>STOP</div>
        <button className="dpad-btn" title="Pan Right" onClick={() => handlePTZ('pan_right')}>▶</button>

        <button className="dpad-btn" title="South-West" onClick={() => handlePTZ('pan_left')}>↙</button>
        <button className="dpad-btn" title="Tilt Down" onClick={() => handlePTZ('tilt_down')}>▼</button>
        <button className="dpad-btn" title="South-East" onClick={() => handlePTZ('pan_right')}>↘</button>
      </div>

      {/* Optical Zoom Buttons */}
      <div className="ptz-zoom-controls">
        <button className="btn btn-secondary" onClick={() => handlePTZ('zoom_in')}>
          🔍 {t.zoomIn}
        </button>
        <button className="btn btn-secondary" onClick={() => handlePTZ('zoom_out')}>
          🔍 {t.zoomOut}
        </button>
      </div>

      {/* Motor Speed Slider */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>{t.speed}</span>
          <span>{Math.round(speed * 100)}%</span>
        </div>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.1"
          value={speed}
          onChange={(e) => setSpeed(parseFloat(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--color-accent)' }}
        />
      </div>

      {lastAction !== 'idle' && (
        <div style={{ fontSize: '11px', color: '#10b981', fontFamily: 'var(--font-mono)' }}>
          CMD: {lastAction.toUpperCase()} (speed: {speed})
        </div>
      )}
    </div>
  );
};
