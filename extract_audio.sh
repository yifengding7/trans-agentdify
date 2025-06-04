#!/bin/bash

# 输入视频文件路径
INPUT_VIDEO="$1"
# 输出音频路径（16kHz 单声道 WAV）
OUTPUT_AUDIO="${2:-/tmp/$(date +%s)/audio.wav}"

mkdir -p "$(dirname "$OUTPUT_AUDIO")"

ffmpeg -i "$INPUT_VIDEO" -vn -acodec pcm_s16le -ar 16000 -ac 1 -y "$OUTPUT_AUDIO"