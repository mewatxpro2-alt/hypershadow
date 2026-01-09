-- ═══════════════════════════════════════════════════════════════════════════════
-- BORDER SURVEILLANCE SYSTEM - DATABASE SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════════
-- Classification: RESTRICTED
-- Organization: Border Security Force
-- Module: database/schema.sql
-- Last Updated: 2026-01-02
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- PURPOSE:
--     Defines the complete database schema for the surveillance system.
--     All data is stored in encrypted SQLite database.
--
-- SECURITY NOTES:
--     - Database file should be encrypted at rest
--     - Regular backups required
--     - Audit table should never be truncated
--     - Delete operations should be soft-deletes where possible
--
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: users
-- Stores user accounts for authentication
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',
    email TEXT,
    active INTEGER DEFAULT 1,
    force_password_change INTEGER DEFAULT 1,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    CHECK (role IN ('admin', 'supervisor', 'operator', 'readonly'))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: sessions
-- Tracks active user sessions
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    active INTEGER DEFAULT 1,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: detections
-- Stores all object detections from video processing
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    frame_number INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    class_name TEXT NOT NULL,
    class_id INTEGER,
    confidence REAL NOT NULL,
    bbox_x1 INTEGER NOT NULL,
    bbox_y1 INTEGER NOT NULL,
    bbox_x2 INTEGER NOT NULL,
    bbox_y2 INTEGER NOT NULL,
    center_x INTEGER NOT NULL,
    center_y INTEGER NOT NULL,
    grid_reference TEXT NOT NULL,
    threat_score INTEGER DEFAULT 0,
    threat_level TEXT DEFAULT 'NO_THREAT',
    processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (threat_level IN ('CRITICAL', 'MEDIUM', 'LOW', 'NO_THREAT'))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: alerts
-- Stores generated alerts from high-threat detections
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id INTEGER,
    alert_type TEXT NOT NULL,
    threat_level TEXT NOT NULL,
    threat_score INTEGER NOT NULL,
    grid_reference TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_count INTEGER DEFAULT 1,
    description TEXT,
    screenshot_path TEXT,
    status TEXT DEFAULT 'active',
    acknowledged_at TIMESTAMP,
    acknowledged_by INTEGER,
    dispatched_at TIMESTAMP,
    dispatched_by INTEGER,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    resolution_notes TEXT,
    false_alarm INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (detection_id) REFERENCES detections(id),
    FOREIGN KEY (acknowledged_by) REFERENCES users(id),
    FOREIGN KEY (dispatched_by) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    CHECK (threat_level IN ('CRITICAL', 'MEDIUM', 'LOW')),
    CHECK (status IN ('active', 'acknowledged', 'dispatched', 'resolved', 'archived'))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: patrol_dispatches
-- Records of patrol unit dispatches to alert locations
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patrol_dispatches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    patrol_unit_id TEXT NOT NULL,
    patrol_unit_name TEXT NOT NULL,
    target_grid TEXT NOT NULL,
    estimated_eta_minutes INTEGER,
    actual_arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    status TEXT DEFAULT 'dispatched',
    outcome TEXT,
    personnel_count INTEGER,
    notes TEXT,
    dispatched_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (alert_id) REFERENCES alerts(id),
    FOREIGN KEY (dispatched_by) REFERENCES users(id),
    CHECK (status IN ('dispatched', 'en_route', 'arrived', 'completed', 'cancelled'))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: videos
-- Metadata for uploaded surveillance videos
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    original_filename TEXT,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    duration_seconds REAL,
    width INTEGER,
    height INTEGER,
    fps REAL,
    total_frames INTEGER,
    codec TEXT,
    processed INTEGER DEFAULT 0,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    total_detections INTEGER DEFAULT 0,
    total_alerts INTEGER DEFAULT 0,
    thumbnail_path TEXT,
    uploaded_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: audit_log
-- CRITICAL: Complete audit trail of all system actions
-- This table should NEVER be truncated or have rows deleted
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    session_id TEXT,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: system_settings
-- Stores configurable system settings
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: password_history
-- Tracks password history to prevent reuse
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: statistics_daily
-- Aggregated daily statistics for reporting
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS statistics_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    total_detections INTEGER DEFAULT 0,
    total_alerts INTEGER DEFAULT 0,
    critical_alerts INTEGER DEFAULT 0,
    medium_alerts INTEGER DEFAULT 0,
    low_alerts INTEGER DEFAULT 0,
    false_alarms INTEGER DEFAULT 0,
    average_response_time_minutes REAL,
    videos_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- INDEXES FOR PERFORMANCE
-- ═══════════════════════════════════════════════════════════════════════════════

-- User lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Session lookups
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Detection queries
CREATE INDEX IF NOT EXISTS idx_detections_video_id ON detections(video_id);
CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_detections_grid_reference ON detections(grid_reference);
CREATE INDEX IF NOT EXISTS idx_detections_threat_level ON detections(threat_level);

-- Alert queries
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_threat_level ON alerts(threat_level);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_grid_reference ON alerts(grid_reference);

-- Audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Video queries
CREATE INDEX IF NOT EXISTS idx_videos_processed ON videos(processed);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Update timestamp on user modification
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamp on alert modification
CREATE TRIGGER IF NOT EXISTS update_alerts_timestamp 
AFTER UPDATE ON alerts
BEGIN
    UPDATE alerts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamp on patrol dispatch modification
CREATE TRIGGER IF NOT EXISTS update_patrol_dispatches_timestamp 
AFTER UPDATE ON patrol_dispatches
BEGIN
    UPDATE patrol_dispatches SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ═══════════════════════════════════════════════════════════════════════════════
-- VIEWS FOR COMMON QUERIES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Active alerts view
CREATE VIEW IF NOT EXISTS v_active_alerts AS
SELECT 
    a.id,
    a.alert_type,
    a.threat_level,
    a.threat_score,
    a.grid_reference,
    a.object_type,
    a.object_count,
    a.description,
    a.status,
    a.created_at,
    a.screenshot_path,
    d.class_name,
    d.confidence,
    d.frame_number
FROM alerts a
LEFT JOIN detections d ON a.detection_id = d.id
WHERE a.status IN ('active', 'acknowledged', 'dispatched')
ORDER BY 
    CASE a.threat_level 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'MEDIUM' THEN 2 
        WHEN 'LOW' THEN 3 
    END,
    a.created_at DESC;

-- Today's statistics view
CREATE VIEW IF NOT EXISTS v_today_statistics AS
SELECT 
    COUNT(*) as total_detections,
    SUM(CASE WHEN threat_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
    SUM(CASE WHEN threat_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
    SUM(CASE WHEN threat_level = 'LOW' THEN 1 ELSE 0 END) as low_count,
    AVG(threat_score) as avg_threat_score
FROM detections
WHERE DATE(created_at) = DATE('now');

-- ═══════════════════════════════════════════════════════════════════════════════
-- END OF SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════════
