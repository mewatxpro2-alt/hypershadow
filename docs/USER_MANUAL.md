# ═══════════════════════════════════════════════════════════════════════════════
# BORDER SURVEILLANCE SYSTEM - USER MANUAL
# ═══════════════════════════════════════════════════════════════════════════════

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         OFFICIAL OPERATOR'S MANUAL                            ║
║                      Classification: RESTRICTED                               ║
║                                                                              ║
║  Document ID: BSS-UM-2026-001                                                ║
║  Version: 1.0.0                                                              ║
║  Effective Date: January 2026                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [System Login](#2-system-login)
3. [Dashboard Overview](#3-dashboard-overview)
4. [Live Monitoring](#4-live-monitoring)
5. [Video Analysis](#5-video-analysis)
6. [Alert Management](#6-alert-management)
7. [Map View](#7-map-view)
8. [Reports](#8-reports)
9. [System Settings](#9-system-settings)
10. [Troubleshooting](#10-troubleshooting)
11. [Emergency Procedures](#11-emergency-procedures)

---

## 1. INTRODUCTION

### 1.1 Purpose

The Border Surveillance System (BSS) is an AI-powered monitoring solution designed to:
- Detect and classify objects in drone surveillance footage
- Assess threat levels using multi-factor scoring
- Generate alerts for suspicious activity
- Maintain complete audit trails
- Support patrol coordination

### 1.2 Scope

This manual covers operational procedures for:
- System operators
- Shift supervisors
- Command center personnel

### 1.3 Security Classification

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CLASSIFICATION: RESTRICTED                                                   ║
║                                                                              ║
║  This document contains sensitive operational information.                    ║
║  Handle according to security protocols.                                      ║
║  Do not copy, distribute, or discuss with unauthorized personnel.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. SYSTEM LOGIN

### 2.1 Accessing the System

1. **Open the Application**
   - Double-click the desktop shortcut, OR
   - Run `./run.sh` (Linux/macOS) or `run.bat` (Windows)

2. **Wait for System Initialization**
   ```
   ⚠️ SYSTEM INITIALIZING...
   Loading AI models...
   Checking database integrity...
   Ready.
   ```

3. **Enter Credentials**
   - Username: Your assigned operator ID
   - Password: Your secure password

### 2.2 First-Time Login

On first login, you MUST change your password:

1. Enter default credentials provided by your supervisor
2. System will prompt for new password
3. Enter new password meeting requirements:
   - Minimum 12 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character

### 2.3 Login Failure

After **3 failed attempts**, your account will be locked for 30 minutes.

Contact your supervisor for:
- Password reset
- Account unlock
- Access issues

### 2.4 Session Timeout

```
⚠️ SECURITY NOTICE

Sessions automatically expire after 8 hours of inactivity.
Save your work before leaving the console.
Lock the terminal when stepping away: Ctrl+L
```

---

## 3. DASHBOARD OVERVIEW

### 3.1 Main Navigation

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🔒 BORDER SURVEILLANCE SYSTEM                    [USER: operator01] [LOGOUT] │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📊 Live Monitoring                                                          │
│  📹 Video Analysis                                                           │
│  🗺️ Map View                                                                 │
│  📋 Reports                                                                  │
│  ⚙️ Settings                                                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Status Bar

The status bar displays:
- Current user
- System time (UTC)
- Active alerts count
- System health indicators

### 3.3 Color Coding

| Color | Meaning |
|-------|---------|
| 🔴 Red | Critical alert / Error |
| 🟠 Orange | High priority |
| 🟡 Yellow | Medium priority |
| 🟢 Green | Normal / Clear |
| ⚪ Gray | Inactive / Disabled |

---

## 4. LIVE MONITORING

### 4.1 Starting Live Monitoring

1. Select **"📊 Live Monitoring"** from navigation
2. Upload video file OR connect to live feed
3. Configure detection settings:
   - **Confidence Threshold**: 0.5-0.9 (default: 0.7)
   - **Frame Skip**: 1-30 (default: 5)
4. Click **"▶ Start Analysis"**

### 4.2 Video Feed Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VIDEO FEED                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │     A       B       C       D       E       F                        │  │
│  │   ┌─────┬─────┬─────┬─────┬─────┬─────┐                              │  │
│  │ 1 │     │     │     │     │     │     │                              │  │
│  │   ├─────┼─────┼─────┼─────┼─────┼─────┤                              │  │
│  │ 2 │     │ [!] │     │     │     │     │  ← Detection marker          │  │
│  │   ├─────┼─────┼─────┼─────┼─────┼─────┤                              │  │
│  │ 3 │     │     │     │ [P] │     │     │  ← Person detected           │  │
│  │   ├─────┼─────┼─────┼─────┼─────┼─────┤                              │  │
│  │ 4 │     │     │     │     │     │     │                              │  │
│  │   ├─────┼─────┼─────┼─────┼─────┼─────┤                              │  │
│  │ 5 │     │     │     │     │     │     │                              │  │
│  │   └─────┴─────┴─────┴─────┴─────┴─────┘                              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  Frame: 1245/5000    FPS: 2.5    Detections: 3    Active Alerts: 1          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Detection Indicators

| Symbol | Object Type | Color |
|--------|-------------|-------|
| [P] | Person | Yellow |
| [V] | Vehicle | Blue |
| [B] | Boat | Cyan |
| [A] | Aircraft | Magenta |
| [G] | Group (3+) | Red |
| [!] | Alert | Flashing Red |

### 4.4 Real-Time Metrics

Monitor these key metrics:
- **Active Detections**: Current frame detections
- **Total Detections**: Session total
- **Alert Count**: Triggered alerts
- **Processing Rate**: Frames per second
- **Queue Status**: Pending analysis

---

## 5. VIDEO ANALYSIS

### 5.1 Uploading Video Files

1. Navigate to **"📹 Video Analysis"**
2. Click **"📁 Upload Video"**
3. Select file (supported formats: MP4, AVI, MOV, MKV)
4. Wait for upload progress to complete

### 5.2 Batch Processing

For multiple videos:

1. Upload all videos first
2. Select videos in the queue
3. Configure shared settings
4. Click **"▶ Process All"**

### 5.3 Frame-by-Frame Review

1. After processing, use navigation controls:
   - ◀◀ First frame
   - ◀ Previous frame
   - ▶ Next frame
   - ▶▶ Last frame

2. Jump to specific detections:
   - Click detection in list
   - System navigates to frame

### 5.4 Export Options

Export detection results as:
- **CSV**: For spreadsheet analysis
- **JSON**: For data integration
- **PDF Report**: For official documentation
- **Video**: With detection overlay

---

## 6. ALERT MANAGEMENT

### 6.1 Alert Panel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🚨 ACTIVE ALERTS                                             [Clear All]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔴 CRITICAL #2847                               14:32:15 UTC               │
│     Grid: C-3 | Type: Group (4 persons) | Score: 87                         │
│     [View] [Acknowledge] [Dispatch] [Dismiss]                               │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  🟠 HIGH #2846                                   14:28:43 UTC               │
│     Grid: D-2 | Type: Vehicle | Score: 65                                   │
│     [View] [Acknowledge] [Dispatch] [Dismiss]                               │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  🟡 MEDIUM #2845                                 14:15:22 UTC               │
│     Grid: B-4 | Type: Person | Score: 45                                    │
│     Status: Acknowledged by operator02                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Alert Actions

| Action | Description | Required Role |
|--------|-------------|---------------|
| **View** | Open detection details | All |
| **Acknowledge** | Mark as seen | Operator+ |
| **Dispatch** | Send patrol unit | Supervisor+ |
| **Dismiss** | Close false positive | Supervisor+ |
| **Escalate** | Increase priority | Operator+ |

### 6.3 Alert Response Procedure

**CRITICAL Alerts (Score 80+)**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CRITICAL ALERT RESPONSE PROCEDURE                                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  1. ACKNOWLEDGE alert within 30 seconds                                      ║
║  2. VERIFY detection by reviewing video frame                                ║
║  3. NOTIFY shift supervisor immediately                                      ║
║  4. DISPATCH nearest patrol unit                                             ║
║  5. DOCUMENT actions taken in alert notes                                    ║
║  6. MONITOR situation until patrol confirms                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**HIGH Alerts (Score 60-79)**

1. Acknowledge within 2 minutes
2. Review detection footage
3. Assess threat validity
4. Dispatch or dismiss as appropriate

**MEDIUM/LOW Alerts (Score <60)**

1. Review during regular monitoring
2. Log observation notes
3. Dismiss false positives

### 6.4 Patrol Dispatch

To dispatch a patrol unit:

1. Click **[Dispatch]** on alert
2. Select available unit from list:
   ```
   Available Units:
   ☐ ALPHA-1 (Distance: 2.3 km)
   ☐ BRAVO-2 (Distance: 4.1 km)
   ☐ CHARLIE-3 (Distance: 6.7 km)
   ```
3. Add response instructions
4. Confirm dispatch

---

## 7. MAP VIEW

### 7.1 Map Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🗺️ TACTICAL MAP                                              [Refresh]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Zoom +] [Zoom -] [Center] [Grid On/Off] [Legend]                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │      🔺 Border Post Alpha        🔺 Border Post Bravo                │  │
│  │            ╲                           ╱                              │  │
│  │             ╲─────────────────────────╱                               │  │
│  │              ╲    BORDER LINE        ╱                                │  │
│  │               ╲                     ╱                                 │  │
│  │    🚨 Alert    ╲                   ╱     📍 Detection                │  │
│  │    #2847        ╲                 ╱                                   │  │
│  │                  ╲               ╱                                    │  │
│  │        🚔 ALPHA-1 (En Route)                                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Legend: 🔺 Border Post  📍 Detection  🚨 Alert  🚔 Patrol  ⬡ Grid Zone    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Map Symbols

| Symbol | Description |
|--------|-------------|
| 🔺 | Border observation post |
| 📍 | Detection location |
| 🚨 | Active alert |
| 🚔 | Patrol unit |
| ⬡ | Grid zone boundary |
| 🟢 | Cleared area |
| 🔴 | Hot zone |

### 7.3 Map Controls

- **Pan**: Click and drag
- **Zoom**: Mouse wheel or +/- buttons
- **Select**: Click on marker for details
- **Filter**: Use layer toggles

### 7.4 Grid Overlay

Toggle military grid overlay:
1. Click **[Grid On/Off]**
2. Grid zones A-1 through F-5 displayed
3. Hover over zone for statistics

---

## 8. REPORTS

### 8.1 Report Types

| Report | Description | Access Level |
|--------|-------------|--------------|
| **Daily Summary** | 24-hour activity overview | All |
| **Detection Log** | All detections with details | All |
| **Alert History** | Alert timeline and responses | Operator+ |
| **Patrol Activity** | Unit movements and responses | Supervisor+ |
| **System Audit** | Login/logout, configuration changes | Admin only |

### 8.2 Generating Reports

1. Navigate to **"📋 Reports"**
2. Select report type
3. Configure parameters:
   - Date range
   - Zones (optional)
   - Threat levels (optional)
4. Click **"Generate Report"**
5. Wait for processing
6. View or download report

### 8.3 Daily Summary Report

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DAILY SURVEILLANCE SUMMARY                            ║
║                         Date: 2026-01-02                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  DETECTION STATISTICS                                                        ║
║  ────────────────────                                                        ║
║  Total Detections: 247                                                       ║
║  ├── Persons: 156 (63%)                                                     ║
║  ├── Vehicles: 52 (21%)                                                     ║
║  ├── Boats: 28 (11%)                                                        ║
║  └── Aircraft: 11 (5%)                                                      ║
║                                                                              ║
║  ALERT SUMMARY                                                               ║
║  ─────────────                                                               ║
║  Critical: 3 (2 dispatched, 1 dismissed)                                    ║
║  High: 8 (5 dispatched, 3 monitored)                                        ║
║  Medium: 15 (all monitored)                                                 ║
║  Low: 42 (all logged)                                                       ║
║                                                                              ║
║  PATROL RESPONSES                                                            ║
║  ────────────────                                                            ║
║  Total Dispatches: 7                                                         ║
║  Average Response Time: 12.4 minutes                                         ║
║  Confirmed Threats: 2                                                        ║
║  False Positives: 4                                                         ║
║                                                                              ║
║  HOT ZONES                                                                   ║
║  ─────────                                                                   ║
║  1. Grid C-3: 34 detections                                                 ║
║  2. Grid D-2: 28 detections                                                 ║
║  3. Grid B-4: 21 detections                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 8.4 Exporting Reports

Export options:
- **PDF**: Official documentation
- **CSV**: Data analysis
- **Print**: Hardcopy record

---

## 9. SYSTEM SETTINGS

### 9.1 Accessing Settings

1. Navigate to **"⚙️ Settings"**
2. Available tabs based on access level:
   - Detection (Operator+)
   - Alerts (Supervisor+)
   - Security (Admin only)
   - System (Admin only)

### 9.2 Detection Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Confidence Threshold | 0.5-0.9 | 0.7 | Minimum detection confidence |
| Frame Skip | 1-30 | 5 | Process every Nth frame |
| Night Mode | On/Off | Auto | Enhanced low-light processing |
| Object Filter | Multi | All | Filter specific object types |

### 9.3 Alert Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Critical Threshold | 60-100 | 80 | Score for critical alerts |
| High Threshold | 40-80 | 60 | Score for high alerts |
| Audio Alert | On/Off | On | Sound for critical alerts |
| Auto-Dispatch | On/Off | Off | Automatic patrol dispatch |

### 9.4 Security Settings (Admin Only)

- Session timeout duration
- Password policy settings
- Account lockout threshold
- Audit log retention
- Encryption key rotation

---

## 10. TROUBLESHOOTING

### 10.1 Common Issues

| Issue | Solution |
|-------|----------|
| Video won't upload | Check file format (MP4/AVI/MOV) |
| Detection not working | Verify model loaded in settings |
| Map not displaying | Clear browser cache |
| Session expired | Re-login with credentials |
| Slow processing | Increase frame skip value |

### 10.2 Error Messages

| Error Code | Meaning | Action |
|------------|---------|--------|
| E001 | Authentication failed | Check credentials |
| E002 | Session expired | Re-login |
| E003 | Database error | Contact admin |
| E004 | Model not found | Reinstall application |
| E005 | Invalid video format | Convert to MP4 |
| E006 | Disk space low | Clear old data |
| E007 | Processing timeout | Reduce video size |

### 10.3 Performance Tips

1. **Use Frame Skip**: Increase to 10+ for faster processing
2. **Process Night Separately**: Use night mode for thermal
3. **Clear Cache**: Regularly clear processed frame cache
4. **Single Tab**: Use only one browser tab

### 10.4 Reporting Issues

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ISSUE REPORTING PROCEDURE                                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  1. Document the issue:                                                      ║
║     - Time of occurrence                                                     ║
║     - Steps to reproduce                                                     ║
║     - Error message (if any)                                                 ║
║     - Screenshot (if possible)                                               ║
║                                                                              ║
║  2. Check system logs: Settings > System > View Logs                         ║
║                                                                              ║
║  3. Report to shift supervisor                                               ║
║                                                                              ║
║  4. DO NOT attempt unauthorized repairs                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 11. EMERGENCY PROCEDURES

### 11.1 System Failure

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         SYSTEM FAILURE PROTOCOL                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  IMMEDIATE ACTIONS:                                                          ║
║                                                                              ║
║  1. ☐ Note failure time in physical log                                     ║
║  2. ☐ Attempt system restart using run.sh/run.bat                           ║
║  3. ☐ If restart fails, notify supervisor IMMEDIATELY                       ║
║  4. ☐ Switch to manual monitoring procedures                                 ║
║  5. ☐ Contact technical support                                              ║
║                                                                              ║
║  DO NOT:                                                                     ║
║  ✗ Attempt database repairs without authorization                            ║
║  ✗ Delete any system files                                                   ║
║  ✗ Connect system to external networks                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 11.2 Security Breach

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        SECURITY BREACH PROTOCOL                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  IF YOU SUSPECT UNAUTHORIZED ACCESS:                                         ║
║                                                                              ║
║  1. ☐ DO NOT log out (preserve session evidence)                            ║
║  2. ☐ Immediately notify security officer                                    ║
║  3. ☐ Document all suspicious activity                                       ║
║  4. ☐ Do not discuss with other personnel                                    ║
║  5. ☐ Await security team instructions                                       ║
║                                                                              ║
║  SIGNS OF BREACH:                                                            ║
║  • Unfamiliar user logged in                                                 ║
║  • Unexplained configuration changes                                         ║
║  • Missing or corrupted data                                                 ║
║  • System behavior anomalies                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 11.3 Data Backup

Regular backups are automated. In emergencies:

1. Navigate to **Settings > System > Backup**
2. Click **"Emergency Backup"**
3. Save to secure external drive
4. Physically secure the backup media

### 11.4 Emergency Contacts

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          EMERGENCY CONTACTS                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Duty Officer:          [Contact Unit Commander]                             ║
║  Technical Support:     [Contact IT Department]                              ║
║  Security Officer:      [Contact Security Chief]                             ║
║  System Administrator:  [Contact System Admin]                               ║
║                                                                              ║
║  ⚠️ For classified system issues, use SECURE channels only                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## APPENDIX A: KEYBOARD SHORTCUTS

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Lock screen |
| `Ctrl+R` | Refresh view |
| `Space` | Pause/resume video |
| `←/→` | Previous/next frame |
| `A` | Acknowledge alert |
| `D` | Dispatch patrol |
| `M` | Toggle map view |
| `F11` | Fullscreen |
| `Esc` | Exit fullscreen/close modal |

---

## APPENDIX B: THREAT SCORING REFERENCE

### Scoring Formula

```
THREAT_SCORE = BASE_SCORE + TIME_FACTOR + ZONE_FACTOR + GROUP_FACTOR + CONFIDENCE_FACTOR
```

### Base Scores by Object Type

| Object | Base Score |
|--------|------------|
| Person | 10 |
| Group (3+) | 25 |
| Vehicle | 15 |
| Boat | 20 |
| Aircraft | 30 |
| Backpack | 8 |
| Animal | 3 |

### Time of Day Factors

| Time | Factor |
|------|--------|
| 00:00 - 05:59 | +15 (Night) |
| 06:00 - 17:59 | +0 (Day) |
| 18:00 - 23:59 | +10 (Evening) |

### Zone Sensitivity Factors

| Zone Rating | Factor |
|-------------|--------|
| Critical | +25 |
| High | +15 |
| Medium | +5 |
| Low | +0 |

---

## APPENDIX C: GLOSSARY

| Term | Definition |
|------|------------|
| **Alert** | System notification of potential threat |
| **BSS** | Border Surveillance System |
| **Confidence** | AI certainty of detection (0-1) |
| **Detection** | Object identified by AI system |
| **Dispatch** | Send patrol unit to location |
| **Frame Skip** | Number of frames to skip between analyses |
| **Grid Reference** | Military-style location identifier (e.g., C-3) |
| **Hot Zone** | Area with high detection activity |
| **Threat Score** | Calculated danger level (0-100) |
| **UTC** | Coordinated Universal Time |

---

## DOCUMENT CONTROL

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOCUMENT INFORMATION                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Document ID:        BSS-UM-2026-001                                         ║
║  Version:            1.0.0                                                   ║
║  Classification:     RESTRICTED                                              ║
║  Effective Date:     January 2026                                            ║
║  Review Date:        January 2027                                            ║
║                                                                              ║
║  Prepared By:        BSS Development Team                                    ║
║  Approved By:        [Approval Authority]                                    ║
║                                                                              ║
║  Distribution:       Authorized personnel only                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

**END OF DOCUMENT**

*Classification: RESTRICTED - Handle according to security protocols*
