# ═══════════════════════════════════════════════════════════════════════════════
# BORDER SURVEILLANCE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

```
 ____  ____  ____  ____  ____  ____    ____  __  __  ____  _  _  ____  __  __    __    ____  ____  ____ 
(  _ \(  _ \(  _ \(  _ \( ___)(  _ \  / ___)(  )(  )(  _ \( \/ )( ___)(  )(  )  (  )  (_  _)( ___)(  _ \
 ) _ < )   / )(_) ))   / )__)  )   /  \___ \ )(__)( )   / \  /  )__)  )(  )(    )(    _)(_  )__)  )   /
(____/(_)\_)(____/(_)\_)(____)(_)\_)  (____/(______(_)\_) (__) (____)(__)(__)  (____)(____)(____)(_)\_)
```

**Classification:** 🔴 RESTRICTED  
**Organization:** Border Security Force  
**Version:** 1.0.0  
**Last Updated:** 2026-01-02

---

## ⚠️ SECURITY NOTICE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                              CLASSIFIED SYSTEM                               ║
║                                                                              ║
║  This is a RESTRICTED military surveillance system.                          ║
║  Unauthorized access, copying, or distribution is PROHIBITED.                ║
║                                                                              ║
║  • All data remains on local machine (NO cloud services)                     ║
║  • NO internet connection required or allowed during operation               ║
║  • Air-gapped deployment REQUIRED for production use                         ║
║  • Full audit trail maintained for all actions                               ║
║  • Violations will be prosecuted under military law                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 📋 Features

| Feature | Description | Status |
|---------|-------------|--------|
| ✅ Real-time Detection | AI-powered threat detection using YOLOv8 | Active |
| ✅ Thermal Support | Process thermal and low-light footage | Active |
| ✅ Threat Scoring | Point-based threat analysis system | Active |
| ✅ Military Grid | Standard military grid reference system | Active |
| ✅ Encrypted Database | SQLite with encryption at rest | Active |
| ✅ Offline Maps | Pre-downloaded OpenStreetMap tiles | Active |
| ✅ Audit Logging | Complete action trail for accountability | Active |
| ✅ Role-Based Access | Operator, Supervisor, Admin roles | Active |
| ✅ Alert Management | Acknowledge, dispatch, track alerts | Active |

---

## 🖥️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| **Python** | 3.9+ | 3.11 |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 50 GB free | 100 GB SSD |
| **GPU** | None (CPU mode) | NVIDIA RTX 3060+ (CUDA) |
| **Network** | Not required | Not allowed |

---

## 📁 Project Structure

```
border_surveillance/
├── 📁 config/                    # System configuration
│   ├── settings.py              # Main configuration file
│   ├── security.py              # Encryption keys, access control
│   └── zones.json               # Border zone definitions
│
├── 📁 models/                    # AI Models (LOCAL ONLY)
│   ├── yolov8n.pt               # Main detection model (6.3MB)
│   ├── yolov8n_thermal.pt       # Thermal-specific model (optional)
│   └── model_loader.py          # Model initialization utilities
│
├── 📁 core/                      # Core Processing Modules
│   ├── detection.py             # YOLOv8 local inference
│   ├── threat_scoring.py        # Point-based threat analysis
│   ├── grid_system.py           # Military grid calculations
│   └── video_processor.py       # Frame extraction and processing
│
├── 📁 database/                  # Data Storage
│   ├── db_manager.py            # SQLite operations
│   ├── schema.sql               # Database structure
│   └── encryption.py            # Data encryption utilities
│
├── 📁 ui/                        # User Interface
│   ├── app.py                   # Main Streamlit dashboard
│   ├── components.py            # Reusable UI components
│   ├── auth.py                  # Authentication system
│   └── styles.py                # Military theme CSS
│
├── 📁 maps/                      # Offline Mapping
│   ├── map_generator.py         # Map creation utilities
│   ├── tile_downloader.py       # Download OSM tiles
│   ├── grid_overlay.py          # Military grid overlay
│   └── tiles/                   # Downloaded map tiles
│
├── 📁 utils/                     # Utilities
│   └── logger.py                # Logging configuration
│
├── 📁 logs/                      # Log Files
│   ├── system.log               # System events
│   ├── audit.log                # Security audit trail
│   └── detections/              # Detection records
│
├── 📁 data/                      # Data Storage
│   ├── videos/                  # Uploaded surveillance footage
│   ├── cache/                   # Processed frames cache
│   └── screenshots/             # Alert screenshots
│
├── 📁 docs/                      # Documentation
│   ├── INSTALLATION.md          # Setup instructions
│   ├── USER_MANUAL.md           # Operator guide
│   └── SECURITY.md              # Security protocols
│
├── 📁 tests/                     # Testing
│   └── test_detection.py        # Unit tests
│
├── requirements.txt             # Python dependencies
├── install.sh                   # Linux installation script
├── install.bat                  # Windows installation script
├── run.sh                       # Linux startup script
├── run.bat                      # Windows startup script
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Linux / macOS

```bash
# 1. Clone or copy project to secure location
cd /secure/location/border_surveillance

