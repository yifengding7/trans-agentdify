import csv
import re
import srt
from pathlib import Path

def term_replace(input_srt: str, term_csv: str, output_srt: str):
    # 读取术语词典
    terms = {}
    with open(term_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for en, zh in reader:
            terms[en.strip().lower()] = zh.strip()
    
    # 处理SRT文件
    subs = list(srt.parse(Path(input_srt).read_text(encoding='utf-8')))
    
    for sub in subs:
        # 创建正则表达式模式（全词匹配且不区分大小写）
        for en_term in terms:
            pattern = re.compile(rf'\b{re.escape(en_term)}\b', flags=re.IGNORECASE)
            sub.content = pattern.sub(terms[en_term], sub.content)
    
    Path(output_srt).write_text(srt.compose(subs), encoding='utf-8')

if __name__ == "__main__":
    import sys
    term_replace(sys.argv[1], sys.argv[2], sys.argv[3])