"""
Тест bitemporal логіки - зв'язки з часовими мітками
Перевіряє роботу з valid_from/valid_until та created_at/expired_at
"""

import os
from falkordb import FalkorDB
from datetime import datetime, timedelta

class BitemporalTester:
    """Тести для bitemporal edges"""
    
    def __init__(self, graph_name="bitemporal_test"):
        host = os.getenv('FALKORDB_HOST', 'localhost')
        port = int(os.getenv('FALKORDB_PORT', 6379))
        
        self.db = FalkorDB(host=host, port=port)
        self.graph = self.db.select_graph(graph_name)
        
        # Очищаємо граф
        self.graph.query("MATCH (n) DETACH DELETE n")
        print(f"✅ Підключено до графу: {graph_name}\n")
    
    def create_person(self, name, title):
        """Створює персону"""
        query = f"""
        CREATE (p:Person {{
            name: '{name}',
            title: '{title}'
        }})
        RETURN p
        """
        self.graph.query(query)
        print(f"✅ Створено Person: {name} ({title})")
    
    def create_company(self, name, industry):
        """Створює компанію"""
        query = f"""
        CREATE (c:Company {{
            name: '{name}',
            industry: '{industry}'
        }})
        RETURN c
        """
        self.graph.query(query)
        print(f"✅ Створено Company: {name} ({industry})")
    
    def create_temporal_relationship(self, from_name, to_name, rel_type, 
                                    valid_from, valid_until=None, properties=None):
        """
        Створює зв'язок з bitemporal метаданими
        
        valid_from/valid_until - коли факт був правдивим в реальності
        created_at/expired_at - коли ми дізналися про факт
        """
        
        if properties is None:
            properties = {}
        
        # Bitemporal timestamps
        created_at = datetime.now().isoformat()
        valid_from_str = valid_from.isoformat() if isinstance(valid_from, datetime) else valid_from
        valid_until_str = valid_until.isoformat() if valid_until else 'null'
        
        # Формуємо properties
        props = {
            'valid_from': valid_from_str,
            'valid_until': valid_until_str,
            'created_at': created_at,
            'expired_at': 'null',
            **properties
        }
        
        props_str = ', '.join([
            f"{k}: '{v}'" if v != 'null' else f"{k}: null" 
            for k, v in props.items()
        ])
        
        query = f"""
        MATCH (a {{name: '{from_name}'}}), (b {{name: '{to_name}'}})
        CREATE (a)-[r:{rel_type} {{{props_str}}}]->(b)
        RETURN r
        """
        
        self.graph.query(query)
        print(f"✅ Створено зв'язок: {from_name} -[{rel_type}]-> {to_name}")
        print(f"   valid_from: {valid_from_str}")
        print(f"   valid_until: {valid_until_str}")
    
    def query_at_time(self, person_name, company_name, target_date):
        """
        Запит: чи працювала персона в компанії на конкретну дату?
        """
        
        target_str = target_date.isoformat() if isinstance(target_date, datetime) else target_date
        
        query = f"""
        MATCH (p:Person {{name: '{person_name}'}})-[r:WORKS_FOR]->(c:Company {{name: '{company_name}'}})
        WHERE r.valid_from <= '{target_str}'
          AND (r.valid_until IS NULL OR r.valid_until >= '{target_str}')
          AND r.expired_at IS NULL
        RETURN p.name, c.name, r.valid_from, r.valid_until
        """
        
        result = self.graph.query(query)
        
        print(f"\n🔍 Чи працював {person_name} в {company_name} на {target_str}?")
        
        if result.result_set:
            for record in result.result_set:
                print(f"   ✅ ТАК: з {record[2]} до {record[3] or 'теперішнього часу'}")
            return True
        else:
            print(f"   ❌ НІ")
            return False
    
    def get_employment_history(self, person_name):
        """Отримує історію роботи персони"""
        
        query = f"""
        MATCH (p:Person {{name: '{person_name}'}})-[r:WORKS_FOR]->(c:Company)
        RETURN c.name AS company, r.valid_from AS from, r.valid_until AS until, r.expired_at AS expired
        ORDER BY r.valid_from DESC
        """
        
        result = self.graph.query(query)
        
        print(f"\n📋 Історія роботи {person_name}:")
        for record in result.result_set:
            status = "❌ Застаріло" if record[3] else "✅ Актуально"
            until = record[2] or "теперішній час"
            print(f"   {record[0]}: {record[1]} → {until} ({status})")
        
        return result
    
    def expire_relationship(self, person_name, company_name):
        """
        Позначає зв'язок як застарілий (не видаляє!)
        Встановлює expired_at = теперішній час
        """
        
        expired_at = datetime.now().isoformat()
        
        query = f"""
        MATCH (p:Person {{name: '{person_name}'}})-[r:WORKS_FOR]->(c:Company {{name: '{company_name}'}})
        WHERE r.expired_at IS NULL
        SET r.expired_at = '{expired_at}'
        SET r.valid_until = '{expired_at}'
        RETURN r
        """
        
        self.graph.query(query)
        print(f"\n⏰ Застарів зв'язок: {person_name} -[WORKS_FOR]-> {company_name}")
        print(f"   expired_at: {expired_at}")
    
    def run_demo(self):
        """Демонстрація bitemporal логіки"""
        
        print("="*70)
        print("⏰ BITEMPORAL TEST - Зв'язки з часовими мітками")
        print("="*70 + "\n")
        
        # Крок 1: Створюємо сутності
        print("--- Крок 1: Створення сутностей ---\n")
        
        self.create_person("John Smith", "Software Engineer")
        self.create_company("Apple Inc", "Technology")
        self.create_company("Microsoft", "Technology")
        
        # Крок 2: John працював в Apple з 2020 по 2023
        print("\n--- Крок 2: John працював в Apple (2020-2023) ---\n")
        
        self.create_temporal_relationship(
            "John Smith", 
            "Apple Inc", 
            "WORKS_FOR",
            valid_from=datetime(2020, 1, 15),
            valid_until=datetime(2023, 12, 31),
            properties={
                "role": "Senior Developer",
                "department": "iOS Team"
            }
        )
        
        # Крок 3: Запит - чи працював John в Apple у 2022?
        print("\n--- Крок 3: Перевірка на 2022 рік ---")
        
        self.query_at_time("John Smith", "Apple Inc", datetime(2022, 6, 1))
        
        # Крок 4: Запит - чи працює John в Apple зараз (2024)?
        print("\n--- Крок 4: Перевірка на 2024 рік ---")
        
        self.query_at_time("John Smith", "Apple Inc", datetime(2024, 10, 20))
        
        # Крок 5: John переходить в Microsoft (2024)
        print("\n--- Крок 5: John переходить в Microsoft (2024) ---\n")
        
        self.create_temporal_relationship(
            "John Smith",
            "Microsoft",
            "WORKS_FOR",
            valid_from=datetime(2024, 1, 1),
            valid_until=None,  # Досі працює
            properties={
                "role": "Tech Lead",
                "department": "Azure Team"
            }
        )
        
        # Крок 6: Історія роботи
        print("\n--- Крок 6: Повна історія роботи ---")
        
        self.get_employment_history("John Smith")
        
        # Крок 7: Застарілі дані
        print("\n--- Крок 7: Позначаємо старий зв'язок як expired ---")
        
        # Припустимо ми дізналися що дані про Apple застарілі
        self.expire_relationship("John Smith", "Apple Inc")
        
        # Крок 8: Перевірка після expire
        print("\n--- Крок 8: Історія після expire ---")
        
        self.get_employment_history("John Smith")
        
        # Крок 9: Складний temporal запит
        print("\n--- Крок 9: Де John працював у 2022-2024? ---")
        
        query = """
        MATCH (p:Person {name: 'John Smith'})-[r:WORKS_FOR]->(c:Company)
        WHERE r.valid_from <= '2024-12-31T23:59:59'
          AND (r.valid_until IS NULL OR r.valid_until >= '2022-01-01T00:00:00')
        RETURN c.name AS company, 
               r.valid_from AS from, 
               r.valid_until AS until,
               r.expired_at IS NULL AS is_active
        ORDER BY r.valid_from
        """
        
        result = self.graph.query(query)
        
        print("\n📊 Результат:")
        for record in result.result_set:
            active = "✅ Активний" if record[3] else "❌ Застарілий"
            until = record[2] or "досі"
            print(f"   • {record[0]}: {record[1]} → {until} ({active})")
        
        print("\n" + "="*70)
        print("✅ Bitemporal тест завершено!")
        print("="*70 + "\n")


if __name__ == "__main__":
    tester = BitemporalTester()
    tester.run_demo()
