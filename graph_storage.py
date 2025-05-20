import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import ast
from config import OUTPUT_DIR

load_dotenv()

class GraphDBExporter:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URL")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError("Missing Neo4j credentials in .env file")
            
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def export_data(self, input_dir=OUTPUT_DIR):
        with self.driver.session() as session:
            for file_name in os.listdir(input_dir):
                if not file_name.endswith(".csv"):
                    continue
                
                file_path = os.path.join(input_dir, file_name)
                df = pd.read_csv(file_path)
                
                for _, row in df.iterrows():
                    try:
                        score_map = ast.literal_eval(row['Category_Score_Map'])
                    except (ValueError, SyntaxError, KeyError) as e:
                        print(f"Error parsing Category_Score_Map in {file_name}: {e}")
                        continue
                    article_id = session.execute_write(
                        self._create_article_node,
                        row.get('Headline', 'No Heading'),
                        row.get('URL', ''),
                        row.get('Full Text', '')
                    )
                    
                    for category, data in score_map.items():
                        if category == "Uncategorized":
                            continue
                            
                        session.execute_write(
                            self._create_category_structure,
                            category,
                            data,
                            article_id
                        )
    
    @staticmethod
    def _create_article_node(tx, heading, url, full_text):
        query = """
        CREATE (a:Article {
            heading: $heading,
            url: $url,
            full_text: $full_text,
            article_id: randomUUID(),
            last_updated: datetime()
        })
        RETURN a.article_id as article_id
        """
        result = tx.run(query, heading=heading, url=url, full_text=full_text)
        record = result.single()
        return record["article_id"] if record else None
    
    @staticmethod
    def _create_category_structure(tx, category, data, article_id):
        category_query = """
        MERGE (c:Category {name: $name})
        SET c.total_score = $score,
            c.last_updated = datetime()
        """
        tx.run(category_query, name=category, score=data.get('total_score', 0.0))
        
        for subcat, subdata in data.get('subcategories', {}).items():
            score = subdata.get('score') if isinstance(subdata, dict) else subdata
            
            subcat_query = """
            MATCH (a:Article {article_id: $article_id})
            MERGE (sc:Subcategory {name: $subcat})
            MERGE (c:Category {name: $cat})
            MERGE (c)-[:HAS_SUBCATEGORY]->(sc)
            MERGE (a)-[r:BELONGS_TO]->(sc)
            SET r.score = $score,
                r.last_updated = datetime()
            """
            tx.run(subcat_query,
                  article_id=article_id,
                  subcat=subcat,
                  cat=category,
                  score=score)

if __name__ == "__main__":
    try:
        exporter = GraphDBExporter()
        exporter.export_data()
        print("✅ Data exported to Neo4j successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'exporter' in locals():
            exporter.close()"}}}