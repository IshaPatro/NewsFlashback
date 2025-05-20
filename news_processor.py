import os
import pandas as pd
from config import CATEGORY_KEYWORDS

def clean_keywords(text):
    if pd.isna(text):
        return []
    keywords = [kw.strip().lower() for kw in str(text).split(",")]
    return [kw for kw in keywords if kw]

def categorize_article_with_score(keywords_list, full_text, CATEGORY_KEYWORDS=CATEGORY_KEYWORDS):
    results = {}
    full_text = str(full_text).lower()
    cleaned_keywords = [kw.lower() for kw in keywords_list]
    all_search_terms = set(cleaned_keywords + full_text.split())
    
    for category, subcategories in CATEGORY_KEYWORDS.items():
        category_data = {
            'total_score': 0.0,
            'subcategories': {}
        }
        
        subcategory_weight = 1/len(subcategories)
        
        for subcategory in subcategories:
            if subcategory in all_search_terms:
                score = round(subcategory_weight, 4)
                if score > 0.05: 
                    category_data['subcategories'][subcategory] = score
                    category_data['total_score'] += score
        
        category_data['total_score'] = round(category_data['total_score'], 2)
        if category_data['total_score'] >= 0.1:
            results[category] = category_data
    
    if not results:
        return {"Uncategorized": {'total_score': 0.0, 'subcategories': {}}}
    
    return dict(sorted(results.items(), key=lambda x: x[1]['total_score'], reverse=True))

def process_directory():
    input_dir = "FinancialNewsData"

    for file_name in os.listdir(input_dir):
        if not file_name.endswith(".csv"):
            continue

        file_path = os.path.join(input_dir, file_name)
        df = pd.read_csv(file_path)
        df["Category_Score_Map"] = df.apply(
            lambda row: categorize_article_with_score(
                clean_keywords(row["Keywords"]),
                row["Full Text"]
            ),
            axis=1
        )

        df.to_csv(file_path, index=False)
        print(f"✅ Processed and updated: {file_name}")

if __name__ == "__main__":
    process_directory()
