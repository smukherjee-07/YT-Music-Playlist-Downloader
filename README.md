<div align="center">

# 🎵 YT Music Downloader

**A fast, simple command-line tool for downloading tracks and playlists from YouTube & YouTube Music as MP3 files.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![yt-dlp](https://img.shields.io/badge/powered%20by-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

</div>

---

## 📖 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Install Python Dependencies](#2-install-python-dependencies)
  - [3. Install FFmpeg](#-installing-ffmpeg)
  - [4. Install yt-dlp](#-installing-yt-dlp)
- [Usage](#-usage)
- [Download Organization](#-download-organization)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Updating Dependencies](#-updating-dependencies)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## ✨ Features

- 🎧 Download single tracks or entire playlists as high-quality MP3
- 📁 Automatic, clean folder organization (playlists get their own subfolder)
- 🔢 Preserves original playlist track ordering
- 🖼️ Embeds metadata and thumbnails into downloaded files
- 💾 Remembers your last download location between sessions
- 🖥️ Simple, interactive command-line menu — no complex flags to remember
- 🌍 Cross-platform: Windows, Linux, and macOS
- 🔃 Playlist tracks can be downloaded concurrently using 3 or 4 download workers, reducing the total download time while preserving the original playlist order in the filenames.
---

## 📋 Requirements

| Tool | Purpose |
|---|---|
| [Python 3.10+](https://www.python.org/downloads/) | Runs the application |
| [FFmpeg](https://ffmpeg.org/) | Converts audio to MP3, embeds metadata/thumbnails |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Handles the actual media extraction |
| [Git](https://git-scm.com/) | Clones the repository |

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YT-Music-Downloader.git
cd YT-Music-Downloader
```

### 2. Install Python Dependencies

<details>
<summary><strong>Windows</strong></summary>

```powershell
py -m pip install -r requirements.txt
```
</details>

<details>
<summary><strong>Linux</strong></summary>

```bash
python3 -m pip install -r requirements.txt
```
</details>

<details>
<summary><strong>macOS</strong></summary>

```bash
python3 -m pip install -r requirements.txt
```
</details>

---

### 🎬 Installing FFmpeg

FFmpeg is required for converting downloaded audio to MP3 and embedding metadata/thumbnails.

<details>
<summary><strong>Windows</strong></summary>

Using Winget:

```powershell
winget install Gyan.FFmpeg
```

Or download a build from the [official FFmpeg site](https://ffmpeg.org/download.html) and add its `bin` directory to your system `PATH`.

Verify:

```powershell
ffmpeg -version
```
</details>

<details>
<summary><strong>Ubuntu / Debian</strong></summary>

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify:

```bash
ffmpeg -version
```
</details>

<details>
<summary><strong>Fedora</strong></summary>

```bash
sudo dnf install ffmpeg
```
</details>

<details>
<summary><strong>Arch Linux</strong></summary>

```bash
sudo pacman -S ffmpeg
```
</details>

<details>
<summary><strong>macOS</strong></summary>

Using Homebrew:

```bash
brew install ffmpeg
```

Verify:

```bash
ffmpeg -version
```
</details>

---

### 📥 Installing yt-dlp

<details>
<summary><strong>Windows</strong></summary>

Using Winget:

```powershell
winget install yt-dlp
```

Or via pip:

```powershell
py -m pip install -U "yt-dlp[default]"
```

Verify:

```powershell
yt-dlp --version
```
</details>

<details>
<summary><strong>Linux</strong></summary>

Using pip:

```bash
python3 -m pip install -U "yt-dlp[default]"
```

Or on Ubuntu/Debian systems where the package is available:

```bash
sudo apt update
sudo apt install yt-dlp
```

Verify:

```bash
yt-dlp --version
```
</details>

<details>
<summary><strong>macOS</strong></summary>

Using Homebrew:

```bash
brew install yt-dlp
```

Or using pip:

```bash
python3 -m pip install -U "yt-dlp[default]"
```

Verify:

```bash
yt-dlp --version
```
</details>

---

## ▶️ Usage

Run the application:

| OS | Command |
|---|---|
| Windows | `py main.py` |
| Linux | `python3 main.py` |
| macOS | `python3 main.py` |

You'll be greeted with an interactive menu:

```text
Main Menu
1. Download Track or Playlist
2. Change Download Location
3. Exit
```

Simply enter a YouTube or YouTube Music URL and choose your preferred audio quality.

---

## 📂 Download Organization

**Individual tracks** are saved directly to your selected download directory:

```text
Music/
└── Artist Song.mp3
```

**Playlists** are automatically placed in their own folder, with track numbering that follows the original playlist order — even if downloads finish out of sequence:

```text
Music/
└── Playlist Name/
    ├── 01 Artist Song.mp3
    ├── 02 Artist Song.mp3
    ├── 03 Artist Song.mp3
    └── ...
```

---

## 🗂️ Project Structure

```text
YT-Music-Playlist-Downloader/
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## ⚙️ Configuration

The app automatically remembers your last download location in a configuration file stored in your home directory. This file is created the first time you run the application — no manual setup required.

---

## 🔄 Updating Dependencies

Keep yt-dlp up to date to avoid extraction errors as YouTube changes:

```bash
python -m pip install -U "yt-dlp[default]"
```

On systems using `python3`:

```bash
python3 -m pip install -U "yt-dlp[default]"
```

---

## 🛠️ Troubleshooting

| Issue | Likely Fix |
|---|---|
| `ffmpeg: command not found` | FFmpeg isn't installed or not on your `PATH`. Re-check the [installation steps](#-installing-ffmpeg). |
| Download fails / extraction error | Update yt-dlp — YouTube changes frequently break older versions. |
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt` in the correct Python environment. |
| Playlist downloads out of order | Numbering is applied after all downloads complete — check the final folder, not download progress order. |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

This project is intended for downloading content that you have permission to download.

Users are responsible for complying with applicable copyright laws, the rights of content owners, and the terms of service of the platforms they use.

The author does not encourage unauthorized downloading or redistribution of copyrighted material.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for the complete license text.
