import { useState, useEffect } from 'react';
import type { Camera, SecurityEvent, SystemHealth, Language } from './types';
import { getTranslation } from './i18n';
import { TopNav } from './components/TopNav';
import { CameraCell } from './components/CameraCell';
import { PTZWidget } from './components/PTZWidget';
import { EventFeed } from './components/EventFeed';
import { OpenSDKModal } from './components/OpenSDKModal';
import { AddCameraModal } from './components/AddCameraModal';

const INITIAL_CAMERAS: Camera[] = [
  {
    id: 1,
    name: 'Main Gate - Entrance 01',
    location: 'Perimeter North',
    group_name: 'Entrance',
    vendor: 'Dahua / Lechange',
    stream_type: 'rtsp',
    rtsp_url: 'rtsp://admin:Demo1234@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0',
    device_ip: '192.168.1.101',
    device_port: 554,
    device_serial: 'DH4K9921008123',
    channel_id: 0,
    status: 'online',
    resolution: '1920x1080',
    fps: 25,
    bitrate_kbps: 2500,
    ptz_supported: false,
    audio_supported: true,
    ai_enabled: true,
    recording_mode: 'continuous',
  },
  {
    id: 2,
    name: 'Lobby & Reception',
    location: 'Building A Ground Floor',
    group_name: 'Indoor',
    vendor: 'Hikvision',
    stream_type: 'rtsp',
    rtsp_url: 'rtsp://admin:Demo1234@192.168.1.102:554/Streaming/Channels/101',
    device_ip: '192.168.1.102',
    device_port: 554,
    channel_id: 0,
    status: 'online',
    resolution: '2560x1440',
    fps: 30,
    bitrate_kbps: 3500,
    ptz_supported: false,
    audio_supported: false,
    ai_enabled: true,
    recording_mode: 'motion',
  },
  {
    id: 3,
    name: 'Parking Lot West PTZ',
    location: 'Outdoor West Lot',
    group_name: 'Perimeter',
    vendor: 'Dahua PTZ',
    stream_type: 'rtsp',
    rtsp_url: 'rtsp://admin:Demo1234@192.168.1.105:554/cam/realmonitor?channel=1&subtype=0',
    device_ip: '192.168.1.105',
    device_port: 554,
    channel_id: 0,
    status: 'online',
    resolution: '1920x1080',
    fps: 30,
    bitrate_kbps: 3000,
    ptz_supported: true,
    audio_supported: true,
    ai_enabled: true,
    recording_mode: 'continuous',
  },
  {
    id: 4,
    name: 'Server Room Access',
    location: 'Secure Zone Basement',
    group_name: 'Critical',
    vendor: 'Uniview',
    stream_type: 'rtsp',
    rtsp_url: 'rtsp://admin:Demo1234@192.168.1.103:554/unicast/c1/s0/live',
    device_ip: '192.168.1.103',
    device_port: 554,
    channel_id: 0,
    status: 'online',
    resolution: '1920x1080',
    fps: 25,
    bitrate_kbps: 2000,
    ptz_supported: false,
    audio_supported: true,
    ai_enabled: true,
    recording_mode: 'motion',
  },
];

const INITIAL_EVENTS: SecurityEvent[] = [
  {
    id: 1,
    camera_id: 1,
    event_type: 'vehicle',
    severity: 'info',
    confidence: 0.96,
    title: 'Vehicle Detected at Entrance',
    description: 'White sedan entered license detection zone.',
    acknowledged: false,
    created_at: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
  },
  {
    id: 2,
    camera_id: 2,
    event_type: 'person',
    severity: 'info',
    confidence: 0.94,
    title: 'Person Detected in Lobby',
    description: 'Pedestrian entered main reception foyer.',
    acknowledged: false,
    created_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
  },
  {
    id: 3,
    camera_id: 4,
    event_type: 'line_crossing',
    severity: 'warning',
    confidence: 0.98,
    title: 'Tripwire Crossed - Server Room',
    description: 'Virtual tripwire crossed outside scheduled maintenance hours.',
    acknowledged: true,
    acknowledged_by: 'admin',
    created_at: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
  },
];

