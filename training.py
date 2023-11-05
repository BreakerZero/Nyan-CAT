import os
from evaluate import load
from datasets import load_dataset, load_metric
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer
import numpy as np
os.environ["WANDB_DISABLED"] = "true"
prefix = ""
max_input_length = 128
max_target_length = 128
batch_size = 16
metric = load("sacrebleu")


def preprocess_function(examples):
    inputs = examples[source_lang]
    targets = examples[target_lang]
    model_inputs = tokenizer(inputs, max_length=max_input_length, truncation=True)
    # Setup the tokenizer for targets
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(targets, max_length=max_target_length, truncation=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def postprocess_text(preds, labels):
    preds = [pred.strip() for pred in preds]
    labels = [[label.strip()] for label in labels]
    return preds, labels


def compute_metrics(eval_preds):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    # Replace -100 in the labels as we can't decode them.
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    # Some simple post-processing
    decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)
    result = metric.compute(predictions=decoded_preds, references=decoded_labels)
    result = {"bleu": result["score"]}
    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
    result["gen_len"] = np.mean(prediction_lens)
    result = {k: round(v, 4) for k, v in result.items()}
    return result

def Training(id, Source_Lang, Target_Lang):
    cwd = os.getcwd()
    model_checkpoint = str(cwd) + "\\translatemodel\\opus-mt-"+Source_Lang+"-"+Target_Lang+"\\"
    model_name = model_checkpoint.split("/")[-1]
    global source_lang
    global target_lang
    global tokenizer
    source_lang = Source_Lang
    target_lang = Target_Lang
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    path = str(cwd) + "\\static\\csv\\memory" + str(id) + ".csv"
    raw_datasets = load_dataset("csv", data_files=path, delimiter=";", encoding="1252")
    tokenized_datasets = raw_datasets.map(preprocess_function, batched=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)
    args = Seq2SeqTrainingArguments(
        model_checkpoint,
        learning_rate=2e-5,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        weight_decay=0.01,
        save_total_limit=3,
        num_train_epochs=1,
        predict_with_generate=True
    )
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model,
        args,
        train_dataset=tokenized_datasets["train"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )
    trainer.train()
    trainer.save_model(model_checkpoint)
    os.remove("static/csv/memory" + str(id) + ".csv")