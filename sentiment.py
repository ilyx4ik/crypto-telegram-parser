from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_NAME = "ProsusAI/finbert"

print("Загрузка модели FinBERT...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)


def analyze_sentiment(text: str) -> str:
    try:
        inputs = tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=512
        )

        with torch.no_grad():
            outputs = model(**inputs)

        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        label_id = torch.argmax(predictions).item()

        labels = ["Positive 🚀", "Negative 📉", "Neutral ⚖️"]
        return labels[label_id]
    except Exception as e:
        print(f"Ошибка при анализе сентимента: {e}")
        return "Neutral ⚖️"


if __name__ == "__main__":
  test_text = "Bitcoin price surges after historic approval of new spot ETF"
  result = analyze_sentiment(test_text)
  print(f"Новость: {test_text}\nСентимент: {result}")