export function App() {
  const [lang, setLang] = useState<Language>('fa');
  const t = getTranslation(lang);

  const [cameras, setCameras] = useState<Camera[]>(INITIAL_CAMERAS);
  const [events, setEvents] = useState<SecurityEvent[]>(INITIAL_EVENTS);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(INITIAL_CAMERAS[2]); // Default to PTZ camera
  const [gridMode, setGridMode] = useState<1 | 4 | 9 | 16>(4);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [rightTab, setRightTab] = useState<'events' | 'ptz'>('events');

  // Modals
  const [isDiagnoseOpen, setIsDiagnoseOpen] = useState<boolean>(false);
  const [initialDiagnoseCode, setInitialDiagnoseCode] = useState<string>('503');
  const [isAddCameraOpen, setIsAddCameraOpen] = useState<boolean>(false);

  // Sync RTL / LTR document direction with language
  useEffect(() => {
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
  }, [lang]);

  // Fetch from backend API
  useEffect(() => {
    const loadBackendData = async () => {
      try {
        const camRes = await fetch('/api/v1/cameras');
        if (camRes.ok) {
          const camData = await camRes.json();
          if (Array.isArray(camData) && camData.length > 0) {
            setCameras(camData);
          }
        }
      } catch {
        // Use local fallback
      }

      try {
        const evRes = await fetch('/api/v1/events');
        if (evRes.ok) {
          const evData = await evRes.json();
          if (Array.isArray(evData) && evData.length > 0) {
            setEvents(evData);
          }
        }
      } catch {
        // Use local fallback
      }

      try {
        const sysRes = await fetch('/api/v1/system/health');
        if (sysRes.ok) {
          const sysData = await sysRes.json();
          setSystemHealth(sysData);
        }
      } catch {
        // Use local fallback
      }
    };

    loadBackendData();
  }, []);

  const toggleLanguage = () => {
    setLang((prev) => (prev === 'en' ? 'fa' : 'en'));
  };

  const handleOpenDiagnose = (code: string) => {
    setInitialDiagnoseCode(code);
    setIsDiagnoseOpen(true);
  };

  const handleAcknowledgeEvent = async (id: number) => {
    setEvents((prev) =>
      prev.map((ev) =>
        ev.id === id ? { ...ev, acknowledged: true, acknowledged_by: 'admin' } : ev
      )
    );
    try {
      await fetch(`/api/v1/events/${id}/acknowledge`, {
        method: 'POST',
        headers: { Authorization: 'Bearer mock_token' },
      });
    } catch {
      // Offline fallback
    }
  };

  const handleCameraAdded = (newCam: Camera) => {
    setCameras((prev) => [newCam, ...prev]);
    setSelectedCamera(newCam);
  };

  // Filter cameras
  const filteredCameras = cameras.filter(
    (c) =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.vendor.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Sliced cameras to show in current grid mode
  const displayedCameras =
    gridMode === 1
      ? selectedCamera
        ? [selectedCamera]
        : filteredCameras.slice(0, 1)
      : filteredCameras.slice(0, gridMode);

  return (
    <div className="app-container">
      {/* Top Header Navigation */}
      <TopNav
        systemHealth={systemHealth}
        gridMode={gridMode}
        onGridModeChange={setGridMode}
        lang={lang}
        onToggleLang={toggleLanguage}
        onOpenAddModal={() => setIsAddCameraOpen(true)}
        onOpenDiagnoseModal={() => handleOpenDiagnose('503')}
      />

      <div className="main-viewport">
        {/* Left Sidebar: Camera Tree & Filter */}
        <aside className="sidebar-left">
          <div className="sidebar-header">
            <span className="sidebar-title">{t.cameras}</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              {cameras.length} / 100
            </span>
          </div>

          <div className="camera-search-bar">
            <input
              type="text"
              className="search-input"
              placeholder={t.searchPlaceholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="camera-tree-list">
            {filteredCameras.map((cam) => (
              <div
                key={cam.id}
                className={`camera-tree-item ${
                  selectedCamera?.id === cam.id ? 'selected' : ''
                }`}
                onClick={() => {
                  setSelectedCamera(cam);
                  if (cam.ptz_supported) {
                    setRightTab('ptz');
                  }
                }}
              >
                <div className="camera-item-main">
                  <span
                    className={`status-indicator-dot ${
                      cam.status === 'online'
                        ? 'status-dot-online'
                        : cam.status === 'error'
                        ? 'status-dot-warning'
                        : 'status-dot-offline'
                    }`}
                  />
                  <div>
                    <div className="camera-item-name">{cam.name}</div>
                    <div className="camera-item-vendor">
                      {cam.vendor} • {cam.device_ip || 'P2P'}
                    </div>
                  </div>
                </div>

                {cam.ptz_supported && (
                  <span style={{ fontSize: '10px', color: '#60a5fa', fontWeight: 600 }}>
                    PTZ
                  </span>
                )}
              </div>
            ))}
          </div>
        </aside>

        {/* Center: Live Surveillance Matrix Grid */}
        <main className={`video-grid-container grid-${gridMode}`}>
          {displayedCameras.map((cam) => (
            <CameraCell
              key={cam.id}
              camera={cam}
              isSelected={selectedCamera?.id === cam.id}
              onSelect={(c) => {
                setSelectedCamera(c);
                if (c.ptz_supported) {
                  setRightTab('ptz');
                }
              }}
              onOpenDiagnose={handleOpenDiagnose}
              lang={lang}
            />
          ))}
        </main>

        {/* Right Sidebar: Security AI Events & PTZ Control */}
        <aside className="sidebar-right">
          <div className="tab-nav-panel">
            <button
              className={`tab-nav-btn ${rightTab === 'events' ? 'active' : ''}`}
              onClick={() => setRightTab('events')}
            >
              🔔 {t.events} ({events.length})
            </button>
            <button
              className={`tab-nav-btn ${rightTab === 'ptz' ? 'active' : ''}`}
              onClick={() => setRightTab('ptz')}
            >
              🎮 PTZ
            </button>
          </div>

          {rightTab === 'events' ? (
            <EventFeed
              events={events}
              onAcknowledge={handleAcknowledgeEvent}
              lang={lang}
            />
          ) : (
            <div style={{ padding: '12px' }}>
              <PTZWidget camera={selectedCamera} lang={lang} />
            </div>
          )}
        </aside>
      </div>

      {/* OpenSDK Diagnostic & Error Resolver Modal */}
      <OpenSDKModal
        initialCode={initialDiagnoseCode}
        isOpen={isDiagnoseOpen}
        onClose={() => setIsDiagnoseOpen(false)}
        lang={lang}
      />

      {/* Add Camera Modal */}
      <AddCameraModal
        isOpen={isAddCameraOpen}
        onClose={() => setIsAddCameraOpen(false)}
        onCameraAdded={handleCameraAdded}
        lang={lang}
      />
    </div>
  );
}

export default App;
