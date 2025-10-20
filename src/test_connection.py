"""
Тест підключення до FalkorDB
Перевіряє чи працює база даних
"""

import os
from falkordb import FalkorDB

def test_connection():
    """Тестує підключення до FalkorDB"""
    
    print("🔌 Підключення до FalkorDB...")
    
    # Отримуємо параметри з environment
    host = os.getenv('FALKORDB_HOST', 'localhost')
    port = int(os.getenv('FALKORDB_PORT', 6379))
    
    try:
        # Підключаємося
        db = FalkorDB(host=host, port=port)
        
        # Створюємо тестовий граф
        graph = db.select_graph("test_graph")
        
        # Простий запит
        result = graph.query("RETURN 'Hello from FalkorDB!' AS message")
        
        # Виводимо результат
        for record in result.result_set:
            print(f"✅ З'єднання успішне: {record[0]}")
        
        # Інформація про підключення
        print(f"\n📊 Параметри підключення:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Граф: test_graph")
        
        # Очищаємо тестовий граф
        graph.delete()
        print("\n🧹 Тестовий граф видалено")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка підключення: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
