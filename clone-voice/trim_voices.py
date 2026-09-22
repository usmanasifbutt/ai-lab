"""One-off script: trim every WAV in voices/ to at most MAX_SECONDS, in place."""

from pathlib import Path

from utils import trim_to_max_duration

VOICES_DIR = Path(__file__).parent / "voices"
MAX_SECONDS = 15


def main() -> None:
    wav_files = sorted(VOICES_DIR.glob("*.wav"))
    if not wav_files:
        print("No WAV files found in voices/.")
        return

    for wav_path in wav_files:
        trim_to_max_duration(wav_path, MAX_SECONDS)
        print(f"Trimmed {wav_path.name} to <= {MAX_SECONDS}s")


if __name__ == "__main__":
    main()
