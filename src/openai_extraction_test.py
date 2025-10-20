"""
Тест витягування сутностей з тексту через OpenAI
Інтеграція OpenAI + FalkorDB
"""

import os
import json
from datetime import datetime
from openai import OpenAI
from falkordb import FalkorDB

class OpenAIEntityExtractor:
    """Витягує сутності з тексту через OpenAI"""
    
    def __init__(self, graph_name="openai_test"):
        # OpenAI клієнт
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY не встановлений в .env")
        
        self.openai_client = OpenAI(api_key=api_key)
        
        # FalkorDB підключення
        host = os.getenv('FALKORDB_HOST', 'localhost')
        port = int(os.getenv('FALKORDB_PORT', 6379))
        
        self.db = FalkorDB(host=host, port=port)
        self.graph = self.db.select_graph(graph_name)
        
        # Очищаємо граф
        self.graph.query("MATCH (n) DETACH DELETE n")
        
        print(f"✅ OpenAI підключено")
        print(f"✅ FalkorDB граф: {graph_name}\n")
    
    def extract_entities(self, text, document_date=None):
        """
        Витягує сутності та зв'язки з тексту через OpenAI
        """
        
        if document_date is None:
            document_date = datetime.now().isoformat()
        
        prompt = f"""
Extract entities and relationships from this text:

Text: "{text}"
Document date: {document_date}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "entities": [
    {{
      "name": "canonical name",
      "type": "Person|Organization|Location|Event",
      "properties": {{"key": "value"}},
      "confidence": 0.95
    }}
  ],
  "relationships": [
    {{
      "source": "entity1 name",
      "target": "entity2 name",
      "type": "WORKS_FOR|LOCATED_IN|KNOWS",
      "properties": {{"role": "CEO"}},
      "temporal": {{
        "valid_from": "2020-01-01T00:00:00",
        "valid_until": null
      }},
      "confidence": 0.90
    }}
  ]
}}

Guidelines:
- Use canonical names (e.g., "Apple Inc." not "Apple")
- Extract temporal context when available
- Set confidence 0.0-1.0 based on text clarity
"""
        
        print("🤖 Відправляю запит до OpenAI...")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert entity extraction system. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Видаляємо markdown якщо є
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            
            print(f"✅ Витягнуто {len(result['entities'])} сутностей")
            print(f"✅ Витягнуто {len(result['relationships'])} зв'язків\n")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Помилка парсингу JSON: {e}")
            print(f"Відповідь OpenAI:\n{content}")
            return {"entities": [], "relationships": []}
        
        except Exception as e:
            print(f"❌ Помилка OpenAI: {e}")
            return {"entities": [], "relationships": []}
    
    def save_to_graph(self, extraction_result):
        """Зберігає витягнуті дані в FalkorDB"""
        
        print("💾 Збереження в FalkorDB...")
        
        entities = extraction_result.get("entities", [])
        relationships = extraction_result.get("relationships", [])
        
        # Створюємо сутності
        for entity in entities:
            self._create_entity(entity)
        
        # Створюємо зв'язки
        for rel in relationships:
            self._create_relationship(rel)
        
        print(f"✅ Збережено в граф\n")
    
    def _create_entity(self, entity):
        """Створює сутність в графі"""
        
        name = entity['name']
        entity_type = entity['type']
        properties = entity.get('properties', {})
        confidence = entity.get('confidence', 0.5)
        
        # Додаємо метадані
        properties['confidence'] = confidence
        properties['created_at'] = datetime.now().isoformat()
        
        # Формуємо properties string
        props_list = [f"name: '{name}'"]
        for k, v in properties.items():
            if isinstance(v, str):
                props_list.append(f"{k}: '{v}'")
            else:
                props_list.append(f"{k}: {v}")
        
        props_str = ', '.join(props_list)
        
        query = f"CREATE (e:{entity_type} {{{props_str}}}) RETURN e"
        
        try:
            self.graph.query(query)
            print(f"  ✅ {entity_type}: {name}")
        except Exception as e:
            print(f"  ❌ Помилка створення {name}: {e}")
    
    def _create_relationship(self, rel):
        """Створює зв'язок в графі"""
        
        source = rel['source']
        target = rel['target']
        rel_type = rel['type']
        properties = rel.get('properties', {})
        temporal = rel.get('temporal', {})
        confidence = rel.get('confidence', 0.5)
        
        # Bitemporal metadata
        valid_from = temporal.get('valid_from', datetime.now().isoformat())
        valid_until = temporal.get('valid_until', None)
        
        # Додаємо метадані
        properties['valid_from'] = valid_from
        properties['valid_until'] = valid_until if valid_until else 'null'
        properties['created_at'] = datetime.now().isoformat()
        properties['expired_at'] = 'null'
        properties['confidence'] = confidence
        
        # Формуємо properties string
        props_list = []
        for k, v in properties.items():
            if v == 'null':
                props_list.append(f"{k}: null")
            elif isinstance(v, str):
                props_list.append(f"{k}: '{v}'")
            else:
                props_list.append(f"{k}: {v}")
        
        props_str = ', '.join(props_list)
        
        query = f"""
        MATCH (a {{name: '{source}'}}), (b {{name: '{target}'}})
        CREATE (a)-[r:{rel_type} {{{props_str}}}]->(b)
        RETURN r
        """
        
        try:
            self.graph.query(query)
            print(f"  ✅ {source} -[{rel_type}]-> {target}")
        except Exception as e:
            print(f"  ❌ Помилка зв'язку {source}->{target}: {e}")
    
    def query_graph(self, question):
        """Запитує граф"""
        
        print(f"\n❓ Запит: {question}\n")
        
        # Простий приклад запиту
        query = """
        MATCH (p:Person)-[r:WORKS_FOR]->(c:Organization)
        RETURN p.name AS person, c.name AS company, r.valid_from AS from
        """
        
        result = self.graph.query(query)
        
        print("📊 Результат:")
        for record in result.result_set:
            print(f"   • {record[0]} працює в {record[1]} з {record[2]}")
        
        return result
    
    def run_demo(self):
        """Демонстрація витягування сутностей"""
        
        print("="*70)
        print("🤖 OpenAI + FalkorDB Integration Test")
        print("="*70 + "\n")
        
        # Тестовий текст
        test_text = """
        John Smith joined Apple Inc. as a Senior Software Engineer in January 2020. 
        He works on the iOS development team in Cupertino, California.
        In 2023, he was promoted to Tech Lead and now manages a team of 5 engineers.
        Apple Inc. is a technology company founded by Steve Jobs.
        """
        
        print("📄 Текст для аналізу:")
        print("-" * 70)
        print(test_text)
        print("-" * 70 + "\n")
        
        # Крок 1: Витягуємо сутності
        print("--- Крок 1: Витягування сутностей через OpenAI ---\n")
        
        extraction = self.extract_entities(test_text, "2024-10-20")
        
        # Показуємо що витягнуто
        print("📋 Витягнуті дані:")
        print(json.dumps(extraction, indent=2, ensure_ascii=False))
        print()
        
        # Крок 2: Зберігаємо в граф
        print("--- Крок 2: Збереження в FalkorDB ---\n")
        
        self.save_to_graph(extraction)
        
        # Крок 3: Запитуємо граф
        print("--- Крок 3: Запит до графу ---")
        
        self.query_graph("Хто де працює?")
        
        # Крок 4: Складний запит
        print("\n--- Крок 4: Всі сутності в графі ---\n")
        
        query = "MATCH (n) RETURN labels(n) AS type, n.name AS name, n.confidence AS conf"
        result = self.graph.query(query)
        
        print("📊 Всі сутності:")
        for record in result.result_set:
            print(f"   • {record[1]} ({record[0][0]}) - confidence: {record[2]}")
        
        print("\n" + "="*70)
        print("✅ Тест завершено!")
        print("="*70 + "\n")


if __name__ == "__main__":
    # Перевіряємо наявність API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Помилка: OPENAI_API_KEY не встановлений")
        print("Додай його в .env файл:")
        print("OPENAI_API_KEY=your_key_here")
        exit(1)
    
    extractor = OpenAIEntityExtractor()
    extractor.run_demo()
