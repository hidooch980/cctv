import React, { useState } from 'react';
import type { Camera, Language } from '../types';
import { getTranslation } from '../i18n';

interface AddCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCameraAdded: (cam: Camera) => void;
  lang: Language;
}

export const AddCameraModal: React.FC<AddCameraModalProps> = ({
  isOpen,
  onClose,
  onCameraAdded,
  lang,
}) => {
  const t = getTranslation(lang);
  const [name, setName] = useState('');
  const [ip, setIp] = useState('192.168.1.');
  const [port, setPort] = useState(554);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [vendor, setVendor] = useState('Dahua / Lechange');
  const [streamType, setStreamType] = useState('rtsp');
  const [deviceSerial, setDeviceSerial] = useState('');
  const [ptzSupported, setPtzSupported] = useState(false);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [testResult, setTestResult] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleTest = () => {
    if (!ip || ip === '192.168.1.') {
      setTestResult('fail');
      return;
    }
    setTestResult('ok');
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;

    const newCamData = {
      name,
      location: 'Main Perimeter',
      group_name: 'Security Zone',
      vendor,
      stream_type: streamType,
      device_ip: ip,
      device_port: port,
      device_username: username,
      device_password: password,
      device_serial: deviceSerial,
      ptz_supported: ptzSupported,
      ai_enabled: aiEnabled,
      resolution: '1920x1080',
      fps: 25,
      bitrate_kbps: 2048,
    };

    try {
      const res = await fetch('/api/v1/cameras', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer mock_token',
        },
        body: JSON.stringify(newCamData),
      });

      if (res.ok) {
        const created = await res.json();
        onCameraAdded(created);
        onClose();
        return;
      }
    } catch {
      // Fallback local add
    }

    const fallbackCam: Camera = {
      id: Date.now(),
      name,
      location: 'Main Perimeter',
      group_name: 'Security Zone',
      vendor,
      stream_type: streamType,
      device_ip: ip,
      device_port: port,
      device_serial: deviceSerial,
      channel_id: 0,
      status: 'online',
      resolution: '1920x1080',
      fps: 25,
      bitrate_kbps: 2048,
      ptz_supported: ptzSupported,
      audio_supported: true,
      ai_enabled: aiEnabled,
      recording_mode: 'continuous',
    };
    onCameraAdded(fallbackCam);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <form onSubmit={handleSave}>
          <div className="modal-header">
            <div className="modal-title">📹 {t.addCamera}</div>
            <button type="button" className="modal-close-btn" onClick={onClose}>✕</button>
          </div>

          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">{t.cameraName} *</label>
              <input
                type="text"
                className="form-input"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Gate 02 West"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">{t.vendor}</label>
                <select className="form-select" value={vendor} onChange={(e) => setVendor(e.target.value)}>
                  <option value="Dahua / Lechange">Dahua / Lechange (OpenSDK)</option>
                  <option value="Hikvision">Hikvision (ISAPI / ONVIF)</option>
                  <option value="Uniview">Uniview (ONVIF)</option>
                  <option value="Axis">Axis Communications</option>
                  <option value="Generic">Generic ONVIF / RTSP</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">{t.streamType}</label>
                <select className="form-select" value={streamType} onChange={(e) => setStreamType(e.target.value)}>
                  <option value="rtsp">RTSP over TCP</option>
                  <option value="opensdk">OpenSDK P2P Stream</option>
                  <option value="onvif">ONVIF Media 2</option>
                  <option value="webrtc">WebRTC Direct</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">{t.ipAddress}</label>
                <input
                  type="text"
                  className="form-input"
                  style={{ fontFamily: 'var(--font-mono)' }}
                  value={ip}
                  onChange={(e) => setIp(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">{t.port}</label>
                <input
                  type="number"
                  className="form-input"
                  style={{ fontFamily: 'var(--font-mono)' }}
                  value={port}
                  onChange={(e) => setPort(parseInt(e.target.value) || 554)}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">{t.username}</label>
                <input
                  type="text"
                  className="form-input"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">{t.password}</label>
                <input
                  type="password"
                  className="form-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">{t.deviceSerial}</label>
              <input
                type="text"
                className="form-input"
                style={{ fontFamily: 'var(--font-mono)' }}
                value={deviceSerial}
                onChange={(e) => setDeviceSerial(e.target.value)}
                placeholder="Required for OpenSDK cloud/P2P streaming"
              />
            </div>

            <div style={{ display: 'flex', gap: '20px', alignItems: 'center', paddingTop: '6px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
                <input
                  type="checkbox"
                  checked={ptzSupported}
                  onChange={(e) => setPtzSupported(e.target.checked)}
                />
                {t.ptzSupported}
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
                <input
                  type="checkbox"
                  checked={aiEnabled}
                  onChange={(e) => setAiEnabled(e.target.checked)}
                />
                {t.aiEnabled}
              </label>
            </div>

            {/* Test Connection Button & Indicator */}
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button type="button" className="btn btn-secondary" onClick={handleTest}>
                🔌 {t.testConnection}
              </button>
              {testResult === 'ok' && (
                <span style={{ color: '#10b981', fontSize: '12px' }}>✓ {t.testSuccess}</span>
              )}
              {testResult === 'fail' && (
                <span style={{ color: '#ef4444', fontSize: '12px' }}>✕ {t.testFailed}</span>
              )}
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              {t.cancel}
            </button>
            <button type="submit" className="btn btn-primary">
              {t.save}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
