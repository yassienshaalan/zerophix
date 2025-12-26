import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

try:
    import torch
    from transformers import (
        AutoTokenizer, 
        AutoModelForTokenClassification, 
        TrainingArguments, 
        Trainer,
        DataCollatorForTokenClassification
    )
    from datasets import Dataset
except ImportError:
    print("Error: Fine-tuning requires 'transformers', 'torch', and 'datasets'.")
    print("Please install them with: pip install transformers torch datasets seqeval")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> List[Dict]:
    """
    Load data from a JSONL file.
    Each line should be: {"tokens": ["word1", "word2"], "ner_tags": ["O", "B-PERSON"]}
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def tokenize_and_align_labels(examples, tokenizer):
    tokenized_inputs = tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

def main():
    parser = argparse.ArgumentParser(description="Fine-tune a NER model for ZeroPhix")
    parser.add_argument("--train_file", type=str, required=True, help="Path to training data (JSONL)")
    parser.add_argument("--val_file", type=str, help="Path to validation data (JSONL)")
    parser.add_argument("--model_name", type=str, default="microsoft/deberta-v3-base", help="Base model to fine-tune")
    parser.add_argument("--output_dir", type=str, default="./fine_tuned_model", help="Directory to save the model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()

    logger.info(f"Loading data from {args.train_file}...")
    raw_train_data = load_data(args.train_file)
    
    # Create label map
    unique_labels = set()
    for item in raw_train_data:
        for tag in item["ner_tags"]:
            unique_labels.add(tag)
    
    label_list = sorted(list(unique_labels))
    label2id = {l: i for i, l in enumerate(label_list)}
    id2label = {i: l for i, l in enumerate(label_list)}
    
    logger.info(f"Found {len(label_list)} labels: {label_list}")

    # Convert tags to IDs
    def convert_tags_to_ids(data):
        for item in data:
            item["ner_tags"] = [label2id[tag] for tag in item["ner_tags"]]
        return data

    train_data = convert_tags_to_ids(raw_train_data)
    hf_train_dataset = Dataset.from_list(train_data)
    
    if args.val_file:
        raw_val_data = load_data(args.val_file)
        val_data = convert_tags_to_ids(raw_val_data)
        hf_val_dataset = Dataset.from_list(val_data)
    else:
        # Split train if no val provided
        split = hf_train_dataset.train_test_split(test_size=0.1)
        hf_train_dataset = split["train"]
        hf_val_dataset = split["test"]

    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize_fn(examples):
        return tokenize_and_align_labels(examples, tokenizer)

    tokenized_train = hf_train_dataset.map(tokenize_fn, batched=True)
    tokenized_val = hf_val_dataset.map(tokenize_fn, batched=True)

    logger.info("Loading model...")
    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name, 
        num_labels=len(label_list), 
        id2label=id2label, 
        label2id=label2id
    )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        evaluation_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        save_total_limit=2,
        logging_dir=f"{args.output_dir}/logs",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    logger.info("Starting training...")
    trainer.train()

    logger.info(f"Saving model to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    logger.info("Done! You can now use this model in ZeroPhix by setting 'models_dir' in your config.")

if __name__ == "__main__":
    main()
