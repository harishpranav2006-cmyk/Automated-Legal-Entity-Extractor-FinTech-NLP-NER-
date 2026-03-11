"""
train_bilstm.py — Akshada
Alternative deep-learning NER using TensorFlow Bi-LSTM + CRF.
Entities: PARTY, DATE, AMOUNT, JURISDICTION (BIO tagging scheme)

Usage:
    python src/ner/train_bilstm.py
"""

import json
import logging
import numpy as np
from pathlib import Path
from collections import defaultdict

import tensorflow as tf
from tensorflow.keras import layers, Model, optimizers
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
TRAIN_JSONL  = Path("data/annotated/train.jsonl")
DEV_JSONL    = Path("data/annotated/dev.jsonl")
MODEL_OUT    = Path("models/bilstm_ner")
GLOVE_PATH   = Path("models/glove.6B.100d.txt")   # Download separately if using GloVe

# ─── BIO Tag Set ───────────────────────────────────────────────────────────────
ENTITY_LABELS = ["PARTY", "DATE", "AMOUNT", "JURISDICTION"]

BIO_TAGS = ["O"] + [f"B-{l}" for l in ENTITY_LABELS] + [f"I-{l}" for l in ENTITY_LABELS]
TAG2IDX  = {tag: idx for idx, tag in enumerate(BIO_TAGS)}
IDX2TAG  = {idx: tag for tag, idx in TAG2IDX.items()}
NUM_TAGS = len(BIO_TAGS)

# ─── Hyperparameters ───────────────────────────────────────────────────────────
MAX_SEQ_LEN  = 128
EMBED_DIM    = 100
LSTM_UNITS   = 128
BATCH_SIZE   = 16
EPOCHS       = 20
LEARN_RATE   = 0.001
DROPOUT_RATE = 0.3


# ─── Helpers ──────────────────────────────────────────────────────────────────
def tokenize_and_tag(text: str, entities: list) -> tuple[list[str], list[str]]:
    """
    Simple whitespace tokenizer that assigns BIO tags based on char offsets.
    entities: [[start, end, label], ...]
    Returns (tokens, bio_tags)
    """
    tokens = []
    tags   = []
    words  = text.split()
    char_pos = 0

    # Build char-to-entity mapping
    char_labels = ["O"] * len(text)
    for start, end, label in entities:
        if label not in ENTITY_LABELS:
            continue
        char_labels[start] = f"B-{label}"
        for i in range(start + 1, end):
            char_labels[i] = f"I-{label}"

    for word in words:
        start = text.find(word, char_pos)
        if start == -1:
            tokens.append(word)
            tags.append("O")
            char_pos += len(word) + 1
            continue

        tag      = char_labels[start]
        char_pos = start + len(word)
        tokens.append(word)
        tags.append(tag if tag != "O" else "O")

    return tokens, tags


def load_jsonl(jsonl_path: Path) -> tuple[list, list]:
    """Loads JSONL and returns (all_token_seqs, all_tag_seqs)."""
    all_tokens = []
    all_tags   = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record   = json.loads(line)
            text     = record.get("text", "")
            entities = record.get("entities", [])
            tokens, tags = tokenize_and_tag(text, entities)
            all_tokens.append(tokens)
            all_tags.append(tags)

    logger.info(f"Loaded {len(all_tokens)} sequences from {jsonl_path.name}")
    return all_tokens, all_tags


def build_vocab(all_token_seqs: list) -> dict:
    """Builds word → index vocabulary from training tokens."""
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for seq in all_token_seqs:
        for token in seq:
            if token.lower() not in vocab:
                vocab[token.lower()] = len(vocab)
    logger.info(f"Vocabulary size: {len(vocab)}")
    return vocab


def encode_sequences(token_seqs, tag_seqs, word2idx, max_len=MAX_SEQ_LEN):
    """Converts token/tag sequences to padded integer arrays."""
    X = [[word2idx.get(t.lower(), 1) for t in seq] for seq in token_seqs]
    y = [[TAG2IDX.get(tag, 0)        for tag in seq] for seq in tag_seqs]

    X = pad_sequences(X, maxlen=max_len, padding="post", truncating="post", value=0)
    y = pad_sequences(y, maxlen=max_len, padding="post", truncating="post", value=0)
    y = np.expand_dims(y, -1)   # Shape: (batch, seq_len, 1) for sparse CE
    return X, y


