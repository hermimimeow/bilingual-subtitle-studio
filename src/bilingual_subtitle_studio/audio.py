from __future__ import annotations

import subprocess
from pathlib import Path

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def is_supported_audio(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def is_supported_video(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def build_ffmpeg_audio_command(input_path: Path, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "64k",
        str(output_path),
    ]


def extract_audio(input_path: Path, output_path: Path) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    if not is_supported_video(input_path):
        raise ValueError(f"unsupported video format: {input_path.suffix}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_audio_command(input_path, output_path)
    subprocess.run(command, check=True)
    return output_path
