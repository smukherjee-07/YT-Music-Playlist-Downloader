import json
import re
import shutil
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import yt_dlp
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.prompt import Prompt
from rich.table import Table


# ============================================================
# Configuration
# ============================================================

console = Console()

CONFIG_FILE = (
    Path.home()
    / ".config"
    / "music_downloader"
    / "config.json"
)

DEFAULT_CONCURRENT_DOWNLOADS = 3
MAX_CONCURRENT_DOWNLOADS = 4

# ============================================================
# Utility Functions
# ============================================================

def sanitize_name(name: str) -> str:
    """Remove characters that are illegal in Windows filenames."""
    clean = re.sub(r'[<>:"/\\|?*]', "", name)
    clean = clean.strip(". ")
    clean = " ".join(clean.split())

    return clean if clean else "unnamed_track"


def load_config() -> dict:
    """Load saved configuration."""
    if not CONFIG_FILE.exists():
        return {"last_location": None}

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {
            "last_location": None
        }

    except (json.JSONDecodeError, OSError):
        return {"last_location": None}


def save_config(config: dict) -> None:
    """Save configuration."""
    try:
        CONFIG_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except OSError as error:
        console.print(
            f"[yellow]Warning: Could not save configuration: {error}[/]"
        )


# ============================================================
# Dependency Checking
# ============================================================

def check_dependencies() -> bool:
    """Check for FFmpeg and yt-dlp executable."""
    missing = []

    if shutil.which("ffmpeg") is None:
        missing.append("FFmpeg")

    if shutil.which("yt-dlp") is None:
        missing.append("yt-dlp")

    if missing:
        console.print(
            "\n[bold red]Missing system dependencies:[/]"
        )

        for item in missing:
            console.print(f"  • {item}")

        console.print(
            "\n[dim]Make sure they are installed and available "
            "in your PATH.[/]\n"
        )

        return False

    return True


# ============================================================
# Download Location
# ============================================================

def get_download_directory() -> Path:
    """Get and remember the user's preferred download location."""
    config = load_config()
    last_location = config.get("last_location")

    if last_location:
        saved_path = Path(last_location)

        if saved_path.is_dir():
            console.print("\n[bold cyan]Download Location[/]")
            console.print(
                f"1. Use saved location: [green]{saved_path}[/]"
            )
            console.print("2. Choose a new location")

            choice = Prompt.ask(
                "Select option",
                choices=["1", "2"],
                default="1"
            )

            if choice == "1":
                return saved_path

    while True:
        raw_path = Prompt.ask(
            "\nEnter folder path to save music"
        ).strip()

        if not raw_path:
            console.print(
                "[yellow]Please enter a folder path.[/]"
            )
            continue

        try:
            target = (
                Path(raw_path)
                .expanduser()
                .resolve()
            )

            target.mkdir(
                parents=True,
                exist_ok=True
            )

            config["last_location"] = str(target)
            save_config(config)

            console.print(
                f"[green]Location saved:[/] {target}"
            )

            return target

        except OSError as error:
            console.print(
                f"[bold red]Invalid directory:[/] {error}"
            )


# ============================================================
# Quality Selection
# ============================================================

def select_quality() -> str:
    """Ask the user for MP3 quality."""
    console.print("\n[bold cyan]Select Audio Quality[/]")
    console.print("1. Best MP3 quality (VBR)")
    console.print("2. 320 kbps")
    console.print("3. 256 kbps")
    console.print("4. 192 kbps")
    console.print("5. 128 kbps")

    qualities = {
        "1": "0",
        "2": "320K",
        "3": "256K",
        "4": "192K",
        "5": "128K",
    }

    choice = Prompt.ask(
        "Choice",
        choices=list(qualities.keys()),
        default="1"
    )

    return qualities[choice]

def select_concurrency() -> int:
    """Choose the number of simultaneous playlist downloads."""

    console.print("\n[bold cyan]Concurrent Downloads[/]")
    console.print("1. 3 downloads at once")
    console.print("2. 4 downloads at once")

    choice = Prompt.ask(
        "Choice",
        choices=["1", "2"],
        default="1"
    )

    return 3 if choice == "1" else 4

# ============================================================
# URL Analysis
# ============================================================

def get_media_info(url: str) -> dict | None:
    """
    Inspect the URL with yt-dlp.

    The playlist/single-track detection is intentionally kept
    simple and is separate from the download process.
    """
    console.print(
        f"\n[bold cyan]Analyzing URL:[/] {url}"
    )

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(
                url,
                download=False
            )

    except Exception as error:
        console.print(
            f"[bold red]Failed to read URL:[/] {error}"
        )
        return None


# ============================================================
# Download Engine
# ============================================================

def build_options(output_template: str, audio_quality: str, hook) -> dict:
    """Build yt-dlp options for one download."""
    return {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": audio_quality,
            },
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
        "addmetadata": True,
        "writethumbnail": True,
        "embedthumbnail": True,
        "overwrites": True,
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "continuedl": True,
        "retries": 3,
    }


