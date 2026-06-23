# VLK Launcher — VOLKZ Clan

> Private esports SaaS launcher for the VOLKZ Clan — Roblox Rivals.

**Author:** yolezz  
**Version:** 1.0.0  
**Platform:** Windows + macOS

---

## Architecture

```
vlk-launcher/
├── client/               # PySide6 desktop app
│   ├── assets/           # Icons (icon.ico, icon.png, icon.svg)
│   ├── core/             # API + WebSocket client
│   ├── ui/               # All UI windows and panels
│   │   ├── panels/       # Home, Chat, Members, Profile, Ranking
│   │   ├── login_window.py
│   │   ├── main_window.py
│   │   ├── theme.py      # Design tokens + QSS
│   │   └── widgets.py    # Shared components
│   └── voice/            # Voice service abstraction (LiveKit/Mumble/WebRTC)
├── server/               # FastAPI backend
│   ├── core/             # DB, config, JWT auth, WS manager
│   └── routers/          # auth, licenses, admin, announcements
├── .github/workflows/    # CI/CD (build + auto-release)
├── vlk_launcher.spec     # PyInstaller packaging spec
└── .env.example          # Environment template
```

---

## Quick Start

### Server

```bash
cd vlk-launcher
pip install -r server/requirements.txt
cp .env.example .env   # edit your secrets

# Run
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Default admin license key: `VLK-ADMIN-0000`

### Client

```bash
pip install -r client/requirements.txt

# Point to your server
export VLK_SERVER_URL=http://your-server:8000

python -m client.main
```

### Build (manual)

```bash
pip install pyinstaller
pyinstaller vlk_launcher.spec
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./vlk.db` | DB connection |
| `JWT_SECRET` | — | **Change this** |
| `MASTER_PASSWORD` | — | Admin panel master password |
| `VOICE_SERVICE` | `livekit` | `livekit` / `mumble` / `webrtc` |
| `LIVEKIT_URL` | — | LiveKit server URL |
| `LIVEKIT_API_KEY` | — | LiveKit API key |
| `MUMBLE_HOST` | — | Mumble server hostname |
| `VLK_SERVER_URL` | `http://localhost:8000` | Client → server URL |

---

## Auth System

- License key → username → password registration flow
- JWT tokens (24h expiry)
- Roles: `user`, `admin`, `superadmin`
- Admin panel protected by `MASTER_PASSWORD` header
- License reassignment supported in Profile panel

---

## Voice Integration

Voice is handled by external services. Configure via `.env`:

- **LiveKit** (default): Generates a LiveKit Meet link for the VLK room
- **Mumble**: Launches local Mumble client with `mumble://` URI
- **WebRTC**: Opens configured Jitsi/custom WebRTC URL

No raw audio is processed inside the launcher.

---

## CI/CD

Push to `main` → GitHub Actions automatically:
1. Builds Windows `.exe` via PyInstaller
2. Builds macOS `.app` bundle
3. Creates a versioned GitHub Release with both archives

---

## License

Private — VOLKZ Clan internal use only.
