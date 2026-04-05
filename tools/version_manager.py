#!/usr/bin/env python3
"""
版本管理器
备份和回滚亲人 Skill 的历史版本
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def backup(base_dir: str, slug: str):
    """备份当前版本"""
    skill_dir = Path(base_dir) / slug
    versions_dir = skill_dir / 'versions'

    if not skill_dir.exists():
        print(f"错误：Skill 目录不存在: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    # 读取当前版本号
    meta_path = skill_dir / 'meta.json'
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        current_version = meta.get('version', 'v1')
    else:
        current_version = 'v1'

    # 创建版本目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    version_name = f"{current_version}_{timestamp}"
    version_dir = versions_dir / version_name
    version_dir.mkdir(parents=True, exist_ok=True)

    # 复制核心文件
    files_to_backup = ['persona.md', 'care.md', 'memory.md', 'SKILL.md', 'meta.json']
    backed_up = []
    for fname in files_to_backup:
        src = skill_dir / fname
        if src.exists():
            shutil.copy2(str(src), str(version_dir / fname))
            backed_up.append(fname)

    print(f"已备份版本 {version_name}")
    print(f"  备份文件: {', '.join(backed_up)}")
    print(f"  位置: {version_dir}")

    return version_name


def rollback(base_dir: str, slug: str, version: str):
    """回滚到指定版本"""
    skill_dir = Path(base_dir) / slug
    versions_dir = skill_dir / 'versions'

    if not versions_dir.exists():
        print("错误：没有可用的历史版本", file=sys.stderr)
        sys.exit(1)

    # 查找版本
    version_dir = None
    for d in versions_dir.iterdir():
        if d.is_dir() and version in d.name:
            version_dir = d
            break

    if not version_dir:
        print(f"错误：未找到版本 '{version}'", file=sys.stderr)
        print("可用版本：")
        list_versions(base_dir, slug)
        sys.exit(1)

    # 先备份当前版本
    print("备份当前版本...")
    backup(base_dir, slug)

    # 恢复文件
    restored = []
    for f in version_dir.iterdir():
        if f.is_file():
            shutil.copy2(str(f), str(skill_dir / f.name))
            restored.append(f.name)

    print(f"\n已回滚到版本: {version_dir.name}")
    print(f"  恢复文件: {', '.join(restored)}")


def list_versions(base_dir: str, slug: str):
    """列出所有历史版本"""
    versions_dir = Path(base_dir) / slug / 'versions'

    if not versions_dir.exists():
        print("暂无历史版本")
        return

    versions = sorted(versions_dir.iterdir(), reverse=True)
    versions = [v for v in versions if v.is_dir()]

    if not versions:
        print("暂无历史版本")
        return

    print(f"共 {len(versions)} 个历史版本：\n")
    for v in versions:
        files = [f.name for f in v.iterdir() if f.is_file()]
        mtime = datetime.fromtimestamp(v.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f"  📦 {v.name}")
        print(f"     时间: {mtime}")
        print(f"     文件: {', '.join(files)}")
        print()


def main():
    parser = argparse.ArgumentParser(description='版本管理器（亲人.skill）')
    parser.add_argument('--action', required=True,
                        choices=['backup', 'rollback', 'list'],
                        help='操作类型')
    parser.add_argument('--slug', required=True, help='Skill slug')
    parser.add_argument('--version', help='版本名（rollback 用）')
    parser.add_argument('--base-dir', default='./relatives', help='基础目录')

    args = parser.parse_args()

    if args.action == 'backup':
        backup(args.base_dir, args.slug)
    elif args.action == 'rollback':
        if not args.version:
            parser.error("--version 为必填参数")
        rollback(args.base_dir, args.slug, args.version)
    elif args.action == 'list':
        list_versions(args.base_dir, args.slug)


if __name__ == '__main__':
    main()
