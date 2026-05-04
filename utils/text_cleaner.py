import re


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_noise_markers(text: str) -> str:
    cleaned = text.replace("\u3000", " ").replace("\ufeff", " ")
    cleaned = cleaned.replace("###", " ").replace("***", " ")
    return normalize_whitespace(cleaned)


def clean_text(text: str) -> str:
    return strip_noise_markers(text)


def is_meaningful_text(text: str, min_length: int = 2) -> bool:
    return len(text.strip()) >= min_length