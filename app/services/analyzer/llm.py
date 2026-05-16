"""
オンプレLLMを使った解析エンジン（スタブ）。

実装は未完了。設定で analyzer_engine="llm" に切り替えた時、
ここを実装すれば LLM 経由の構造化抽出が動く。

## 想定する接続先
- Ollama: http://localhost:11434  (デフォルト)
- vLLM:   OpenAI 互換エンドポイント

## 実装時にやること
1. settings.llm_endpoint / settings.llm_model を読み込む
2. プロンプトでテキストから以下を JSON で抽出させる:
   {
     "trait": { "calm": 0.0-1.0, ... },
     "features": {
       "mentioned_night_shift": bool,
       "experience_years": int | null, ...
     }
   }
3. JSON をパースして TextAnalysisResult を返す
4. 失敗時は KeywordAnalyzer にフォールバック
"""
from app.models.candidate import TextAnalysisResult
from app.services.analyzer.base import AnalyzerEngine


# LLM への指示プロンプト（実装時に使用）
SYSTEM_PROMPT = """あなたは介護分野の採用面接を分析するエキスパートです。
与えられた面接テキストから応募者の特性を客観的に評価し、
以下のJSON形式で必ず出力してください。

{
  "trait": {
    "calm": 穏やかさ・安定性 (0.0-1.0),
    "empathy": 共感力・温かさ (0.0-1.0),
    "energy": 活動性・明るさ (0.0-1.0),
    "focus": 集中力・真面目さ (0.0-1.0),
    "adaptability": 柔軟性・適応力 (0.0-1.0),
    "communication": コミュニケーション力 (0.0-1.0)
  },
  "features": {
    "mentioned_night_shift": 夜勤への前向きな意向があるか (boolean),
    "mentioned_physical_care": 身体介護への言及・経験があるか (boolean),
    "mentioned_dementia": 認知症ケアへの理解・関心があるか (boolean),
    "mentioned_disability": 障害福祉への言及・関心があるか (boolean),
    "mentioned_group_living": 少人数・共同生活環境への適性があるか (boolean),
    "mentioned_activity": レクリエーション・活動支援への関心があるか (boolean),
    "experience_years": 介護経験年数 (integer または null),
    "confidence_score": 発言の自信度 (0.0-1.0),
    "keywords": ["抽出した重要キーワード"]
  },
  "analysis_confidence": 解析の信頼度 (0.0-1.0)
}

重要:
- 否定形（「夜勤はできない」「認知症は苦手」）は false として扱うこと
- テキストにない情報は推測せず保守的にスコアリングすること
- JSON のみ出力し、他の説明文は付けないこと
"""


class LLMAnalyzer(AnalyzerEngine):
    """オンプレLLM経由の解析エンジン（未実装スタブ）。"""

    name = "llm"

    def __init__(self, endpoint: str, model: str, timeout: int):
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    def analyze(self, text: str) -> TextAnalysisResult:
        raise NotImplementedError(
            "LLMAnalyzer は未実装です。"
            "オンプレ LLM 環境 (Ollama / vLLM) 構築後に実装してください。"
            "現状は settings.analyzer_engine='keyword' を使用してください。"
        )

    def healthcheck(self) -> bool:
        # 実装時: requests で /api/tags や /health を叩いて疎通確認
        return False
