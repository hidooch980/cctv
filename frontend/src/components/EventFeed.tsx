import React from 'react';
import type { SecurityEvent, Language } from '../types';
import { getTranslation } from '../i18n';

interface EventFeedProps {
  events: SecurityEvent[];
  onAcknowledge: (id: number) => void;
  lang: Language;
}

export const EventFeed: React.FC<EventFeedProps> = ({ events, onAcknowledge, lang }) => {
  const t = getTranslation(lang);

  const getBadgeClass = (type: string) => {
    switch (type) {
      case 'person':
        return 'event-badge-person';
      case 'vehicle':
        return 'event-badge-vehicle';
      case 'line_crossing':
      case 'tampering':
        return 'event-badge-warning';
      case 'sdk_error':
        return 'event-badge-error';
      default:
        return 'event-badge-person';
    }
  };

  return (
    <div className="panel-content-scroll">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {t.recentEvents} ({events.length})
        </span>
      </div>

      {events.length === 0 ? (
        <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
          {t.noEvents}
        </div>
      ) : (
        events.map((ev) => (
          <div key={ev.id} className="event-card">
            <div className="event-card-header">
              <span className={`event-type-badge ${getBadgeClass(ev.event_type)}`}>
                {ev.event_type.replace('_', ' ')}
              </span>
              <span className="event-time">
                {new Date(ev.created_at).toLocaleTimeString()}
              </span>
            </div>

            <div className="event-title">{ev.title}</div>
            {ev.description && <div className="event-desc">{ev.description}</div>}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                CONF: {Math.round(ev.confidence * 100)}%
              </span>

              {ev.acknowledged ? (
                <span style={{ fontSize: '11px', color: 'var(--status-online)', fontWeight: 500 }}>
                  ✓ {t.acknowledged}
                </span>
              ) : (
                <button
                  className="btn btn-secondary"
                  style={{ padding: '2px 8px', fontSize: '11px' }}
                  onClick={() => onAcknowledge(ev.id)}
                >
                  {t.acknowledge}
                </button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
};
