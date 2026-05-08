"""
面接動画のAI解析サービス。
DeepFace で表情・感情を、Whisper で発話内容を解析する。
"""
import tempfile
import os
from pathlib import Path

import cv2
import numpy as np
import whisper

from app.models.candidate import EmotionProfile, SpeechProfile, VideoAnalysisResult

# キーワード辞書（発話テキストから特性を抽出）
_KEYWORD_MAPS = {
    "mentioned_night_shift": [
        "夜勤", "夜間", "泊まり", "ナイト", "深夜", "オールナイト",
    ],
    "mentioned_physical_care": [
        "身体介護", "入浴介助", "排泄介助", "移乗", "移動介助", "食事介助",
        "おむつ", "体位変換", "清拭",
    ],
    "mentioned_dementia": [
        "認知症", "グループホーム", "物忘れ", "徘徊", "BPSD", "アルツハイマー",
        "レビー小体",
    ],
    "mentioned_disability": [
        "障害", "就労支援", "B型", "A型", "移行支援", "生活介護",
        "精神", "知的", "身体障害", "発達",
    ],
    "mentioned_group_living": [
        "共同生活", "グループ", "一緒に", "チーム", "みんなで", "協力",
    ],
    "mentioned_activity": [
        "レクリエーション", "活動", "体操", "歌", "創作", "外出支援",
        "リハビリ", "運動", "ゲーム",
    ],
}

_CONFIDENCE_KEYWORDS = [
    "得意", "経験", "自信", "できます", "やってきました",
    "実績", "担当", "任されて",
]


def _extract_speech_features(transcript: str) -> dict:
    text_lower = transcript
    features: dict = {}
    for field, keywords in _KEYWORD_MAPS.items():
        features[field] = any(kw in text_lower for kw in keywords)

    confidence_hits = sum(1 for kw in _CONFIDENCE_KEYWORDS if kw in text_lower)
    features["confidence_score"] = min(confidence_hits / 3.0, 1.0)

    # 経験年数の簡易抽出（「○年」パターン）
    import re
    m = re.search(r"(\d+)\s*年", transcript)
    features["experience_years"] = int(m.group(1)) if m else None

    # キーワード抽出（名詞的な語句）
    all_kws = [kw for kws in _KEYWORD_MAPS.values() for kw in kws]
    features["keywords"] = [kw for kw in all_kws if kw in text_lower]

    return features


def _aggregate_emotions(frame_emotions: list[dict]) -> EmotionProfile:
    """複数フレームの感情スコアを集約してプロファイルを生成する。"""
    if not frame_emotions:
        return EmotionProfile(
            calm=0.5, empathy=0.5, energy=0.5,
            focus=0.5, adaptability=0.5, communication=0.5,
        )

    # DeepFace の感情ラベルを独自の特性にマッピング
    # DeepFace の出力: angry, disgust, fear, happy, sad, surprise, neutral
    totals = {e: 0.0 for e in ["calm", "empathy", "energy", "focus", "adaptability", "communication"]}
    n = len(frame_emotions)

    for fe in frame_emotions:
        neutral = fe.get("neutral", 0) / 100.0
        happy = fe.get("happy", 0) / 100.0
        angry = fe.get("angry", 0) / 100.0
        sad = fe.get("sad", 0) / 100.0
        surprise = fe.get("surprise", 0) / 100.0
        fear = fe.get("fear", 0) / 100.0

        totals["calm"] += neutral * 0.8 + (1 - angry - fear) * 0.2
        totals["empathy"] += happy * 0.6 + sad * 0.3 + neutral * 0.1
        totals["energy"] += happy * 0.7 + surprise * 0.3
        totals["focus"] += neutral * 0.7 + (1 - surprise) * 0.3
        totals["adaptability"] += (neutral + happy + surprise) / 3.0
        totals["communication"] += happy * 0.5 + neutral * 0.5

    return EmotionProfile(
        **{k: min(max(v / n, 0.0), 1.0) for k, v in totals.items()}
    )


async def analyze_video(video_path: str) -> VideoAnalysisResult:
    """
    動画ファイルを解析して VideoAnalysisResult を返す。
    1. DeepFace で表情・感情分析（サンプリングフレーム）
    2. Whisper で音声→テキスト変換＋特性抽出
    """
    try:
        from deepface import DeepFace
    except ImportError:
        DeepFace = None

    # --- 動画情報取得 ---
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 1
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    # --- 表情解析: 3秒おきにサンプリング ---
    frame_emotions: list[dict] = []
    sample_interval = max(1, int(fps * 3))

    for frame_idx in range(0, total_frames, sample_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue

        if DeepFace is not None:
            try:
                result = DeepFace.analyze(
                    frame,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )
                emotions = result[0]["emotion"] if isinstance(result, list) else result["emotion"]
                frame_emotions.append(emotions)
            except Exception:
                pass

    cap.release()

    emotion_profile = _aggregate_emotions(frame_emotions)
    analysis_confidence = min(len(frame_emotions) / max(total_frames / sample_interval, 1), 1.0)

    # --- 音声解析: Whisper ---
    model = whisper.load_model("base")
    whisper_result = model.transcribe(video_path, language="ja")
    transcript = whisper_result.get("text", "")

    speech_features = _extract_speech_features(transcript)
    speech_profile = SpeechProfile(
        transcript=transcript,
        keywords=speech_features.get("keywords", []),
        experience_years=speech_features.get("experience_years"),
        mentioned_night_shift=speech_features["mentioned_night_shift"],
        mentioned_physical_care=speech_features["mentioned_physical_care"],
        mentioned_dementia=speech_features["mentioned_dementia"],
        mentioned_disability=speech_features["mentioned_disability"],
        mentioned_group_living=speech_features["mentioned_group_living"],
        mentioned_activity=speech_features["mentioned_activity"],
        confidence_score=speech_features["confidence_score"],
    )

    return VideoAnalysisResult(
        emotion=emotion_profile,
        speech=speech_profile,
        video_duration_seconds=duration,
        analysis_confidence=max(analysis_confidence, 0.3),
    )
