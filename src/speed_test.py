"""
Тести швидкості FalkorDB
Вимірює продуктивність різних операцій
"""

import os
import time
from falkordb import FalkorDB
from datetime import datetime
import statistics

class SpeedTester:
    """Тести продуктивності"""
    
    def __init__(self, graph_name="speed_test"):
        host = os.getenv('FALKORDB_HOST', 'localhost')
        port = int(os.getenv('FALKORDB_PORT', 6379))
        
        self.db = FalkorDB(host=host, port=port)
        self.graph = self.db.select_graph(graph_name)
        
        # Очищаємо граф
        self.graph.query("MATCH (n) DETACH DELETE n")
        print(f"✅ Підключено до тестового графу")
    
    def measure_time(self, func, *args, **kwargs):
        """Вимірює час виконання функції"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return (end - start) * 1000, result  # В мілісекундах
    
    def test_node_creation(self, count=100):
        """Тест швидкості створення вузлів"""
        
        print(f"\n🔄 Створення {count} вузлів...")
        
        times = []
        for i in range(count):
            query = f"""
            CREATE (p:Person {{
                name: 'Person_{i}',
                age: {20 + (i % 50)},
                created_at: '{datetime.now().isoformat()}'
            }})
            """
            
            elapsed, _ = self.measure_time(self.graph.query, query)
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        print(f"✅ Середній час створення: {avg_time:.2f} ms")
        print(f"   Min: {min(times):.2f} ms | Max: {max(times):.2f} ms")
        
        return times
    
    def test_batch_creation(self, count=100):
        """Тест пакетного створення вузлів"""
        
        print(f"\n🔄 Пакетне створення {count} вузлів...")
        
        # Формуємо один великий запит
        creates = []
        for i in range(count):
            creates.append(f"""
                CREATE (p{i}:Person {{
                    name: 'BatchPerson_{i}',
                    age: {20 + (i % 50)}
                }})
            """)
        
        query = "\n".join(creates)
        
        elapsed, _ = self.measure_time(self.graph.query, query)
        
        print(f"✅ Час пакетного створення: {elapsed:.2f} ms")
        print(f"   Швидкість: {count / (elapsed / 1000):.0f} вузлів/сек")
        
        return elapsed
    
    def test_relationship_creation(self, count=50):
        """Тест створення зв'язків"""
        
        print(f"\n🔄 Створення {count} зв'язків...")
        
        times = []
        for i in range(count):
            query = f"""
            MATCH (a:Person {{name: 'Person_{i}'}}), (b:Person {{name: 'Person_{i+1}'}})
            CREATE (a)-[r:KNOWS {{since: '2024'}}]->(b)
            """
            
            elapsed, _ = self.measure_time(self.graph.query, query)
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        print(f"✅ Середній час створення зв'язку: {avg_time:.2f} ms")
        
        return times
    
    def test_simple_query(self, iterations=100):
        """Тест простих запитів"""
        
        print(f"\n🔄 Виконання {iterations} простих запитів...")
        
        times = []
        for i in range(iterations):
            query = f"MATCH (p:Person {{name: 'Person_{i % 100}'}}) RETURN p"
            
            elapsed, _ = self.measure_time(self.graph.query, query)
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        print(f"✅ Середній час запиту: {avg_time:.2f} ms")
        
        return times
    
    def test_complex_query(self, iterations=50):
        """Тест складних запитів з JOIN"""
        
        print(f"\n🔄 Виконання {iterations} складних запитів...")
        
        times = []
        for _ in range(iterations):
            query = """
            MATCH (p1:Person)-[:KNOWS]->(p2:Person)
            WHERE p1.age > 30
            RETURN p1.name, p2.name, p1.age
            LIMIT 10
            """
            
            elapsed, _ = self.measure_time(self.graph.query, query)
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        print(f"✅ Середній час складного запиту: {avg_time:.2f} ms")
        
        return times
    
    def test_graph_traversal(self, depth=3):
        """Тест обходу графу на глибину"""
        
        print(f"\n🔄 Обхід графу (глибина {depth})...")
        
        query = f"""
        MATCH path = (start:Person {{name: 'Person_0'}})-[:KNOWS*1..{depth}]->(end:Person)
        RETURN length(path) AS depth, COUNT(*) AS paths
        """
        
        elapsed, result = self.measure_time(self.graph.query, query)
        
        print(f"✅ Час обходу: {elapsed:.2f} ms")
        for record in result.result_set:
            print(f"   Глибина {record[0]}: {record[1]} шляхів")
        
        return elapsed
    
    def run_all_tests(self):
        """Запуск всіх тестів"""
        
        print("\n" + "="*60)
        print("⚡ ТЕСТИ ШВИДКОСТІ FalkorDB")
        print("="*60)
        
        # Тест 1: Створення вузлів
        node_times = self.test_node_creation(100)
        
        # Тест 2: Пакетне створення
        batch_time = self.test_batch_creation(100)
        
        # Тест 3: Створення зв'язків
        rel_times = self.test_relationship_creation(50)
        
        # Тест 4: Прості запити
        simple_times = self.test_simple_query(100)
        
        # Тест 5: Складні запити
        complex_times = self.test_complex_query(50)
        
        # Тест 6: Обхід графу
        traversal_time = self.test_graph_traversal(3)
        
        # Підсумок
        print("\n" + "="*60)
        print("📊 ПІДСУМОК")
        print("="*60)
        print(f"Створення вузла:      {statistics.mean(node_times):.2f} ms (середнє)")
        print(f"Пакетне створення:    {batch_time/200:.2f} ms (на вузол)")
        print(f"Створення зв'язку:    {statistics.mean(rel_times):.2f} ms (середнє)")
        print(f"Простий запит:        {statistics.mean(simple_times):.2f} ms (середнє)")
        print(f"Складний запит:       {statistics.mean(complex_times):.2f} ms (середнє)")
        print(f"Обхід графу:          {traversal_time:.2f} ms")
        print("="*60 + "\n")


if __name__ == "__main__":
    tester = SpeedTester()
    tester.run_all_tests()
