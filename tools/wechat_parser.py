#!/usr/bin/env python3
"""
微信聊天记录解析器
支持 WeChatMsg / 留痕 / PyWxDump 导出格式
针对亲友场景优化：提取口头禅、方言词汇、语音消息频率、关心/互动模式
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime


def detect_format(file_path: str) -> str:
    """自动检测导出文件格式"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.json':
        return 'json'
    elif ext == '.html' or ext == '.htm':
        return 'html'
    elif ext == '.csv':
        return 'csv'
    elif ext == '.db' or ext == '.sqlite':
        return 'sqlite'
    elif ext == '.txt':
        return 'txt'
    else:
        return 'txt'


def parse_txt(file_path: str, target_name: str) -> list:
    """解析纯文本格式的聊天记录"""
    messages = []
    current_msg = None

    # 常见的微信导出格式: "2024-01-01 12:00:00 张三"
    pattern = re.compile(
        r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+?)$'
    )

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            match = pattern.match(line)
            if match:
                if current_msg:
                    messages.append(current_msg)
                current_msg = {
                    'time': match.group(1),
                    'sender': match.group(2),
                    'content': ''
                }
            elif current_msg:
                if current_msg['content']:
                    current_msg['content'] += '\n'
                current_msg['content'] += line

    if current_msg:
        messages.append(current_msg)

    # 过滤目标人物的消息
    if target_name:
        target_msgs = [m for m in messages if target_name in m.get('sender', '')]
    else:
        target_msgs = messages

    return target_msgs


def parse_json(file_path: str, target_name: str) -> list:
    """解析 JSON 格式（留痕等工具导出）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = []
    # 适配多种 JSON 格式
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and 'messages' in data:
        items = data['messages']
    else:
        items = [data]

    for item in items:
        msg = {
            'time': item.get('time', item.get('timestamp', '')),
            'sender': item.get('sender', item.get('from', item.get('talker', ''))),
            'content': item.get('content', item.get('message', item.get('text', ''))),
            'type': item.get('type', item.get('msg_type', 'text'))
        }
        if target_name and target_name not in str(msg.get('sender', '')):
            continue
        messages.append(msg)

    return messages


def parse_html(file_path: str, target_name: str) -> list:
    """解析 HTML 格式（WeChatMsg 导出）"""
    messages = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 简单的 HTML 解析，提取消息文本
    # WeChatMsg 导出的 HTML 通常有特定的 class 名
    msg_pattern = re.compile(
        r'<div[^>]*class="[^"]*message[^"]*"[^>]*>.*?'
        r'<span[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</span>.*?'
        r'<span[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</span>',
        re.DOTALL
    )

    for match in msg_pattern.finditer(content):
        sender = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if target_name and target_name not in sender:
            continue
        messages.append({
            'sender': sender,
            'content': text,
            'type': 'text'
        })

    return messages


def analyze_messages(messages: list, target_name: str) -> dict:
    """分析消息，提取亲友特征"""
    target_msgs = [m for m in messages if not target_name or target_name in m.get('sender', '')]

    analysis = {
        'total_messages': len(target_msgs),
        'catchphrases': [],
        'word_frequency': {},
        'voice_message_ratio': 0,
        'care_patterns': [],
        'time_patterns': [],
        'emoji_usage': [],
        'message_length_avg': 0,
        'dialect_words': [],
        'sample_messages': []
    }

    if not target_msgs:
        return analysis

    # 词频统计
    all_text = ' '.join(m.get('content', '') for m in target_msgs if m.get('content'))
    words = re.findall(r'[\u4e00-\u9fff]+', all_text)
    word_counter = Counter(words)
    analysis['word_frequency'] = dict(word_counter.most_common(50))

    # 语音消息比例
    voice_count = sum(1 for m in target_msgs if m.get('type') in ['voice', 'audio', '语音'])
    analysis['voice_message_ratio'] = voice_count / len(target_msgs) if target_msgs else 0

    # 关心模式识别
    care_keywords = ['吃饭', '冷不冷', '加衣服', '注意身体', '早点睡', '回来', '到了没',
                     '钱够不够', '别太累', '多吃点', '喝水', '天气', '降温', '别熬夜']
    for msg in target_msgs:
        content = msg.get('content', '')
        for keyword in care_keywords:
            if keyword in content:
                analysis['care_patterns'].append({
                    'keyword': keyword,
                    'message': content[:100]
                })
                break

    # 消息长度
    lengths = [len(m.get('content', '')) for m in target_msgs if m.get('content')]
    analysis['message_length_avg'] = sum(lengths) / len(lengths) if lengths else 0

    # 表情符号使用
    emoji_pattern = re.compile(r'[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff]')
    emojis = emoji_pattern.findall(all_text)
    analysis['emoji_usage'] = dict(Counter(emojis).most_common(10))

    # 采样消息（最多20条有代表性的）
    sample_indices = list(range(0, len(target_msgs), max(1, len(target_msgs) // 20)))[:20]
    analysis['sample_messages'] = [target_msgs[i] for i in sample_indices]

    return analysis


def format_output(messages: list, analysis: dict, target_name: str) -> str:
    """格式化输出"""
    output = []
    output.append(f"# {target_name or '亲友'} 聊天记录分析\n")
    output.append(f"共解析 {analysis['total_messages']} 条消息\n")

    if analysis['voice_message_ratio'] > 0:
        output.append(f"语音消息占比：{analysis['voice_message_ratio']:.1%}\n")

    output.append(f"平均消息长度：{analysis['message_length_avg']:.0f} 字\n")

    if analysis['word_frequency']:
        output.append("\n## 高频词\n")
        for word, count in list(analysis['word_frequency'].items())[:20]:
            output.append(f"- {word}: {count}次")

    if analysis['care_patterns']:
        output.append("\n## 关心模式\n")
        seen = set()
        for p in analysis['care_patterns'][:15]:
            if p['keyword'] not in seen:
                output.append(f"- [{p['keyword']}] {p['message']}")
                seen.add(p['keyword'])

    if analysis['emoji_usage']:
        output.append("\n## 表情使用\n")
        for emoji, count in analysis['emoji_usage'].items():
            output.append(f"- {emoji}: {count}次")

    output.append("\n## 消息采样\n")
    for msg in analysis.get('sample_messages', [])[:20]:
        time_str = msg.get('time', '')
        sender = msg.get('sender', '')
        content = msg.get('content', '')[:200]
        output.append(f"[{time_str}] {sender}: {content}")

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='微信聊天记录解析器（亲友.skill）')
    parser.add_argument('--file', required=True, help='聊天记录文件路径')
    parser.add_argument('--target', default='', help='目标人物名称（过滤用）')
    parser.add_argument('--output', default='/tmp/wechat_out.txt', help='输出文件路径')
    parser.add_argument('--format', default='auto', choices=['auto', 'txt', 'json', 'html', 'csv', 'sqlite'],
                        help='文件格式（默认自动检测）')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}", file=sys.stderr)
        sys.exit(1)

    # 检测格式
    fmt = args.format if args.format != 'auto' else detect_format(args.file)
    print(f"检测到格式: {fmt}")

    # 解析
    if fmt == 'json':
        messages = parse_json(args.file, args.target)
    elif fmt == 'html':
        messages = parse_html(args.file, args.target)
    else:
        messages = parse_txt(args.file, args.target)

    print(f"共解析 {len(messages)} 条消息")

    # 分析
    analysis = analyze_messages(messages, args.target)

    # 输出
    result = format_output(messages, analysis, args.target)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"分析结果已保存到: {args.output}")


if __name__ == '__main__':
    main()
