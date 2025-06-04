import sys
import srt
from loguru import logger
from pathlib import Path

def merge_subtitles(en_path: str, zh_path: str, output_path: str):
    try:
        en_subs = list(srt.parse(Path(en_path).read_text(encoding='utf-8')))
        zh_subs = list(srt.parse(Path(zh_path).read_text(encoding='utf-8')))

        if len(en_subs) != len(zh_subs):
            logger.warning(f'字幕行数不匹配: 英文{len(en_subs)}行 vs 中文{len(zh_subs)}行')

        merged = []
        for idx, (en, zh) in enumerate(zip(en_subs, zh_subs), 1):
            merged.append(srt.Subtitle(
                index=idx,
                start=en.start,
                end=en.end,
                content=f"{en.content}\n{zh.content}"
            ))

        Path(output_path).write_text(srt.compose(merged), encoding='utf-8')
        logger.success(f'成功生成双语字幕: {output_path}')
    except Exception as e:
        logger.error(f'字幕合并失败: {str(e)}')
        raise

if __name__ == "__main__":
    merge_subtitles(sys.argv[1], sys.argv[2], sys.argv[3])