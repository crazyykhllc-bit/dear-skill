#!/usr/bin/env python3
"""
Skill 文件管理器
列出/管理已生成的亲友 Skill
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def list_skills(base_dir: str):
    """列出所有已生成的亲友 Skill"""
    base = Path(base_dir)
    if not base.exists():
        print("暂无已创建的亲友 Skill")
        return

    skills = []
    for slug_dir in sorted(base.iterdir()):
        if not slug_dir.is_dir():
            continue
        meta_path = slug_dir / 'meta.json'
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            skills.append(meta)
        elif (slug_dir / 'SKILL.md').exists():
            skills.append({
                'name': slug_dir.name,
                'slug': slug_dir.name,
                'created_at': datetime.fromtimestamp(
                    (slug_dir / 'SKILL.md').stat().st_mtime
                ).isoformat()
            })

    if not skills:
        print("暂无已创建的亲友 Skill")
        return

    print(f"共 {len(skills)} 个亲友 Skill：\n")
    for s in skills:
        name = s.get('name', s.get('slug', '?'))
        slug = s.get('slug', '?')
        version = s.get('version', '?')
        profile = s.get('profile', {})
        relation = profile.get('relation', '')
        origin = profile.get('origin', '')
        status = profile.get('status', '')

        info = f"  👤 {name}"
        if relation:
            info += f"（{relation}）"
        if origin:
            info += f" · {origin}"
        if status:
            info += f" · {status}"
        info += f"\n     /{slug} · 版本 {version}"

        created = s.get('created_at', '')[:10]
        updated = s.get('updated_at', '')[:10]
        if created:
            info += f" · 创建于 {created}"
        if updated and updated != created:
            info += f" · 更新于 {updated}"

        corrections = s.get('corrections_count', 0)
        if corrections:
            info += f" · {corrections} 次纠正"

        print(info)
        print()


def create_skill_directory(base_dir: str, slug: str):
    """创建 Skill 目录结构"""
    base = Path(base_dir) / slug
    dirs = [
        base / 'versions',
        base / 'memories' / 'chats',
        base / 'memories' / 'photos',
        base / 'memories' / 'audio',
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"已创建目录: {base}")


def main():
    parser = argparse.ArgumentParser(description='Skill 文件管理器（亲友.skill）')
    parser.add_argument('--action', required=True, choices=['list', 'create-dir'],
                        help='操作类型')
    parser.add_argument('--base-dir', default='./relatives', help='基础目录')
    parser.add_argument('--slug', help='Skill slug（create-dir 用）')

    args = parser.parse_args()

    if args.action == 'list':
        list_skills(args.base_dir)
    elif args.action == 'create-dir':
        if not args.slug:
            parser.error("--slug 为必填参数")
        create_skill_directory(args.base_dir, args.slug)


if __name__ == '__main__':
    main()
