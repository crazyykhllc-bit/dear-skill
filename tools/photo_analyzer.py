#!/usr/bin/env python3
"""
照片元信息分析器
提取照片 EXIF 信息（时间、地点），构建家庭记忆时间线
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def extract_exif(file_path: str) -> dict:
    """提取照片 EXIF 信息"""
    info = {
        'file': os.path.basename(file_path),
        'date': None,
        'location': None,
        'camera': None
    }

    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS

        img = Image.open(file_path)
        exif_data = img._getexif()

        if not exif_data:
            return info

        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)

            if tag == 'DateTimeOriginal':
                try:
                    info['date'] = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S').isoformat()
                except (ValueError, TypeError):
                    info['date'] = str(value)

            elif tag == 'GPSInfo':
                gps_info = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value

                if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                    lat = _convert_gps(gps_info['GPSLatitude'])
                    lon = _convert_gps(gps_info['GPSLongitude'])
                    if gps_info.get('GPSLatitudeRef', 'N') == 'S':
                        lat = -lat
                    if gps_info.get('GPSLongitudeRef', 'E') == 'W':
                        lon = -lon
                    info['location'] = {'lat': lat, 'lon': lon}

            elif tag == 'Model':
                info['camera'] = str(value)

    except ImportError:
        # 如果没有 PIL，尝试用文件修改时间
        stat = os.stat(file_path)
        info['date'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
    except Exception as e:
        info['error'] = str(e)

    return info


def _convert_gps(gps_coords) -> float:
    """将 GPS 坐标转换为十进制度数"""
    try:
        d = float(gps_coords[0])
        m = float(gps_coords[1])
        s = float(gps_coords[2])
        return d + m / 60.0 + s / 3600.0
    except (TypeError, IndexError, ValueError):
        return 0.0


def analyze_photos(dir_path: str) -> dict:
    """分析目录下所有照片"""
    supported_ext = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.bmp'}
    dir_p = Path(dir_path)
    files = [f for f in dir_p.rglob('*') if f.suffix.lower() in supported_ext]

    if not files:
        return {'error': f'未找到照片文件（支持格式: {", ".join(supported_ext)}）'}

    print(f"找到 {len(files)} 张照片")

    photos = []
    for i, file_path in enumerate(files):
        if (i + 1) % 10 == 0:
            print(f"  处理中 {i+1}/{len(files)}...")
        info = extract_exif(str(file_path))
        photos.append(info)

    # 按时间排序
    dated = [p for p in photos if p.get('date')]
    dated.sort(key=lambda x: x['date'])

    # 统计
    analysis = {
        'total': len(photos),
        'with_date': len(dated),
        'with_location': sum(1 for p in photos if p.get('location')),
        'timeline': [],
        'locations': [],
        'photos': photos
    }

    # 构建时间线
    if dated:
        analysis['date_range'] = {
            'earliest': dated[0]['date'],
            'latest': dated[-1]['date']
        }
        # 按年月分组
        year_month = {}
        for p in dated:
            ym = p['date'][:7]  # YYYY-MM
            if ym not in year_month:
                year_month[ym] = 0
            year_month[ym] += 1
        analysis['timeline'] = [{'month': k, 'count': v} for k, v in sorted(year_month.items())]

    # 地点汇总
    locations = [p['location'] for p in photos if p.get('location')]
    analysis['locations'] = locations

    return analysis


def format_output(analysis: dict) -> str:
    """格式化输出"""
    output = ["# 照片分析结果\n"]

    if 'error' in analysis:
        output.append(f"错误：{analysis['error']}")
        return '\n'.join(output)

    output.append(f"共分析 {analysis['total']} 张照片")
    output.append(f"有时间信息：{analysis['with_date']} 张")
    output.append(f"有地理信息：{analysis['with_location']} 张\n")

    if 'date_range' in analysis:
        output.append(f"时间跨度：{analysis['date_range']['earliest'][:10]} ~ {analysis['date_range']['latest'][:10]}\n")

    if analysis['timeline']:
        output.append("## 时间分布\n")
        for item in analysis['timeline']:
            output.append(f"- {item['month']}: {item['count']} 张")

    if analysis['locations']:
        output.append(f"\n## 拍摄地点\n")
        output.append(f"共 {len(analysis['locations'])} 个带地理信息的照片\n")
        for loc in analysis['locations'][:20]:
            output.append(f"- ({loc['lat']:.4f}, {loc['lon']:.4f})")

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='照片元信息分析器（亲人.skill）')
    parser.add_argument('--dir', required=True, help='照片目录')
    parser.add_argument('--output', default='/tmp/photo_out.txt', help='输出文件路径')

    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"错误：目录不存在: {args.dir}", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_photos(args.dir)
    result = format_output(analysis)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"分析结果已保存到: {args.output}")


if __name__ == '__main__':
    main()
