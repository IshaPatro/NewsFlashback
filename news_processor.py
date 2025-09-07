import os
import pandas as pd
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from config import CATEGORY_KEYWORDS

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

def clean_keywords(text):
    if pd.isna(text):
        return []
    keywords = [kw.strip().lower() for kw in str(text).split(",")]
    return [kw for kw in keywords if kw]

def get_keywords_and_relevance(text):
    prompt = f"""
    Extract the most relevant keywords from this news article and assign a relevance score to each keyword on a scale of 0.0 to 1.0.
    News: {text}
    
    Return strictly in this exact format without any markdown or code blocks:
    {{
        "keywords": [
            {{"keyword1": 0.95}},
            {{"keyword2": 0.12}},
            ...
        ]
    }}
    
    Only include keywords that are highly relevant to the content.
    """
    
    max_retries = 3
    retry_count = 0
    backoff_time = 2
    
    while retry_count < max_retries:
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith("```") and response_text.endswith("```"):
                clean_text = response_text.split("```")[1].strip()
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:].strip()
            else:
                clean_text = response_text
            
            result = json.loads(clean_text)
            return result["keywords"]
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                import time
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            else:
                print(f"Error extracting keywords after {max_retries} attempts: {str(e)}")
                return []

def process_directory():
    input_dir = "FinancialNewsData"
    processed_files = set()
    progress_file = "processing_progress.json"
    
    # Load progress if exists
    processed_indices = {}
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                processed_indices = json.load(f)
        except:
            processed_indices = {}
    
    for file_name in os.listdir(input_dir):
        if not file_name.endswith(".csv"):
            continue

        file_path = os.path.join(input_dir, file_name)
        df = pd.read_csv(file_path)
        
        if "keywords" in df.columns:
            df.drop(columns=["keywords"], inplace=True)
        
        if "Category_Score_Map" not in df.columns:
            df["Category_Score_Map"] = None
        
        file_updated = False
        file_indices = processed_indices.get(file_name, [])
        
        for idx, row in df.iterrows():
            # Skip already processed indices for this file
            if str(idx) in file_indices:
                continue
                
            # Skip rows that already have Category_Score_Map
            if not pd.isna(row["Category_Score_Map"]) and row["Category_Score_Map"]:
                if str(idx) not in file_indices:
                    file_indices.append(str(idx))
                continue
                
            full_text = row.get("Full Text", "")
            
            if not full_text or pd.isna(full_text):
                if str(idx) not in file_indices:
                    file_indices.append(str(idx))
                continue
                
            keywords_with_relevance = get_keywords_and_relevance(full_text)
            
            if keywords_with_relevance:
                print(f"AI Response for article in {file_name}: {keywords_with_relevance}")
                
                df.at[idx, "Category_Score_Map"] = str(keywords_with_relevance)
                df.to_csv(file_path, index=False)
                file_updated = True
                
                # Mark this index as processed
                if str(idx) not in file_indices:
                    file_indices.append(str(idx))
                    
                # Save progress after each article
                processed_indices[file_name] = file_indices
                with open(progress_file, 'w') as f:
                    json.dump(processed_indices, f)
                    
                print(f"✅ Processed article in {file_name} and updated CSV")
        
        if file_updated:
            processed_files.add(file_name)
        
        # Update progress for this file
        processed_indices[file_name] = file_indices
        with open(progress_file, 'w') as f:
            json.dump(processed_indices, f)
    
    if not processed_files:
        print("No files were updated. All articles may already have Category_Score_Map data.")
    else:
        print(f"✅ Processed and updated {len(processed_files)} files")

def clear_category_score_maps():
    input_dir = "FinancialNewsData"
    cleared_files = 0
    
    for file_name in os.listdir(input_dir):
        if not file_name.endswith(".csv"):
            continue

        file_path = os.path.join(input_dir, file_name)
        df = pd.read_csv(file_path)
        
        if "Category_Score_Map" in df.columns:
            df["Category_Score_Map"] = None
            df.to_csv(file_path, index=False)
            cleared_files += 1
    
    # Reset progress tracking file
    progress_file = "processing_progress.json"
    if os.path.exists(progress_file):
        os.remove(progress_file)
    
    print(f"✅ Cleared Category_Score_Map in {cleared_files} files and reset processing progress")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_category_score_maps()
    process_directory()
