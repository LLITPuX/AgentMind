"""
Базові операції з FalkorDB
CRUD операції для сутностей та зв'язків
"""

import os
from falkordb import FalkorDB
from datetime import datetime
import json

class GraphRAGBasic:
    """Базові операції з графом"""
    
    def __init__(self, graph_name="graphrag_test"):
        host = os.getenv('FALKORDB_HOST', 'localhost')
        port = int(os.getenv('FALKORDB_PORT', 6379))
        
        self.db = FalkorDB(host=host, port=port)
        self.graph = self.db.select_graph(graph_name)
        print(f"✅ Підключено до графу: {graph_name}")
    
    def create_entity(self, entity_type, name, properties=None):
        """Створює сутність (вузол) в графі"""
        
        if properties is None:
            properties = {}
        
        # Додаємо timestamp
        properties['created_at'] = datetime.now().isoformat()
        
        # Формуємо запит
        props_str = ', '.join([f"{k}: '{v}'" for k, v in properties.items()])
        query = f"""
        CREATE (e:{entity_type} {{
            name: '{name}',
            {props_str}
        }})
        RETURN e
        """
        
        result = self.graph.query(query)
        print(f"✅ Створено {entity_type}: {name}")
        return result
    
    def create_relationship(self, from_name, to_name, relation_type, properties=None):
        """Створює зв'язок між двома сутностями"""
        
        if properties is None:
            properties = {}
        
        # Додаємо temporal metadata
        properties['valid_from'] = datetime.now().isoformat()
        properties['created_at'] = datetime.now().isoformat()
        
        props_str = ', '.join([f"{k}: '{v}'" for k, v in properties.items()])
        
        query = f"""
        MATCH (a {{name: '{from_name}'}}), (b {{name: '{to_name}'}})
        CREATE (a)-[r:{relation_type} {{{props_str}}}]->(b)
        RETURN r
        """
        
        result = self.graph.query(query)
        print(f"✅ Створено зв'язок: {from_name} -[{relation_type}]-> {to_name}")
        return result
    
    def find_entity(self, name):
        """Знаходить сутність за назвою"""
        
        query = f"MATCH (e {{name: '{name}'}}) RETURN e"
        result = self.graph.query(query)
        
        if result.result_set:
            print(f"✅ Знайдено: {name}")
            return result.result_set
        else:
            print(f"❌ Не знайдено: {name}")
            return None
    
    def get_relationships(self, name):
        """Отримує всі зв'язки сутності"""
        
        query = f"""
        MATCH (e {{name: '{name}'}})-[r]->(other)
        RETURN type(r) AS relation, other.name AS target
        """
        
        result = self.graph.query(query)
        
        print(f"\n📊 Зв'язки для {name}:")
        for record in result.result_set:
            print(f"   → {record[0]}: {record[1]}")
        
        return result
    
    def query_graph(self, cypher_query):
        """Виконує довільний Cypher запит"""
        
        result = self.graph.query(cypher_query)
        return result
    
    def get_all_nodes(self):
        """Отримує всі вузли в графі"""
        
        query = "MATCH (n) RETURN n.name AS name, labels(n) AS type"
        result = self.graph.query(query)
        
        print("\n📋 Всі вузли в графі:")
        for record in result.result_set:
            print(f"   • {record[0]} ({record[1][0]})")
        
        return result
    
    def clear_graph(self):
        """Очищує граф (видаляє всі дані)"""
        
        query = "MATCH (n) DETACH DELETE n"
        self.graph.query(query)
        print("🧹 Граф очищено")


def run_demo():
    """Демонстрація базових операцій"""
    
    print("\n" + "="*60)
    print("🚀 DEMO: Базові операції з FalkorDB")
    print("="*60 + "\n")
    
    # Ініціалізація
    graph = GraphRAGBasic("demo_graph")
    
    # Очищаємо граф перед демо
    graph.clear_graph()
    
    print("\n--- Крок 1: Створення сутностей ---")
    
    # Створюємо людей
    graph.create_entity("Person", "John Doe", {
        "title": "Software Engineer",
        "email": "john@example.com"
    })
    
    graph.create_entity("Person", "Jane Smith", {
        "title": "CTO",
        "email": "jane@example.com"
    })
    
    # Створюємо компанії
    graph.create_entity("Company", "TechCorp", {
        "industry": "Technology",
        "founded": "2010"
    })
    
    graph.create_entity("Company", "StartupXYZ", {
        "industry": "AI/ML",
        "founded": "2023"
    })
    
    print("\n--- Крок 2: Створення зв'язків ---")
    
    # Зв'язки роботи
    graph.create_relationship("John Doe", "TechCorp", "WORKS_FOR", {
        "role": "Senior Developer",
        "since": "2020-01-15"
    })
    
    graph.create_relationship("Jane Smith", "StartupXYZ", "WORKS_FOR", {
        "role": "CTO",
        "since": "2023-06-01"
    })
    
    # Зв'язки знайомства
    graph.create_relationship("John Doe", "Jane Smith", "KNOWS", {
        "context": "University classmates"
    })
    
    print("\n--- Крок 3: Пошук сутностей ---")
    
    graph.find_entity("John Doe")
    graph.find_entity("TechCorp")
    
    print("\n--- Крок 4: Отримання зв'язків ---")
    
    graph.get_relationships("John Doe")
    graph.get_relationships("Jane Smith")
    
    print("\n--- Крок 5: Складний запит ---")
    
    # Знайти всіх людей що працюють в Tech компаніях
    query = """
    MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
    WHERE c.industry = 'Technology'
    RETURN p.name AS person, c.name AS company
    """
    
    result = graph.query_graph(query)
    
    print("\n🔍 Люди в Tech компаніях:")
    for record in result.result_set:
        print(f"   • {record[0]} працює в {record[1]}")
    
    print("\n--- Крок 6: Всі вузли ---")
    
    graph.get_all_nodes()
    
    print("\n" + "="*60)
    print("✅ Демо завершено успішно!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_demo()
