import re


# 归一化文本中的连续空白字符。
def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# 去除文本中的常见噪声标记。
def strip_noise_markers(text: str) -> str:
    cleaned = text.replace("\u3000", " ").replace("\ufeff", " ")
    cleaned = cleaned.replace("###", " ").replace("***", " ")
    return normalize_whitespace(cleaned)


# 执行文本清洗流程。
def clean_text(text: str) -> str:
    return strip_noise_markers(text)


# 判断清洗后的文本是否具备有效长度。
def is_meaningful_text(text: str, min_length: int = 2) -> bool:
    return len(text.strip()) >= min_length