def make_entry_url(entry: dict) -> str | None:
    """Return a usable URL for a flat-playlist entry."""
    url = entry.get("webpage_url") or entry.get("url")

    if not url:
        return None

    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url

    # Flat extraction can return a video ID rather than a full URL.
    return f"https://www.youtube.com/watch?v={url}"


def download_single_track(
    info: dict,
    target_directory: Path,
    audio_quality: str,
) -> bool:
    """Download one track directly into the selected folder."""
    title = info.get("title") or "Unknown Track"
    url = info.get("webpage_url") or info.get("url")

    if not url:
        console.print("[bold red]No downloadable URL found.[/]")
        return False

    output_template = str(
        target_directory / "%(artist,uploader)s %(title)s.%(ext)s"
    )

    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task_id = progress.add_task(title, total=1, completed=0)

        def hook(data: dict) -> None:
            status = data.get("status")
            if status not in {"downloading", "finished"}:
                return

            info_dict = data.get("info_dict") or {}
            current_title = info_dict.get("title") or title
            total = (
                data.get("total_bytes")
                or data.get("total_bytes_estimate")
                or 1
            )
            downloaded = data.get("downloaded_bytes", 0)
            speed = data.get("speed") or 0

            progress.update(
                task_id,
                description=current_title,
                total=total,
                completed=downloaded,
                speed=speed,
            )

        options = build_options(output_template, audio_quality, hook)

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                result = ydl.download([url])

            if result != 0:
                return False

            task = progress.tasks[task_id]
            progress.update(
                task_id,
                description=f"{title} ✓",
                total=task.total or 1,
                completed=task.total or 1,
            )
            return True

        except Exception as error:
            console.print(f"\n[bold red]Download failed:[/] {title}")
            console.print(f"[dim]{error}[/]")
            return False


def download_playlist_entry(
    entry: dict,
    index: int,
    total_tracks: int,
    target_directory: Path,
    audio_quality: str,
    progress: Progress,
    task_id: int,
) -> bool:
    """Download one playlist entry while retaining its playlist index."""
    title = entry.get("title") or "Unknown Track"
    entry_url = make_entry_url(entry)

    if not entry_url:
        progress.update(
            task_id,
            description=f"[{index:02d}/{total_tracks:02d}] {title} ✗",
            total=1,
            completed=1,
        )
        return False

    output_template = str(
        target_directory
        / (
            f"{index:02d} "
            "%(artist,uploader)s "
            "%(title)s.%(ext)s"
        )
    )

    def hook(data: dict) -> None:
        status = data.get("status")
        if status not in {"downloading", "finished"}:
            return

        info_dict = data.get("info_dict") or {}
        current_title = info_dict.get("title") or title
        total = (
            data.get("total_bytes")
            or data.get("total_bytes_estimate")
            or 1
        )
        downloaded = data.get("downloaded_bytes", 0)
        speed = data.get("speed") or 0

        progress.update(
            task_id,
            description=(
                f"[{index:02d}/{total_tracks:02d}] {current_title}"
            ),
            total=total,
            completed=downloaded,
            speed=speed,
        )

    options = build_options(output_template, audio_quality, hook)

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            result = ydl.download([entry_url])

        if result != 0:
            raise RuntimeError("yt-dlp reported a download failure")

        task = progress.tasks[task_id]
        progress.update(
            task_id,
            description=(
                f"[{index:02d}/{total_tracks:02d}] {title} ✓"
            ),
            total=task.total or 1,
            completed=task.total or 1,
        )
        return True

    except Exception as error:
        progress.update(
            task_id,
            description=(
                f"[{index:02d}/{total_tracks:02d}] {title} ✗"
            ),
        )
        console.print(
            f"\n[bold red]Track {index:02d} failed:[/] {title}"
        )
        console.print(f"[dim]{error}[/]")
        return False