# 2. Make scripts executable
chmod +x install.sh run.sh

# 3. Run installation (one-time, may require internet)
./install.sh

# 4. Start system (offline operation)
./run.sh
```

### Windows

```cmd
REM 1. Open Command Prompt as Administrator
REM 2. Navigate to project folder
cd C:\BorderSurveillance

REM 3. Run installation (one-time)
install.bat

REM 4. Start system
run.bat
```

### Manual Start

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Start dashboard
streamlit run ui/app.py --server.port 8501 --server.address localhost
```

---

## 🔐 Default Credentials

```
╔═══════════════════════════════════════════════════════════════════╗
║  Username: admin                                                   ║
║  Password: ChangeOnFirstLogin!2026                                 ║
║                                                                    ║
║  ⚠️  CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN                ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [INSTALLATION.md](docs/INSTALLATION.md) | Detailed setup instructions |
| [USER_MANUAL.md](docs/USER_MANUAL.md) | Operator's guide |
| [SECURITY.md](docs/SECURITY.md) | Security protocols and policies |

---

## 🎯 Threat Scoring System

The system uses a point-based threat scoring algorithm:

| Score Range | Threat Level | Action Required |
|-------------|--------------|-----------------|
| 0 or below | NO THREAT | Log only |
| 1 - 5 | LOW (GREEN) | Monitor |
| 6 - 10 | MEDIUM (YELLOW) | Alert supervisor |
| 11+ | CRITICAL (RED) | Immediate response |

### Scoring Factors

| Factor | Points | Description |
|--------|--------|-------------|
| Object Type | +1 to +3 | Person=1, Vehicle=2, Truck=3 |
| Time of Day | -1 to +3 | Day=-1, Evening=+1, Night=+3 |
| Zone Location | +0 to +5 | Based on sensitivity |
| Group Size | +0 to +4 | Multiple persons detected |
| Movement Pattern | +0 to +3 | Suspicious behavior |
| Confidence Level | -1 to +1 | AI detection confidence |

---

## 🗺️ Military Grid System

The video frame is divided into a 6x5 grid:

```
    A       B       C       D       E       F
  ┌───────┬───────┬───────┬───────┬───────┬───────┐
1 │ A-1   │ B-1   │ C-1   │ D-1   │ E-1   │ F-1   │  ← Pakistan Side
  ├───────┼───────┼───────┼───────┼───────┼───────┤
2 │ A-2   │ B-2   │ C-2   │ D-2   │ E-2   │ F-2   │
  ├───────┼───────┼───────┼───────┼───────┼───────┤
3 │ A-3   │ B-3   │ C-3   │ D-3   │ E-3   │ F-3   │  ← Border Line
  ├───────┼───────┼───────┼───────┼───────┼───────┤
4 │ A-4   │ B-4   │ C-4   │ D-4   │ E-4   │ F-4   │
  ├───────┼───────┼───────┼───────┼───────┼───────┤
5 │ A-5   │ B-5   │ C-5   │ D-5   │ E-5   │ F-5   │  ← India Side
  └───────┴───────┴───────┴───────┴───────┴───────┘
```

---

## 🔒 Security Features

1. **Data Encryption** - All database contents encrypted at rest
2. **Authentication** - Username/password with bcrypt hashing
3. **Session Timeout** - Auto-logout after 30 minutes of inactivity
4. **Audit Logging** - Every action recorded with timestamp and user
5. **Role-Based Access** - Operator, Supervisor, Admin privilege levels
6. **Offline Operation** - No external network connections
7. **Secure Deletion** - Proper data wiping procedures

---

## 📞 Support

```
╔═══════════════════════════════════════════════════════════════════╗
║  For classified support, contact authorized personnel only:        ║
║                                                                    ║
║  Email: [REDACTED - Contact Unit Commander]                        ║
║  Phone: [REDACTED - Contact Unit Commander]                        ║
║  Emergency: [REDACTED - Contact Duty Officer]                      ║
║                                                                    ║
║  ⚠️  DO NOT post issues publicly or seek help on public forums    ║
║  ⚠️  DO NOT share system details with unauthorized personnel       ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 📜 Legal Notice

This software is the property of Border Security Force. Unauthorized copying,
distribution, modification, or use is strictly prohibited and may result in
severe civil and criminal penalties.

**Classification:** RESTRICTED  
**Distribution:** Authorized personnel only

---

*Last Updated: 2026-01-02 | Version 1.0.0*
