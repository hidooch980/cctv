import React, { useEffect, useRef } from 'react';
import type { Camera, Language } from '../types';
import { getTranslation } from '../i18n';

interface CameraCellProps {
  camera: Camera;
  isSelected: boolean;
  onSelect: (cam: Camera) => void;
  onOpenDiagnose: (code: string) => void;
  lang: Language;
}

export const CameraCell: React.FC<CameraCellProps> = ({
  camera,
  isSelected,
  onSelect,
  onOpenDiagnose,
  lang,
}) => {
  const t = getTranslation(lang);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || camera.status === 'offline') return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let frameCount = 0;

    const render = () => {
      frameCount++;
      const width = canvas.width;
      const height = canvas.height;

      // Draw background CCTV scene (subtle gradient night/indoor surveillance look)
      const grad = ctx.createLinearGradient(0, 0, width, height);
      grad.addColorStop(0, '#0f172a');
      grad.addColorStop(0.5, '#1e293b');
      grad.addColorStop(1, '#0b1120');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // Draw subtle grid / scanning lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      for (let y = 0; y < height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Draw perspective hallway or perimeter outline
      ctx.strokeStyle = 'rgba(100, 116, 139, 0.25)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(width * 0.1, height * 0.9);
      ctx.lineTo(width * 0.4, height * 0.45);
      ctx.lineTo(width * 0.6, height * 0.45);
      ctx.lineTo(width * 0.9, height * 0.9);
      ctx.stroke();

      // Simulated AI Detection bounding box animation
      if (camera.ai_enabled) {
        const tOffset = (Math.sin(frameCount * 0.03) + 1) * 0.5;
        const boxX = width * 0.35 + tOffset * (width * 0.2);
        const boxY = height * 0.35;
        const boxW = width * 0.18;
        const boxH = height * 0.45;

        // Bounding box
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.strokeRect(boxX, boxY, boxW, boxH);

        // Label tag
        ctx.fillStyle = '#10b981';
        ctx.fillRect(boxX, boxY - 18, 90, 18);
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 10px monospace';
        ctx.fillText('PERSON 95%', boxX + 6, boxY - 5);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [camera.status, camera.ai_enabled]);

  // Format dynamic clock
  const now = new Date();
  const timeStr = now.toISOString().replace('T', ' ').substring(0, 19);

  return (
    <div
      className={`camera-cell ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(camera)}
    >
      {/* Top Header Overlay */}
      <div className="cell-header-overlay">
        <div className="cell-title-chip">
          <span
            className={`status-indicator-dot ${
              camera.status === 'online'
                ? 'status-dot-online'
                : camera.status === 'error'
                ? 'status-dot-warning'
                : 'status-dot-offline'
            }`}
          />
          <span>{camera.name}</span>
          <span style={{ opacity: 0.6 }}>|</span>
          <span style={{ fontSize: '10px', color: '#94a3b8' }}>{camera.vendor}</span>
        </div>

        <div className="cell-stream-meta">
          {camera.resolution} @ {camera.fps}fps {camera.bitrate_kbps}kbps
        </div>
      </div>

      {/* Video Content */}
      {camera.status === 'offline' ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            background: '#090d14',
          }}
        >
          <span style={{ fontSize: '20px', marginBottom: '4px' }}>⚡</span>
          <span style={{ fontSize: '12px' }}>{t.offline}</span>
        </div>
      ) : (
        <canvas
          ref={canvasRef}
          width={640}
          height={360}
          className="canvas-stream-feed"
        />
      )}

      {/* Timestamp */}
      <div className="cell-timestamp">{timeStr}</div>

      {/* Hover Action Bar */}
      <div className="cell-toolbar">
        <button
          className="cell-tool-btn"
          title="Snapshot"
          onClick={(e) => {
            e.stopPropagation();
            alert(`Snapshot saved for ${camera.name} at ${timeStr}`);
          }}
        >
          📷
        </button>
        {camera.ptz_supported && (
          <button
            className="cell-tool-btn"
            title="PTZ Active"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(camera);
            }}
          >
            🎮 PTZ
          </button>
        )}
        <button
          className="cell-tool-btn"
          title="Diagnose OpenSDK Stream"
          onClick={(e) => {
            e.stopPropagation();
            onOpenDiagnose(camera.last_error_code || 'STATE_RTSP_PLAY_READY');
          }}
        >
          🩺
        </button>
      </div>
    </div>
  );
};
