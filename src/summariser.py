# src/summariser.py

from transformers import pipeline

# Create summarizer pipeline using DistilBART
# This model is small and runs well on CPU (your Intel i5)
summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6",
    tokenizer="sshleifer/distilbart-cnn-12-6"
)


def summarise(text: str,
              max_length: int = 130,
              min_length: int = 30) -> str:
    """
    Summarise long cybersecurity text using a lightweight transformer.
    If the text is too short, return it as-is.
    """

    if not text:
        return ""

    # If text is already short, no need to summarise
    if len(text.split()) < 40:
        return text.strip()

    try:
        result = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        return result[0]["summary_text"]

    except Exception:
        # In case the transformer fails for some input
        return text[:500]  # fallback — truncate
