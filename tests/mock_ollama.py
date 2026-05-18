"""
統合テスト用のモック Ollama サーバー。
実際の Ollama と同じ API エンドポイントを持ち、
キーワード方式で生成した結果を JSON で返す。

実機で Ollama + llama3.2:3b を使う場合のフローを
ネットワーク不要で再現する。
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.services.analyzer.keyword import KeywordAnalyzer

_keyword_analyzer = KeywordAnalyzer()


class _OllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # テスト時はログを抑制

    def do_GET(self):
        if self.path == "/api/tags":
            body = json.dumps({
                "models": [{"name": "llama3.2:3b"}]
            }).encode()
            self._send(200, body)
        else:
            self._send(404, b'{}')

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            payload = json.loads(raw)

            # プロンプトから面接テキスト部分を抽出
            prompt = payload.get("prompt", "")
            marker = "【面接テキスト】"
            interview_text = prompt.split(marker)[-1].strip() if marker in prompt else prompt

            # キーワード方式で解析してモックレスポンスを生成
            result = _keyword_analyzer.analyze(interview_text)

            response_json = {
                "trait": {
                    "calm": result.trait.calm,
                    "empathy": result.trait.empathy,
                    "energy": result.trait.energy,
                    "focus": result.trait.focus,
                    "adaptability": result.trait.adaptability,
                    "communication": result.trait.communication,
                },
                "features": {
                    "mentioned_night_shift": result.features.mentioned_night_shift,
                    "mentioned_physical_care": result.features.mentioned_physical_care,
                    "mentioned_dementia": result.features.mentioned_dementia,
                    "mentioned_disability": result.features.mentioned_disability,
                    "mentioned_group_living": result.features.mentioned_group_living,
                    "mentioned_activity": result.features.mentioned_activity,
                    "experience_years": result.features.experience_years,
                    "confidence_score": result.features.confidence_score,
                    "keywords": result.features.keywords,
                },
                "analysis_confidence": result.analysis_confidence,
            }
            body = json.dumps({
                "model": payload.get("model", "llama3.2:3b"),
                "response": json.dumps(response_json, ensure_ascii=False),
                "done": True,
            }).encode()
            self._send(200, body)
        else:
            self._send(404, b'{}')

    def _send(self, code: int, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class MockOllamaServer:
    """テスト用モック Ollama サーバー。"""

    def __init__(self, host: str = "127.0.0.1", port: int = 11435):
        self.host = host
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self):
        self._server = HTTPServer((self.host, self.port), _OllamaHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
