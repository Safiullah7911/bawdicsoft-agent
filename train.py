%%writefile train.py
"""
Fine-tunes google/flan-t5-small on multi-column BawdicSoft dataset.
Columns: user_type, user_name, user_interests, page, context -> output
All columns joined into one input string before tokenization.
"""
import json
from datasets import Dataset
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments, Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
)

MODEL_NAME = "google/flan-t5-small"
MAX_INPUT_LEN = 512
MAX_TARGET_LEN = 64


def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return Dataset.from_list(rows)


def join_columns(example):
    """Multi-column ko ek input string mein jodo."""
    return {
        "input": (
            f"user_type: {example['user_type']} | "
            f"user_name: {example['user_name'] or 'none'} | "
            f"user_interests: {example['user_interests'] or 'none'} | "
            f"page: {example['page']} | "
            f"context: {example['context']}"
        ),
        "output": example["output"],
    }


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    train_raw = load_jsonl("data/train.jsonl")
    val_raw = load_jsonl("data/val.jsonl")

    train_ds = train_raw.map(join_columns, remove_columns=train_raw.column_names)
    val_ds = val_raw.map(join_columns, remove_columns=val_raw.column_names)

    print(f"Sample input: {train_ds[0]['input'][:200]}")
    print(f"Sample output: {train_ds[0]['output']}")

    def preprocess(batch):
        model_inputs = tokenizer(
            batch["input"], max_length=MAX_INPUT_LEN,
            truncation=True, padding="max_length",
        )
        labels = tokenizer(
            text_target=batch["output"], max_length=MAX_TARGET_LEN,
            truncation=True, padding="max_length",
        )
        labels["input_ids"] = [
            [(tok if tok != tokenizer.pad_token_id else -100) for tok in seq]
            for seq in labels["input_ids"]
        ]
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    train_tok = train_ds.map(preprocess, batched=True, remove_columns=train_ds.column_names)
    val_tok = val_ds.map(preprocess, batched=True, remove_columns=val_ds.column_names)

    collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    args = Seq2SeqTrainingArguments(
        output_dir="/kaggle/working/checkpoints",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-4,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=4,
        weight_decay=0.01,
        save_total_limit=2,
        predict_with_generate=True,
        logging_steps=25,
        load_best_model_at_end=True,
        report_to="none",
        fp16=True,
    )

    trainer = Seq2SeqTrainer(
        model=model, args=args,
        train_dataset=train_tok, eval_dataset=val_tok,
        data_collator=collator, tokenizer=tokenizer,
    )
    trainer.train()

    model.save_pretrained("/kaggle/working/model_out")
    tokenizer.save_pretrained("/kaggle/working/model_out")
    print("Saved fine-tuned model to /kaggle/working/model_out")


if __name__ == "__main__":
    main()