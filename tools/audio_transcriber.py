#!/usr/bin/env python3
"""
语音/视频转文本工具
亲友.skill 差异化功能：亲人（尤其老人）和朋友都可能发语音消息，需要转文本并提取说话风格
支持格式：mp3, wav, m4a, amr（微信语音格式）, mp4, mov
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    deps = {
        'whisper': False,
        'ffmpeg': False
    }

    try:
        import whisper
        deps['whisper'] = True
    except ImportError:
        pass

    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        deps['ffmpeg'] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return deps


def convert_amr_to_wav(input_path: str, output_path: str) -> bool:
    """将微信 AMR 格式转换为 WAV"""
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-i', input_path, '-ar', '16000', '-ac', '1', output_path],
            capture_output=True, timeout=30
        )
        return os.path.exists(output_path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def transcribe_with_whisper(file_path: str, language: str = 'zh') -> dict:
    """使用 OpenAI Whisper 进行语音转文本"""
    try:
        import whisper
    except ImportError:
        return {'error': '请安装 whisper: pip install openai-whisper'}

    model = whisper.load_model('base')
    result = model.transcribe(file_path, language=language)

    return {
        'text': result.get('text', ''),
        'segments': [
            {
                'start': seg.get('start', 0),
                'end': seg.get('end', 0),
                'text': seg.get('text', '')
            }
            for seg in result.get('segments', [])
        ],
        'language': result.get('language', language)
    }


def analyze_speech_style(transcription: dict) -> dict:
    """分析说话风格（语速、口头禅等）"""
    text = transcription.get('text', '')
    segments = transcription.get('segments', [])

    analysis = {
        'total_duration': 0,
        'total_characters': len(text),
        'speech_rate': 0,  # 字/秒
        'filler_words': [],  # 语气词
        'repeated_phrases': [],  # 重复的短语
    }

    # 计算总时长
    if segments:
        analysis['total_duration'] = segments[-1].get('end', 0) - segments[0].get('start', 0)
        if analysis['total_duration'] > 0:
            analysis['speech_rate'] = analysis['total_characters'] / analysis['total_duration']

    # 提取语气词
    import re
    filler_patterns = [
        '嗯', '哦', '噢', '啊', '哎', '唉', '嘿', '哈',
        '那个', '就是', '然后', '反正', '这个那个', '你说是不是',
        '我跟你说', '哎呀'
    ]
    for pattern in filler_patterns:
        count = text.count(pattern)
        if count > 0:
            analysis['filler_words'].append({'word': pattern, 'count': count})

    analysis['filler_words'].sort(key=lambda x: x['count'], reverse=True)

    return analysis


def process_directory(dir_path: str, output_path: str, language: str = 'zh'):
    """批量处理目录下的音频/视频文件"""
    supported_ext = {'.mp3', '.wav', '.m4a', '.amr', '.mp4', '.mov', '.ogg', '.flac'}
    results = []

    dir_p = Path(dir_path)
    files = [f for f in dir_p.rglob('*') if f.suffix.lower() in supported_ext]

    if not files:
        print(f"未找到支持的音频/视频文件（支持格式: {', '.join(supported_ext)}）")
        return

    print(f"找到 {len(files)} 个文件待处理")

    for i, file_path in enumerate(files):
        print(f"[{i+1}/{len(files)}] 处理: {file_path.name}")

        # AMR 格式需要先转换
        actual_path = str(file_path)
        if file_path.suffix.lower() == '.amr':
            wav_path = str(file_path.with_suffix('.wav'))
            if convert_amr_to_wav(actual_path, wav_path):
                actual_path = wav_path
            else:
                print(f"  警告: AMR 转换失败，跳过 {file_path.name}")
                continue

        # 转文本
        transcription = transcribe_with_whisper(actual_path, language)
        if 'error' in transcription:
            print(f"  错误: {transcription['error']}")
            continue

        # 分析说话风格
        style = analyze_speech_style(transcription)

        results.append({
            'file': file_path.name,
            'text': transcription.get('text', ''),
            'duration': style['total_duration'],
            'speech_rate': style['speech_rate'],
            'filler_words': style['filler_words']
        })

        print(f"  文本: {transcription.get('text', '')[:80]}...")

    # 生成汇总
    output = format_results(results)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\n结果已保存到: {output_path}")


def process_single_file(file_path: str, output_path: str, language: str = 'zh'):
    """处理单个文件"""
    actual_path = file_path

    if file_path.lower().endswith('.amr'):
        wav_path = file_path.rsplit('.', 1)[0] + '.wav'
        if convert_amr_to_wav(file_path, wav_path):
            actual_path = wav_path
        else:
            print("AMR 转换失败，请确保安装了 ffmpeg")
            sys.exit(1)

    transcription = transcribe_with_whisper(actual_path, language)
    if 'error' in transcription:
        print(f"错误: {transcription['error']}")
        sys.exit(1)

    style = analyze_speech_style(transcription)

    results = [{
        'file': os.path.basename(file_path),
        'text': transcription.get('text', ''),
        'duration': style['total_duration'],
        'speech_rate': style['speech_rate'],
        'filler_words': style['filler_words']
    }]

    output = format_results(results)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"结果已保存到: {output_path}")


def format_results(results: list) -> str:
    """格式化输出结果"""
    output = ["# 语音/视频转文本结果\n"]

    all_text = ' '.join(r['text'] for r in results)
    total_duration = sum(r['duration'] for r in results)
    avg_rate = sum(r['speech_rate'] for r in results) / len(results) if results else 0

    output.append(f"共处理 {len(results)} 个文件")
    output.append(f"总时长：{total_duration:.0f} 秒")
    output.append(f"平均语速：{avg_rate:.1f} 字/秒\n")

    # 汇总语气词
    all_fillers = {}
    for r in results:
        for fw in r.get('filler_words', []):
            word = fw['word']
            all_fillers[word] = all_fillers.get(word, 0) + fw['count']

    if all_fillers:
        output.append("## 语气词统计\n")
        for word, count in sorted(all_fillers.items(), key=lambda x: -x[1]):
            output.append(f"- {word}: {count}次")

    output.append("\n## 转写文本\n")
    for r in results:
        output.append(f"### {r['file']}")
        output.append(f"时长：{r['duration']:.0f}秒 | 语速：{r['speech_rate']:.1f}字/秒")
        output.append(f"{r['text']}\n")

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='语音/视频转文本工具（亲友.skill）')
    parser.add_argument('--file', help='单个音频/视频文件路径')
    parser.add_argument('--dir', help='包含音频/视频文件的目录')
    parser.add_argument('--output', default='/tmp/audio_out.txt', help='输出文件路径')
    parser.add_argument('--language', default='zh', help='语言（默认：zh）')
    parser.add_argument('--check', action='store_true', help='检查依赖')

    args = parser.parse_args()

    if args.check:
        deps = check_dependencies()
        print("依赖检查：")
        print(f"  whisper: {'✅ 已安装' if deps['whisper'] else '❌ 未安装 (pip install openai-whisper)'}")
        print(f"  ffmpeg: {'✅ 已安装' if deps['ffmpeg'] else '❌ 未安装 (需要处理 AMR/视频格式)'}")
        sys.exit(0)

    if not args.file and not args.dir:
        parser.error("请指定 --file 或 --dir")

    if args.dir:
        process_directory(args.dir, args.output, args.language)
    else:
        process_single_file(args.file, args.output, args.language)


if __name__ == '__main__':
    main()
