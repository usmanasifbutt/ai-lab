import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

# imageio-ffmpeg vendors a prebuilt ffmpeg binary, so mp3->wav conversion doesn't
# depend on a system-wide ffmpeg install.
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def to_wav(path: Path, output_dir: Path | None = None) -> Path:
    """Return a WAV version of path, converting it first if it's an MP3.

    Writes into output_dir if given, otherwise a fresh temp directory.
    """
    if path.suffix.lower() == ".wav":
        return path

    output_dir = output_dir or Path(tempfile.mkdtemp())
    wav_path = output_dir / f"{path.stem}.wav"
    subprocess.run(
        [FFMPEG_EXE, "-y", "-i", str(path), str(wav_path)],
        check=True,
        capture_output=True,
    )
    return wav_path


def trim_to_max_duration(path: Path, max_seconds: float = 15.0) -> None:
    """Trim a WAV file to at most max_seconds duration, in place."""
    tmp_path = path.with_suffix(".tmp.wav")
    subprocess.run(
        [FFMPEG_EXE, "-y", "-i", str(path), "-t", str(max_seconds), str(tmp_path)],
        check=True,
        capture_output=True,
    )
    tmp_path.replace(path)
