# Portability & Deployment Guide

`traffic-stats-kit` runs across operating systems with no cloud or GPU dependencies.

---

## 1. Operating System Matrix

| OS | Runtime | System Dependencies | Installation Script |
|---|---|---|---|
| **macOS (Apple Silicon & Intel)** | Python 3.10–3.12 | `brew install ffmpeg` | `pip install -e .` |
| **Ubuntu / Debian Linux** | Python 3.10–3.12 | `sudo apt-get install ffmpeg` | `pip install -e .` |
| **Windows 10 / 11** | Python 3.10–3.12 | Bundled `ffmpeg.exe` | `setup_windows.bat` |
| **Embedded Linux / Raspberry Pi 5** | Python 3.11 | `apt install ffmpeg` | `pip install -e .` |

---

## 2. Windows Standalone Package

For field engineers without terminal or development environments:
* Double-click `setup_windows.bat` to automatically verify Python, install isolated dependencies in `.venv`, and download portable `ffmpeg`.
* Double-click `start_agent_windows.bat` to launch the interactive terminal or local browser visualizer.
