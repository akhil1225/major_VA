import pandas as pd
import numpy as np
import pickle

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

from tensorflow.keras.preprocessing.text import Tokenizer #type:ignore
from tensorflow.keras.preprocessing.sequence import pad_sequences #type:ignore
from tensorflow.keras.models import Sequential #type:ignore
from tensorflow.keras.layers import Embedding, Dense, Dropout, Bidirectional, LSTM #type:ignore
from tensorflow.keras.utils import to_categorical #type:ignore
from tensorflow.keras.callbacks import EarlyStopping #type:ignore


TF_ENABLED_ONEDNN_OPTS = 0

data = pd.read_csv("data/commands.csv")

X = data["sentence"].astype(str).values
y = data["intent"].values



label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y) #type:ignore
y_cat = to_categorical(y_encoded)



X_train, X_test, y_train, y_test = train_test_split(
    X, y_cat,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)


vocab_size = 6000
max_len = 25

tokenizer = Tokenizer(num_words=vocab_size, oov_token="<OOV>")
tokenizer.fit_on_texts(X_train)

X_train_seq = tokenizer.texts_to_sequences(X_train)
X_test_seq = tokenizer.texts_to_sequences(X_test)

X_train_pad = pad_sequences(X_train_seq, maxlen=max_len, padding="post")
X_test_pad = pad_sequences(X_test_seq, maxlen=max_len, padding="post")



model = Sequential([
    Embedding(vocab_size, 128, input_length=max_len),
    Bidirectional(LSTM(64, return_sequences=False)),
    Dropout(0.5),
    Dense(64, activation="relu"),
    Dense(y_cat.shape[1], activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)



early_stop = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)

model.fit(
    X_train_pad,
    y_train,
    epochs=50,
    batch_size=8,
    validation_split=0.15,
    callbacks=[early_stop],
    verbose=1
)


y_pred = model.predict(X_test_pad)
y_pred_labels = np.argmax(y_pred, axis=1)
y_true_labels = np.argmax(y_test, axis=1)

acc = accuracy_score(y_true_labels, y_pred_labels)

print("Model Accuracy:", acc)
print("\nClassification Report:\n",
      classification_report(
          label_encoder.inverse_transform(y_true_labels),
          label_encoder.inverse_transform(y_pred_labels)
      )
)


model.save("core/intent_model_dl.keras")


with open("core/tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

with open("core/label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)

print("BiLSTM model saved in core/")
