"""
Тест: Получить всех архивных лідів одной причины отказа с пагинацией
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def test_pagination_for_reject():
    """Проверить работает ли пагинация для архивных лідів"""
    print("\n" + "="*80)
    print("ТЕСТ ПАГИНАЦИИ ДЛЯ АРХИВНЫХ ЛІДІВ")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Возьмем первую причину отказа
    url_rejects = f"{base_url}/v2api/lead-reject/index"
    resp = requests.post(
        url_rejects,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    lead_rejects = resp.json().get('items', [])

    if not lead_rejects:
        print("Нет причин отказа!")
        return

    # Возьмем "Не відповідає ( Не Ца )" - последнюю в списке
    test_reject = lead_rejects[-1]
    reject_id = test_reject.get('id')
    reject_name = test_reject.get('name')

    print(f"\nТестируем причину отказа: {reject_name} (ID {reject_id})")

    # Пробуем получить несколько страниц
    url_leads = f"{base_url}/v2api/customer/index"

    all_leads = {}  # По ID чтобы избежать дубликатов

    for page in range(1, 11):  # Первые 10 страниц
        resp = requests.post(
            url_leads,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "lead_reject_id": reject_id,
                "page": page,
                "page_size": 50
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])
        count = data.get('count', 0)

        new_leads = 0
        for lead in items:
            lead_id = lead.get('id')
            if lead_id not in all_leads:
                all_leads[lead_id] = lead
                new_leads += 1

        print(f"  Страница {page}: получено {len(items)} лідів, новых: {new_leads}, всего уникальных: {len(all_leads)}, count={count}")

        if len(items) == 0:
            print(f"  → Страница пустая, останавливаемся")
            break

        if new_leads == 0 and page > 2:
            print(f"  → Нет новых лідів, останавливаемся")
            break

    print(f"\n✓ Всего уникальных лідів для '{reject_name}': {len(all_leads)}")

    # Теперь попробуем для "Недозвон" статуса
    print(f"\n{'='*80}")
    print("ПОИСК ЛІДІВ В СТАТУСЕ 'Недодзвон'")
    print("="*80)

    # Сначала найдем ID статуса "Недодзвон"
    url_statuses = f"{base_url}/v2api/lead-status/index"
    resp = requests.post(
        url_statuses,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    statuses = resp.json().get('items', [])
    nedodzvon_id = None

    for status in statuses:
        if status.get('name') == 'Недодзвон':
            nedodzvon_id = status.get('id')
            break

    if nedodzvon_id:
        print(f"Нашли статус 'Недодзвон' с ID {nedodzvon_id}")

        # Попробуем получить лідів с этим статусом
        all_nedodzvon = {}

        for page in range(1, 11):
            resp = requests.post(
                url_leads,
                headers={"X-ALFACRM-TOKEN": token},
                json={
                    "lead_status_id": nedodzvon_id,
                    "page": page,
                    "page_size": 50
                },
                timeout=15
            )

            data = resp.json()
            items = data.get('items', [])

            new_leads = 0
            for lead in items:
                lead_id = lead.get('id')
                if lead_id not in all_nedodzvon:
                    all_nedodzvon[lead_id] = lead
                    new_leads += 1

            print(f"  Страница {page}: получено {len(items)} лідів, новых: {new_leads}, всего уникальных: {len(all_nedodzvon)}")

            if len(items) == 0:
                break

            if new_leads == 0 and page > 2:
                break

        print(f"\n✓ Всего уникальных лідів в статусе 'Недодзвон': {len(all_nedodzvon)}")

        # Проверим есть ли у них lead_reject_id
        with_reject = 0
        without_reject = 0

        for lead in list(all_nedodzvon.values())[:10]:
            if lead.get('lead_reject_id') is not None:
                with_reject += 1
            else:
                without_reject += 1

        print(f"\nИз первых 10 лідів в статусе 'Недодзвон':")
        print(f"  С lead_reject_id: {with_reject}")
        print(f"  Без lead_reject_id: {without_reject}")


if __name__ == "__main__":
    test_pagination_for_reject()
