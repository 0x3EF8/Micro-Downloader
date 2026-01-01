# Micro Downloader

A compact, modern GUI-based video downloader built with Python and Tkinter. Supports downloading videos and audio from YouTube, Facebook, Twitter, Instagram, and 1000+ other sites using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

![Micro Downloader](assets/logo.png)

## Features

- **Multi-Platform Support:** Download from YouTube, Facebook, Twitter, Instagram, TikTok, and 1000+ sites
- **Video & Audio Downloads:** Choose between downloading videos (MP4) or extracting audio (MP3)
- **Quality Selection:** Multiple quality options from 144p to 4K for video, and up to 320kbps for audio
- **Modern UI:** Clean, compact interface with custom title bar and system tray support
- **Bundled Dependencies:** FFmpeg and Deno are included - no external setup required
- **Playlist Support:** Download entire playlists with progress tracking

## Download

Get the latest release from the [Releases](https://github.com/0x3EF8/Micro-Downloader/releases) page.

**[⬇️ Download MicroDownloader.exe](https://github.com/0x3EF8/Micro-Downloader/releases/latest)**

## Installation (Development)

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/0x3EF8/Micro-Downloader.git
   cd Micro-Downloader
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Binaries:**
   
   Download and place these in the `bin/` folder:
   - **FFmpeg:** [ffmpeg.org](https://ffmpeg.org/download.html) → `bin/ffmpeg.exe`
   - **Deno:** [deno.land](https://deno.land/) → `bin/deno.exe`

4. **Run:**
   ```bash
   python src/main.py
   ```

## Building from Source

```bash
cd src
pip install pyinstaller
pyinstaller main.spec --clean
```

The executable will be created at `src/dist/MicroDownloader.exe`

## Usage

1. **Paste URL:** Click "Paste" or press `Ctrl+V` to paste a video URL
2. **Select Format:** Choose Video (MP4) or Audio (MP3)
3. **Select Quality:** Pick your desired quality
4. **Download:** Click "Download" to start

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+V` | Paste URL |
| `Enter` | Start Download |
| `Escape` | Stop Download |

## Supported Sites

Micro Downloader uses yt-dlp which supports 1000+ sites including:

- YouTube (videos, shorts, playlists)
- Facebook (videos, reels)
- Twitter/X
- Instagram (posts, reels, stories)
- TikTok
- Vimeo
- Reddit
- And many more...

See the full list: [yt-dlp Supported Sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Project Structure

```
Micro-Downloader/
├── assets/
│   ├── logo.ico
│   └── logo.png
├── bin/
│   ├── ffmpeg.exe
│   └── deno.exe
├── src/
│   ├── main.py
│   └── main.spec
├── requirements.txt
├── LICENSE
└── README.md
```

## Dependencies

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloading
- [Pillow](https://python-pillow.org/) - Image processing
- [pystray](https://github.com/moses-palmer/pystray) - System tray integration
- [FFmpeg](https://ffmpeg.org/) - Media processing (bundled)
- [Deno](https://deno.land/) - JavaScript runtime for some extractors (bundled)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| FFmpeg not found | Place `ffmpeg.exe` in the `bin/` folder |
| Download fails | Check your internet connection and verify the URL is valid |
| Site not supported | Update yt-dlp: `pip install -U yt-dlp` |

## Author

**0x3EF8**

## License

This project is open source and available under the [MIT License](LICENSE).


