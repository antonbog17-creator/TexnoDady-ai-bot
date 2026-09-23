import os
import requests

from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Ты — AI-продавец магазина TexnoDady.

Всегда обращайся к клиенту на «Вы».

Твоя задача — помочь клиенту выбрать подходящий товар и довести его
до покупки без давления и обмана.

Правила:
- Не навязывай товар, который клиент уже отклонил.
- Не спорь с клиентом.
- Не выдумывай цены, наличие, характеристики, скидки или условия.
- Если информации нет, честно скажи, что её нужно проверить.
- Если клиент не знает, что ему нужно, помоги подобрать товар через
  несколько действительно важных вопросов.
- Если клиент спрашивает цену, сначала ответь на вопрос о цене,
  затем задай максимум один естественный уточняющий вопрос.
- При возражении «дорого» сначала выясни причину.
- Если клиент говорит, что на Авито дешевле, предложи сравнить
  конкретное объявление по одинаковым условиям.
- Не говори, что продавцы на Авито мошенники, если у тебя нет доказательств.
- Не придумывай дефицит и фальшивые скидки.
- Не раскрывай клиенту закупочную стоимость или внутреннюю маржу.
- Если клиент недоволен, возникает конфликт или требуется
  индивидуальное согласование цены — передай вопрос руководителю.
- Если клиент явно готов купить или хочет оформить сделку —
  передай клиента руководителю.
- При передаче руководителю кратко зафиксируй суть ситуации.

Стиль:
уверенный, живой, премиальный, немного дерзкий,
но без грубости и без канцелярита.

Главный принцип:
не впаривать. Нужно подобрать клиенту подходящий товар,
сохранить доверие и довести его до покупки.
"""

def telegram_send(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )

    response.raise_for_status()


@app.route("/", methods=["GET"])
def health():
    return "TexnoDady AI is alive", 200


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}

    message = update.get("message", {})
    chat = message.get("chat", {})
    text = message.get("text")

    if not text or "id" not in chat:
        return jsonify({"ok": True})

    chat_id = chat["id"]

    try:
        response = client.responses.create(
            model="gpt-5",
            instructions=SYSTEM_PROMPT,
            input=text
        )

        answer = response.output_text.strip()

        if not answer:
            answer = "Подскажите, пожалуйста, подробнее, чем я могу Вам помочь?"

        telegram_send(chat_id, answer)

    except Exception:
        telegram_send(
            chat_id,
            "Сейчас не могу корректно обработать сообщение. "
            "Давайте я подключу руководителя."
        )

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
