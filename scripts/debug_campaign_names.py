"""
Диагностический скрипт для вывода ВСЕХ названий кампаний из Meta API.

Используется для диагностики проблемы с фильтрацией студентских кампаний.
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем родительский каталог в PYTHONPATH
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv()

# Импортируем модуль для работы с Meta leads
from app.services import meta_leads


async def main():
    """Главная функция - получить и вывести названия кампаний."""

    meta_page_id = os.getenv("META_PAGE_ID")
    meta_page_token = os.getenv("META_PAGE_ACCESS_TOKEN")

    if not meta_page_id or not meta_page_token:
        print("[ERROR] META_PAGE_ID or META_PAGE_ACCESS_TOKEN not set in .env")
        return

    # Запрашиваем последние 30 дней
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"[INFO] Fetching campaigns from {start_date} to {end_date}...")
    print(f"[INFO] META_PAGE_ID: {meta_page_id}\n")

    # Получаем кампании
    all_campaigns = await meta_leads.get_leads_for_period(
        page_id=meta_page_id,
        page_token=meta_page_token,
        start_date=start_date,
        end_date=end_date
    )

    print(f"[INFO] Total campaigns received: {len(all_campaigns)}\n")
    print("=" * 80)
    print("СПИСОК ВСЕХ НАЗВАНИЙ КАМПАНИЙ:")
    print("=" * 80)

    # Сортируем по количеству лидов (чтобы показать наиболее активные кампании сверху)
    campaigns_sorted = sorted(
        all_campaigns.items(),
        key=lambda x: len(x[1].get("leads", [])),
        reverse=True
    )

    for idx, (campaign_id, campaign_data) in enumerate(campaigns_sorted, 1):
        campaign_name = campaign_data.get("campaign_name", "NO_NAME")
        campaign_name_lower = campaign_name.lower()
        leads_count = len(campaign_data.get("leads", []))

        print(f"{idx:3d}. [{campaign_id}] {campaign_name}")
        print(f"     Lowercase: {campaign_name_lower}")
        print(f"     Leads: {leads_count}")

        # Проверяем текущие keywords
        current_student_keywords = ["student", "shkolnik"]
        current_teacher_keywords = ["prepod", "teacher", "vchitel"]

        matches_student = any(kw in campaign_name_lower for kw in current_student_keywords)
        matches_teacher = any(kw in campaign_name_lower for kw in current_teacher_keywords)

        if matches_student:
            print(f"     [OK STUDENT] Matches current student keywords")
        elif matches_teacher:
            print(f"     [OK TEACHER] Matches current teacher keywords")
        else:
            print(f"     [NO MATCH] Does NOT match any current keywords")

        print()

    print("=" * 80)
    print(f"[INFO] Total campaigns: {len(all_campaigns)}")

    # Статистика по соответствию keywords
    student_matches = sum(
        1 for cid, cdata in all_campaigns.items()
        if any(kw in cdata.get("campaign_name", "").lower() for kw in ["student", "shkolnik"])
    )
    teacher_matches = sum(
        1 for cid, cdata in all_campaigns.items()
        if any(kw in cdata.get("campaign_name", "").lower() for kw in ["prepod", "teacher", "vchitel"])
    )
    no_matches = len(all_campaigns) - student_matches - teacher_matches

    print(f"[INFO] Student keywords matches: {student_matches}")
    print(f"[INFO] Teacher keywords matches: {teacher_matches}")
    print(f"[INFO] No matches: {no_matches}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
