"""
NotebookLM が出力するテキストの前処理。
見出し・箇条書き・タイムスタンプを正規化して
解析エンジン が扱いやすい自然文に変換する。
"""
import re


# NotebookLM の典型的な見出しパターン
_HEADING_PATTERN = re.compile(r"^#{1,4}\s+", re.MULTILINE)

# 箇条書きマーカー（- / * / ・ / ● / 数字リスト）
_BULLET_PATTERN = re.compile(r"^\s*[-*・●]\s+|^\s*\d+[.)]\s+", re.MULTILINE)

# タイムスタンプ（例: [00:01:23] / 00:01:23 / (0:01)）
_TIMESTAMP_PATTERN = re.compile(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*")

# 連続する空白行を1行に
_BLANK_LINES_PATTERN = re.compile(r"\n{3,}")

# ラベル行（「発言者：」「話者A:」など）
_SPEAKER_LABEL_PATTERN = re.compile(r"^(話者\w*|発言者|interviewer|interviewee|応募者|面接官)\s*[：:]\s*", re.MULTILINE | re.IGNORECASE)


def preprocess(raw_text: str) -> str:
    """
    NotebookLM テキストを 解析エンジン 向けに正規化する。
    見出し・箇条書き・タイムスタンプを除去し、連続した自然文に変換する。
    """
    text = raw_text

    # タイムスタンプ除去
    text = _TIMESTAMP_PATTERN.sub("", text)

    # 話者ラベル除去
    text = _SPEAKER_LABEL_PATTERN.sub("", text)

    # Markdown 見出し記号を除去（テキストは残す）
    text = _HEADING_PATTERN.sub("", text)

    # 箇条書きマーカーを除去（テキストは残す）
    text = _BULLET_PATTERN.sub("", text)

    # 連続空行を圧縮
    text = _BLANK_LINES_PATTERN.sub("\n\n", text)

    # 各行の前後空白トリム
    lines = [line.strip() for line in text.splitlines()]

    # 空行で段落を区切り、段落内は句点で結合
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line:
            current.append(line)
        else:
            if current:
                paragraphs.append("".join(current))
                current = []
    if current:
        paragraphs.append("".join(current))

    return "\n".join(paragraphs).strip()
