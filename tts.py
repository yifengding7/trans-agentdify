from TTS.api import TTS
from pathlib import Path
import numpy as np
import soundfile as sf
from loguru import logger
import sys
import json

tts_cache = Path('~/.tts_cache').expanduser()
tts_cache.mkdir(exist_ok=True)

def text_to_speech(text: str, speaker: str = "zh-CN-XiaoxiaoNeural"):
    cache_file = tts_cache / f"{hash(text)}-{speaker}.wav"
    
    if cache_file.exists():
        logger.info(f'使用缓存语音: {cache_file}')
        return str(cache_file)

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2",
             device="mps")
    
    wav = tts.tts(text=text,
                  speaker=speaker,
                  language="zh-cn",
                  split_sentences=True)
    
    sf.write(str(cache_file), np.array(wav), 24000)
    return str(cache_file)

def batch_tts(srt_path: str, output_wav: str):
    subs = list(srt.parse(Path(srt_path).read_text(encoding='utf-8')))
    
    with open(output_wav + '.json', 'w') as f:
        timelines = []
        
        for sub in subs:
            audio_file = text_to_speech(sub.content)
            timelines.append({
                "start": sub.start.total_seconds(),
                "end": sub.end.total_seconds(),
                "file": audio_file
            })
        
        json.dump(timelines, f)
    
    logger.success(f'生成TTS时间轴文件: {output_wav}.json')

if __name__ == "__main__":
    batch_tts(sys.argv[1], sys.argv[2])