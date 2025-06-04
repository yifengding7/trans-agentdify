import subprocess
from pathlib import Path
import srt
from datetime import timedelta

def stt(audio_path: str, output_srt: str):
    cmd = [
        "seamless_communication",
        "inference",
        "--model_name", "seamlessM4T_v2_large",
        "--task", "stt",
        "--input_audio", audio_path,
        "--output_srt", output_srt,
        "--device", "mps",
        "--target_lang", "eng"
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    import sys
    stt(sys.argv[1], sys.argv[2])