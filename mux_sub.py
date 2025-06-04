import ffmpeg
from loguru import logger
import sys

def mux_subtitles(video_path: str, srt_path: str, output_path: str):
    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                vcodec='copy',
                acodec='copy',
                scodec='mov_text',
                metadata=f"handler=Chinese",
                map='0',
                map_metadata='-1',
                f='mp4',
                movflags='disable_chpl',
                **{'metadata:s:s:0': f'title=中英双语'}
            )
            .overwrite_output()
            .global_args('-i', srt_path)
            .run(capture_stdout=True, capture_stderr=True)
        )
        logger.success(f'成功封装字幕: {output_path}')
    except ffmpeg.Error as e:
        logger.error(f'封装失败: {e.stderr.decode()}')
        raise

if __name__ == "__main__":
    mux_subtitles(sys.argv[1], sys.argv[2], sys.argv[3])