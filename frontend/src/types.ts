export type Language = 'en' | 'fa';

export interface Camera {
  id: number;
  name: string;
  location: string;
  group_name: string;
  vendor: string;
  stream_type: string;
  rtsp_url?: string;
  device_ip?: string;
  device_port?: number;
  device_serial?: string;
  channel_id: number;
  status: 'online' | 'offline' | 'error' | 'connecting';
  resolution: string;
  fps: number;
  bitrate_kbps: number;
  ptz_supported: boolean;
  audio_supported: boolean;
  ai_enabled: boolean;
  recording_mode: string;
  last_error_code?: string;
  last_error_message?: string;
}

export interface SecurityEvent {
  id: number;
  camera_id: number;
  event_type: 'person' | 'vehicle' | 'motion' | 'line_crossing' | 'tampering' | 'sdk_error';
  severity: 'info' | 'warning' | 'alert' | 'critical';
  confidence: number;
  title: string;
  description?: string;
  metadata_json?: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  created_at: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  uptime_seconds: number;
  capacity: {
    max_cameras: number;
    active_cameras: number;
    offline_cameras: number;
    error_cameras: number;
    utilization_percentage: number;
  };
  storage: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    usage_percentage: number;
    retention_days: number;
  };
  network: {
    total_inbound_mbps: number;
    total_outbound_mbps: number;
    active_sessions: number;
  };
  supported_vendors: string[];
  ai_engine_status: string;
}

export interface OpenSDKErrorDiagnosis {
  code: string;
  numeric_code?: number;
  category: string;
  name: string;
  description_en: string;
  description_fa: string;
  probable_cause_en: string;
  probable_cause_fa: string;
  recommended_action_en: string;
  recommended_action_fa: string;
  recovery_strategy: string;
}

export interface DiscoveredDevice {
  ip: string;
  port: number;
  manufacturer: string;
  model: string;
  mac_address?: string;
  supports_ptz: boolean;
}