def download_playlist(
    info: dict,
    target_directory: Path,
    audio_quality: str,
    concurrent_downloads: int,
) -> None:
    """Download playlist entries concurrently while preserving playlist order."""
    playlist_name = sanitize_name(info.get("title") or "Playlist")
    playlist_directory = target_directory / playlist_name
    playlist_directory.mkdir(parents=True, exist_ok=True)

    entries = [
        entry for entry in (info.get("entries") or []) if entry
    ]
    total_tracks = len(entries)

    console.print(f"\n[bold green]Playlist:[/] {playlist_name}")
    console.print(f"[bold green]Tracks found:[/] {total_tracks}")
    console.print(
        f"[bold green]Concurrent downloads:[/] {concurrent_downloads}"
    )
    console.print(f"[dim]Saving to: {playlist_directory}[/]\n")

    if not entries:
        console.print("[yellow]No downloadable tracks found.[/]")
        return

    stats = {"downloaded": 0, "failed": 0}
    stats_lock = Lock()

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        refresh_per_second=8,
    ) as progress:
        task_ids = {}

        for index, entry in enumerate(entries, start=1):
            title = entry.get("title") or "Preparing..."
            task_ids[index] = progress.add_task(
                f"[{index:02d}/{total_tracks:02d}] {title}",
                total=1,
                completed=0,
            )

        console.print(
            f"[bold cyan]Downloading:[/] {total_tracks} track(s)"
        )

        worker_count = min(
            max(1, concurrent_downloads),
            MAX_CONCURRENT_DOWNLOADS,
            total_tracks,
        )

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(
                    download_playlist_entry,
                    entry,
                    index,
                    total_tracks,
                    playlist_directory,
                    audio_quality,
                    progress,
                    task_ids[index],
                ): index
                for index, entry in enumerate(entries, start=1)
            }

            # Completion order is deliberately ignored for playlist order.
            # The fixed index in each filename preserves the original order.
            for future in as_completed(futures):
                index = futures[future]

                try:
                    success = future.result()
                except Exception as error:
                    success = False
                    console.print(
                        f"\n[bold red]Track {index:02d} worker error:[/] {error}"
                    )

                with stats_lock:
                    if success:
                        stats["downloaded"] += 1
                    else:
                        stats["failed"] += 1

    console.print()

    table = Table(title="Download Summary", show_header=True)
    table.add_column("Status")
    table.add_column("Count", justify="right")
    table.add_row("Downloaded", str(stats["downloaded"]))
    table.add_row("Failed", str(stats["failed"]))
    console.print(table)

    console.print(
        f"\n[bold green]Saved to:[/] {playlist_directory}"
    )


# ============================================================
# Download Dispatcher
# ============================================================

def download_media(
    url: str,
    base_directory: Path,
    audio_quality: str,
    concurrent_downloads: int,
) -> None:
    """Detect and download a single track or playlist."""
    info = get_media_info(url)

    if info is None:
        return

    is_playlist = (
        info.get("_type") == "playlist"
        or "entries" in info
    )

    if is_playlist:
        download_playlist(
            info,
            base_directory,
            audio_quality,
            concurrent_downloads,
        )
        return

    title = info.get("title", "Unknown Track")

    console.print(f"\n[bold green]Single track:[/] {title}")
    console.print(
        f"[dim]Saving to: {base_directory}[/]\n"
    )

    success = download_single_track(
        info,
        base_directory,
        audio_quality,
    )

    console.print()
    if success:
        console.print(
            "[bold green]Download completed successfully.[/]"
        )
    else:
        console.print("[bold red]Download failed.[/]")

    console.print(
        f"[bold green]Saved to:[/] {base_directory}"
    )


# ============================================================
# Banner
# ============================================================

def display_banner() -> None:
    """Display application banner."""
    console.print(
        Panel(
            "[bold cyan]YT MUSIC DOWNLOADER[/]\n"
            "[dim]"
            "Single-track and playlist downloader"
            "[/]",
            expand=False
        )
    )


# ============================================================
# Interactive Mode
# ============================================================

def interactive_mode() -> None:
    """Run the interactive menu."""

    target_directory = get_download_directory()

    while True:
        console.print(
            "\n[bold cyan]Main Menu[/]"
        )

        console.print(
            "1. Download Track or Playlist"
        )
        console.print(
            "2. Change Download Location"
        )
        console.print(
            "3. Exit"
        )

        choice = Prompt.ask(
            "Select",
            choices=["1", "2", "3"],
            default="1"
        )

        if choice == "1":
            url = Prompt.ask(
                "\nEnter YouTube / YouTube Music URL"
            ).strip()

            if not url:
                console.print(
                    "[yellow]No URL entered.[/]"
                )
                continue

            quality = select_quality()
            concurrency = select_concurrency()

            download_media(
                url,
                target_directory,
                quality,
                concurrency
            )

        elif choice == "2":
            target_directory = (
                get_download_directory()
            )

        elif choice == "3":
            console.print(
                "\n[green]Goodbye![/]"
            )
            break


# ============================================================
# Command-Line Mode
# ============================================================

def command_line_mode(url: str) -> None:
    """
    Download directly from the command line.

    Example:
        python main.py "https://music.youtube.com/..."
    """

    config = load_config()

    saved_location = config.get(
        "last_location"
    )

    if saved_location:
        base_directory = Path(
            saved_location
        )
    else:
        base_directory = (
            Path.cwd()
            / "DownloadedMusic"
        )

    base_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # CLI mode uses best MP3 quality.
    download_media(
        url,
        base_directory,
        "0",
        DEFAULT_CONCURRENT_DOWNLOADS
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    """Application entry point."""

    display_banner()

    if not check_dependencies():
        sys.exit(1)

    if len(sys.argv) > 1:
        command_line_mode(
            sys.argv[1]
        )
        return

    interactive_mode()


if __name__ == "__main__":
    main()