def load_glove_embeddings(glove_path: Path, word2idx: dict, embed_dim: int = EMBED_DIM):
    """Loads GloVe vectors into an embedding matrix. Falls back to random if missing."""
    embed_matrix = np.random.uniform(-0.1, 0.1, (len(word2idx), embed_dim)).astype(np.float32)
    embed_matrix[0] = 0  # PAD → zero vector

    if not glove_path.exists():
        logger.warning(f"GloVe file not found at {glove_path}. Using random embeddings.")
        return embed_matrix

    loaded = 0
    with open(glove_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            word  = parts[0]
            if word in word2idx:
                embed_matrix[word2idx[word]] = np.array(parts[1:], dtype=np.float32)
                loaded += 1

    logger.info(f"Loaded {loaded}/{len(word2idx)} GloVe vectors.")
    return embed_matrix


# ─── Model Definition ─────────────────────────────────────────────────────────
def build_bilstm_model(vocab_size: int, embed_matrix: np.ndarray) -> Model:
    """
    Architecture:
      Input → Embedding (GloVe, frozen initially) → Bi-LSTM → Dropout → Dense (softmax)
    Note: tensorflow-addons CRF is optional; using softmax + sparse CE for portability.
    """
    inputs = layers.Input(shape=(MAX_SEQ_LEN,), name="token_ids")

    # Embedding layer (initialise with GloVe)
    x = layers.Embedding(
        input_dim=vocab_size,
        output_dim=EMBED_DIM,
        weights=[embed_matrix],
        trainable=True,          # Fine-tune embeddings
        mask_zero=True,
        name="token_embedding"
    )(inputs)

    # Bi-directional LSTM
    x = layers.Bidirectional(
        layers.LSTM(LSTM_UNITS, return_sequences=True, dropout=DROPOUT_RATE),
        name="bilstm"
    )(x)

    x = layers.Dropout(DROPOUT_RATE, name="dropout")(x)

    # Dense projection → tag probabilities
    outputs = layers.Dense(NUM_TAGS, activation="softmax", name="tag_output")(x)

    model = Model(inputs=inputs, outputs=outputs, name="BiLSTM_NER")
    model.compile(
        optimizer=optimizers.Adam(learning_rate=LEARN_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary(print_fn=logger.info)
    return model


# ─── Training Entry Point ─────────────────────────────────────────────────────
def train():
    # 1. Load data
    train_tokens, train_tags = load_jsonl(TRAIN_JSONL)
    dev_tokens,   dev_tags   = load_jsonl(DEV_JSONL)

    # 2. Build vocab
    word2idx = build_vocab(train_tokens)

    # 3. Encode
    X_train, y_train = encode_sequences(train_tokens, train_tags, word2idx)
    X_dev,   y_dev   = encode_sequences(dev_tokens,   dev_tags,   word2idx)

    # 4. Load embeddings
    embed_matrix = load_glove_embeddings(GLOVE_PATH, word2idx)

    # 5. Build model
    model = build_bilstm_model(vocab_size=len(word2idx), embed_matrix=embed_matrix)

    # 6. Callbacks
    MODEL_OUT.mkdir(parents=True, exist_ok=True)
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_OUT / "best_bilstm.h5"),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            verbose=1
        )
    ]

    # 7. Train
    logger.info("Starting Bi-LSTM training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_dev, y_dev),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    # 8. Save word2idx for inference
    import json
    with open(MODEL_OUT / "word2idx.json", "w") as f:
        json.dump(word2idx, f)
    with open(MODEL_OUT / "tag2idx.json", "w") as f:
        json.dump(TAG2IDX, f)

    logger.info(f"Bi-LSTM training complete. Model saved at {MODEL_OUT}")
    return history


if __name__ == "__main__":
    train()