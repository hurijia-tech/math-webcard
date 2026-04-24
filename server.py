"""
수학 아카이브 로컬 서버
- cards_data.json 서빙
- /save-type API로 question_type 변경 저장
실행: python server.py
접속: http://localhost:8000
"""
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "cards_data.json"


class ArchiveHandler(SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path == "/save-type":
            # 형태 변경 저장 API
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                card_id = payload.get("id")
                new_type = payload.get("question_type")

                if not card_id or not new_type:
                    self._respond(400, {"error": "id와 question_type이 필요합니다"})
                    return

                # JSON 읽기
                with open(DATA_FILE, encoding="utf-8-sig") as f:
                    cards = json.load(f)

                # 해당 카드 업데이트
                updated = False
                for card in cards:
                    if card["id"] == card_id:
                        card["question_type"] = new_type
                        updated = True
                        break

                if not updated:
                    self._respond(404, {"error": f"카드를 찾을 수 없음: {card_id}"})
                    return

                # JSON 저장
                with open(DATA_FILE, "w", encoding="utf-8-sig") as f:
                    json.dump(cards, f, ensure_ascii=False, indent=2)

                self._respond(200, {"ok": True, "id": card_id, "question_type": new_type})
                print(f"  ✅ 저장: {card_id} → {new_type}")

            except Exception as e:
                self._respond(500, {"error": str(e)})
        else:
            self._respond(404, {"error": "Not found"})

    def _respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # GET 요청 로그는 숨기고 중요한 것만 출력
        if args and str(args[0]).startswith("POST"):
            print(f"  [{self.address_string()}] {format % args}")


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    print(f"🚀 수학 아카이브 서버 시작")
    print(f"   주소: http://localhost:{PORT}")
    print(f"   폴더: {BASE_DIR}")
    print(f"   종료: Ctrl+C\n")
    server = HTTPServer(("localhost", PORT), ArchiveHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료")
