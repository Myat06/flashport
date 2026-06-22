"""
Train spaCy NER model for customs document field extraction.

Reads:  data/ner_training.spacy
Writes: models/ner_model/   (spaCy model directory)

Usage:
    cd backend && source venv/bin/activate
    python scripts/train_ner_model.py
"""
import random
from pathlib import Path

import spacy
from spacy.tokens import DocBin
from spacy.training import Example

LABELS = [
    "HS_CODE", "INVOICE_VALUE", "CONTAINER_ID", "IMPORTER", "EXPORTER",
    "NET_WEIGHT", "GROSS_WEIGHT", "VESSEL_NAME", "PORT_OF_ORIGIN",
    "INVOICE_NUMBER", "CARTON_COUNT",
]

DATA_PATH  = Path(__file__).parent.parent / "data" / "ner_training.spacy"
MODEL_PATH = Path(__file__).parent.parent / "models" / "ner_model"


def load_data(path: Path, nlp) -> list[Example]:
    db = DocBin().from_disk(str(path))
    examples = []
    for doc in db.get_docs(nlp.vocab):
        example = Example(nlp.make_doc(doc.text), doc)
        examples.append(example)
    return examples


def train():
    print("Loading base model (en_core_web_sm)...")
    nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])

    # Add NER if not present
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    for label in LABELS:
        ner.add_label(label)

    print(f"Loading training data from {DATA_PATH}...")
    examples = load_data(DATA_PATH, nlp)
    print(f"  {len(examples)} examples loaded")

    # Split 80/20
    random.seed(42)
    random.shuffle(examples)
    split = int(len(examples) * 0.8)
    train_data = examples[:split]
    dev_data   = examples[split:]
    print(f"  Train: {len(train_data)}  Dev: {len(dev_data)}")

    # Freeze all pipes except NER
    other_pipes = [p for p in nlp.pipe_names if p != "ner"]
    print(f"\nTraining NER (freezing: {other_pipes})...")

    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.resume_training()
        optimizer.learn_rate = 0.001

        best_f1 = 0.0
        patience = 0

        for iteration in range(40):
            random.shuffle(train_data)
            losses = {}
            batches = spacy.util.minibatch(train_data, size=spacy.util.compounding(4.0, 32.0, 1.001))
            for batch in batches:
                nlp.update(batch, sgd=optimizer, drop=0.3, losses=losses)

            # Evaluate on dev set
            scores = nlp.evaluate(dev_data)
            ents_f = scores.get("ents_f", 0)
            ents_p = scores.get("ents_p", 0)
            ents_r = scores.get("ents_r", 0)

            if (iteration + 1) % 5 == 0 or iteration == 0:
                print(f"  Iter {iteration+1:3d}  loss={losses.get('ner',0):.3f}  "
                      f"P={ents_p:.3f}  R={ents_r:.3f}  F1={ents_f:.3f}")

            if ents_f > best_f1:
                best_f1 = ents_f
                patience = 0
                MODEL_PATH.mkdir(parents=True, exist_ok=True)
                nlp.to_disk(str(MODEL_PATH))
            else:
                patience += 1
                if patience >= 8:
                    print(f"  Early stop at iter {iteration+1} — best F1={best_f1:.3f}")
                    break

    print(f"\nBest F1: {best_f1:.3f}")
    print(f"Model saved to {MODEL_PATH}")

    # Per-entity scores on dev
    print("\nPer-entity F1 on dev set:")
    best_nlp = spacy.load(str(MODEL_PATH))
    from collections import defaultdict
    tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
    for ex in dev_data:
        pred = best_nlp(ex.reference.text)
        gold_ents = {(e.start_char, e.end_char, e.label_) for e in ex.reference.ents}
        pred_ents = {(e.start_char, e.end_char, e.label_) for e in pred.ents}
        for e in pred_ents:
            if e in gold_ents: tp[e[2]] += 1
            else:              fp[e[2]] += 1
        for e in gold_ents:
            if e not in pred_ents: fn[e[2]] += 1
    print(f"  {'Entity':22} {'F1':>6}")
    for label in sorted(LABELS):
        p = tp[label] / (tp[label]+fp[label]) if tp[label]+fp[label] else 0
        r = tp[label] / (tp[label]+fn[label]) if tp[label]+fn[label] else 0
        f1 = 2*p*r/(p+r) if p+r else 0
        bar = "█" * int(f1 * 20)
        print(f"  {label:22} {f1:>6.3f}  {bar}")

    print(f"\nDone. Load with: nlp = spacy.load('{MODEL_PATH}')")


if __name__ == "__main__":
    train()
