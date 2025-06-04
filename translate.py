import subprocess
from pathlib import Path
import srt

def translate(srt_en: str, srt_zh: str):
    cmd = [
        "seamless_communication",
        "inference",
        "--model_name", "seamlessM4T_v2_large",
        "--task", "s2tt",
        "--input_srt", srt_en,
        "--output_srt", srt_zh,
        "--device", "mps",
        "--source_lang", "eng",
        "--target_lang", "cmn"
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    import sys
    translate(sys.argv[1], sys.argv[2])