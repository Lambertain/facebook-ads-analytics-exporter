"""Проверка данных в Railway PostgreSQL базе данных."""
import asyncio
import asyncpg

async def main():
    # DATABASE_PUBLIC_URL из Railway
    conn = await asyncpg.connect(
        "postgresql://postgres:aAfSfPLmOntvaLCDbYTuuGMkbLhSNcpu@gondola.proxy.rlwy.net:49425/railway"
    )

    try:
        # Проверяем какие таблицы есть
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)

        print("Таблицы в базе данных:")
        for table in tables:
            print(f"  - {table['table_name']}")

        # Проверяем данные в search_results (вкладка Реклама)
        print("\n" + "="*80)
        print("ВКЛАДКА РЕКЛАМА (search_results где tab_type='ads'):")
        print("="*80)

        ads_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM search_results
            WHERE tab_type = 'ads'
        """)
        print(f"Количество записей: {ads_count}")

        if ads_count > 0:
            # Показываем sample
            sample = await conn.fetch("""
                SELECT results
                FROM search_results
                WHERE tab_type = 'ads'
                LIMIT 1
            """)

            if sample:
                import json
                results = json.loads(sample[0]['results'])
                print(f"Количество строк в results: {len(results)}")
                if results:
                    print(f"Колонки: {list(results[0].keys())[:10]}...")

        # Проверяем данные в search_results (вкладка Студенты)
        print("\n" + "="*80)
        print("ВКЛАДКА СТУДЕНТИ (search_results где tab_type='students'):")
        print("="*80)

        students_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM search_results
            WHERE tab_type = 'students'
        """)
        print(f"Количество записей: {students_count}")

        if students_count > 0:
            sample = await conn.fetch("""
                SELECT results
                FROM search_results
                WHERE tab_type = 'students'
                LIMIT 1
            """)

            if sample:
                import json
                results = json.loads(sample[0]['results'])
                print(f"Количество строк в results: {len(results)}")
                if results:
                    print(f"Колонки: {list(results[0].keys())[:10]}...")

        # Проверяем данные в search_results (вкладка Вчителі)
        print("\n" + "="*80)
        print("ВКЛАДКА ВЧИТЕЛІ (search_results где tab_type='teachers'):")
        print("="*80)

        teachers_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM search_results
            WHERE tab_type = 'teachers'
        """)
        print(f"Количество записей: {teachers_count}")

        if teachers_count > 0:
            sample = await conn.fetch("""
                SELECT results
                FROM search_results
                WHERE tab_type = 'teachers'
                LIMIT 1
            """)

            if sample:
                import json
                results = json.loads(sample[0]['results'])
                print(f"Количество строк в results: {len(results)}")
                if results:
                    print(f"Колонки: {list(results[0].keys())[:10]}...")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
