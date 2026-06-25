import os
from pathlib import Path

import django
from django.conf import settings
from django.db import transaction

from PIL import Image, ImageOps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tigray_genocide.settings')
django.setup()

from App.models import Photo_archive

VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


def convert_image(old_path: Path, new_path: Path) -> bool:
    temp_path = new_path.with_suffix(new_path.suffix + '.tmp')
    try:
        with Image.open(old_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')

            temp_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(temp_path, format='WEBP', quality=90)

        if not temp_path.exists() or temp_path.stat().st_size == 0:
            print(f'ERROR: Converted file invalid for {old_path}')
            temp_path.unlink(missing_ok=True)
            return False

        temp_path.replace(new_path)
        return True
    except Exception as exc:
        print(f'ERROR: Failed to convert {old_path}: {exc}')
        temp_path.unlink(missing_ok=True)
        return False


def update_database(old_rel_path: str, new_rel_path: str) -> int:
    with transaction.atomic():
        return Photo_archive.objects.filter(photo=old_rel_path).update(photo=new_rel_path)


def main() -> int:
    media_root = Path(settings.MEDIA_ROOT)
    target_root = media_root / 'photo_archive'

    if not target_root.exists():
        print(f'ERROR: Target folder does not exist: {target_root}')
        return 1

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for old_path in sorted(target_root.rglob('*')):
        if not old_path.is_file():
            continue

        if old_path.suffix.lower() not in VALID_EXTENSIONS:
            skipped_count += 1
            continue

        old_rel_path = old_path.relative_to(media_root).as_posix()
        new_path = old_path.with_suffix('.webp')
        new_rel_path = new_path.relative_to(media_root).as_posix()

        if new_path.exists():
            print(f'NOTE: WebP already exists for {old_rel_path}; verifying DB update.')
            updated = update_database(old_rel_path, new_rel_path)
            if updated > 0:
                print(f'UPDATED DB rows: {updated} for {old_rel_path} -> {new_rel_path}')
                try:
                    old_path.unlink()
                    print(f'DELETED original after existing conversion: {old_rel_path}')
                except Exception as exc:
                    print(f'WARNING: Could not delete original file {old_rel_path}: {exc}')
            else:
                print(f'NO DB rows referenced {old_rel_path}; leaving original file in place.')
            processed_count += 1
            continue

        print(f'CONVERT: {old_rel_path} -> {new_rel_path}')

        if not convert_image(old_path, new_path):
            print(f'FAILED: {old_rel_path}')
            failed_count += 1
            continue

        if not new_path.exists() or new_path.stat().st_size == 0:
            print(f'ERROR: New WebP file missing or empty after conversion: {new_rel_path}')
            failed_count += 1
            continue

        updated = update_database(old_rel_path, new_rel_path)
        if updated == 0:
            print(f'WARNING: No DB rows found for {old_rel_path}; original retained.')
            skipped_count += 1
            continue

        try:
            old_path.unlink()
            print(f'SUCCESS: Converted and deleted original for {old_rel_path}; DB updated {updated} rows.')
            processed_count += 1
        except Exception as exc:
            print(f'ERROR: Could not delete original file {old_rel_path}: {exc}')
            failed_count += 1

    print('\nSUMMARY:')
    print(f'  Processed conversions: {processed_count}')
    print(f'  Skipped items: {skipped_count}')
    print(f'  Failed items: {failed_count}')
    return 0 if failed_count == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
