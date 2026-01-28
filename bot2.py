import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# =====================
# KONFIGURACIJA
# =====================

import os
TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI()

# =====================
# INLINE MENI
# =====================

def inline_menu():
    keyboard = [
        [
            InlineKeyboardButton("Nova igra", callback_data="NEW_GAME"),
            InlineKeyboardButton("Kraj", callback_data="END"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# =====================
# GPT – GENERACIJA IGRE
# =====================

def generate_game_structure(keywords: str) -> dict:
    prompt = f"""
Na osnovu sljedećih ključnih riječi:

{keywords}

Kreiraj poetsku i intimnu strukturu interaktivne igre.

OBAVEZNA PRAVILA:

JEZIK:
- Svi tekstovi moraju biti isključivo na bosanskom jeziku.

SADRŽAJ:
- Kreiraj tačno jedan naslov igre.
- Kreiraj tačno 10 pitanja.
- Svako pitanje mora imati tačno 3 opcije.
- Opcije moraju biti:
  - stvarne riječi ili kratke fraze
  - emotivne, simbolične ili gestualne
  - bez slova (a, b, c)
  - bez brojeva
  - bez interpunkcijskih oznaka kao sadržaja

OPISI OPCIJA:
- Svaka opcija mora imati vlastiti opis.
- Opis maksimalno 2 rečenice.
- Ton: nježan, introspektivan, poetičan.
- Bez eksplicitnog sadržaja.

FORMAT:
- Ne koristi markdown.
- Ne dodaj komentare.
- Ne dodaj objašnjenja.
- Ne dodaj tekst izvan JSON strukture.
- Vrati isključivo validan JSON objekt.

JSON STRUKTURA (mora se tačno poštovati):

{{
  "title": "string",
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string", "string"],
      "descriptions": ["string", "string", "string"]
    }}
  ]
}}

DODATNA PRAVILA VALIDACIJE:

- Polje "questions" mora imati tačno 10 elemenata.
- Svaki element mora imati tačno 3 opcije i 3 opisa.
- Broj opcija mora odgovarati broju opisa.
- Ne koristiti prazne stringove.
- Ne koristiti null vrijednosti.

Vrati isključivo JSON.
"""


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ti si precizan generator poetskih struktura."},
            {"role": "user", "content": prompt},
        ],
    )

    return json.loads(response.choices[0].message.content)

# =====================
# GPT – KONAČNA PRIČA
# =====================

def build_story(answers: list, keywords: str) -> str:
    prompt = (
        "Na osnovu sljedećih ključnih riječi:\n"
        f"{keywords}\n\n"
        "i sljedećih emotivnih izbora:\n"
        + "\n".join(answers) +
        "\n\nNapiši poetsku, intimnu priču od 10–15 rečenica. "
        "Jezik: bosanski. Ton: nježan, introspektivan."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Pišeš poetično na bosanskom jeziku."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content.strip()

# =====================
# TELEGRAM HANDLERJI
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = "WAITING_KEYWORDS"

    await update.message.reply_text(
        "Počinje nova igra.\n\n"
        "Unesi ključne riječi ili misli."
    )

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data["q_index"]
    q = context.user_data["questions"][q_index]

    text = (
        f"{q_index + 1}. {q['question']}\n"
        f"a) {q['options'][0]}\n"
        f"b) {q['options'][1]}\n"
        f"c) {q['options'][2]}\n\n"
        "Unesi: 1, 2 ili 3."
    )

    await update.message.reply_text(text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    text = update.message.text.strip()

    if state is None:
        await update.message.reply_text("Za početak napiši /start")
        return

    # =====================
    # UNOS KLJUČNIH RIJEČI
    # =====================

    if state == "WAITING_KEYWORDS":
        context.user_data["keywords"] = text

        game = generate_game_structure(text)

        context.user_data["title"] = game["title"]
        context.user_data["questions"] = game["questions"]
        context.user_data["q_index"] = 0
        context.user_data["answers"] = []
        context.user_data["state"] = "IN_GAME"

        await update.message.reply_text(
            game["title"]
        )

        await send_question(update, context)
        return

    # =====================
    # TOK IGRE
    # =====================

    if state == "IN_GAME":
        if text not in ("1", "2", "3"):
            await update.message.reply_text("Unesi 1, 2 ili 3.")
            return

        choice = int(text) - 1
        q_index = context.user_data["q_index"]
        q = context.user_data["questions"][q_index]

        desc = q["descriptions"][choice]
        context.user_data["answers"].append(desc)

        await update.message.reply_text(
            f'"{desc}"'
        )

        context.user_data["q_index"] += 1

        if context.user_data["q_index"] >= 10:
            story = build_story(
                context.user_data["answers"],
                context.user_data["keywords"]
            )

            await update.message.reply_text(
                "KONAČNA PRIČA:\n\n" + story,
                reply_markup=inline_menu()
            )

            context.user_data["state"] = "END"
            return

        await send_question(update, context)
        return

# =====================
# INLINE MENU HANDLER
# =====================

async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "NEW_GAME":
        await start(query, context)

    if query.data == "END":
        await query.edit_message_text("Hvala ti na igri 👋")
        context.user_data.clear()

# =====================
# MAIN
# =====================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_menu_click))

    print("Bot radi...")
    app.run_polling()

if __name__ == "__main__":
    main()
