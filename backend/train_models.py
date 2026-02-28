import os
import zipfile
import requests
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import io
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

os.makedirs('models', exist_ok=True)

print("="*60)
print("PHASE 1: SEC EDGAR DATA ACQUISITION & ANOMALY MODEL TRAINING")
print("="*60)
# 1. Download SEC EDGAR data
url = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/2023q4.zip"
headers = {"User-Agent": "TAM Hackathon Team admin@tam.ai"}

try:
    print("Downloading SEC EDGAR 2023 Q4 dataset (this may take a minute)...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # 2. Extract specific files (limit nrows for memory safety during hackathon)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        print("Parsing numeric financial data (num.txt)...")
        num_df = pd.read_csv(z.open('num.txt'), sep='\t', usecols=['adsh', 'tag', 'value'], nrows=500000)

    print("Computing real-world financial benchmarks & ratios...")
    tags_of_interest = ['Revenues', 'GrossProfit', 'NetIncomeLoss', 'Assets', 'Liabilities', 'StockholdersEquity']
    num_filtered = num_df[num_df['tag'].isin(tags_of_interest)]
    
    # Pivot to get companies as rows
    pivoted = num_filtered.pivot_table(index='adsh', columns='tag', values='value', aggfunc='last').dropna()

    if 'Revenues' in pivoted.columns and 'GrossProfit' in pivoted.columns and 'NetIncomeLoss' in pivoted.columns:
        pivoted['gross_margin'] = (pivoted['GrossProfit'] / pivoted['Revenues'].replace(0, 1)) * 100
        pivoted['net_margin'] = (pivoted['NetIncomeLoss'] / pivoted['Revenues'].replace(0, 1)) * 100
        pivoted['asset_turnover'] = pivoted['Revenues'] / pivoted['Assets'].replace(0, 1)
        
        # Remove extreme outliers (bad data entries)
        pivoted = pivoted[(pivoted['gross_margin'] > -100) & (pivoted['gross_margin'] < 100)]
        
        features = ['gross_margin', 'net_margin'] 
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(pivoted[features])
        
        print(f"Training multivariate Isolation Forest on {len(pivoted)} real public companies...")
        iso = IsolationForest(contamination=0.05, random_state=42)
        iso.fit(X_scaled)
        
        joblib.dump(iso, 'models/sec_isolation_forest.joblib')
        joblib.dump(scaler, 'models/sec_scaler.joblib')
        joblib.dump(features, 'models/sec_features.joblib')
        print("✅ SEC Anomaly Model successfully saved to ./models/")
    else:
        print("Not enough complete company records found in the sample.")
except Exception as e:
    print(f"Failed to download/process SEC data: {e}. Skipping Anomaly Model.")


print("\n" + "="*60)
print("PHASE 2: SUPERVISED FINE-TUNING (SFT) FOR DOCUMENT CLASSIFICATION")
print("="*60)

# 1. Create a synthetic labeled training dataset representing M&A financials
# In a real scenario, this would be HuggingFace datasets load_dataset("...")
print("Preparing curated financial document text dataset...")
data = {
    "text": [
        "Consolidated statement of income. Revenue was 5M, COGS was 2M. Gross profit increased. Net income for the year ended.",
        "Balance sheet as of Dec 31. Current assets include cash, accounts receivable. Liabilities and Shareholders Equity.",
        "Cash flow from operating activities, investing activities, net cash provided. Capital expenditures.",
        "Independent Auditor's Report. In our opinion, the audited financial statements present fairly, in all material respects.",
        "Total sales for the quarter reached record highs, gross profit margins expanded. Operating expenses remained flat."
    ] * 30, # Synthetically expand dataset for training loop
    "label": [0, 1, 2, 3, 0] * 30 
}
df = pd.DataFrame(data)
dataset = Dataset.from_pandas(df)

model_name = "ProsusAI/finbert"
print(f"Downloading pre-trained base model ({model_name})...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4, ignore_mismatched_sizes=True)

    training_args = TrainingArguments(
        output_dir="./models/doc_classifier_checkpoint",
        num_train_epochs=2, # Fast fine-tuning for hackathon
        per_device_train_batch_size=8,
        logging_steps=10,
        report_to="none" # disable wandb
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
    )

    print("🚀 Starting SFT Training Loop (Transfer Learning)...")
    trainer.train()

    model.save_pretrained("./models/fine_tuned_doc_classifier")
    tokenizer.save_pretrained("./models/fine_tuned_doc_classifier")
    print("✅ Fine-tuned Document Classifier successfully saved to ./models/")
except Exception as e:
    print(f"Failed to fine-tune model: {e}")
