import os
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

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Nedostaje TELEGRAM_TOKEN environment varijabla")

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

def generate_game_structure(keywords: str, retries: int = 2) -> dict:
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

OPISI OPCIJA:
- Maksimalno 2 rečenice.
- Ton: nježan, introspektivan, poetičan.
- Bez eksplicitnog sadržaja.

FORMAT:
- Vrati isključivo validan JSON.
- Bez markdowna, bez objašnjenja.

JSON FORMAT:

{
  "title": "string",
  "questions": [
    {
      "question": "string",
      "options": ["string", "string", "string"],
      "descriptions": ["string", "string", "string"]
    }
  ]
}
"""

    for attempt in range(retries + 1):
        response = client.chat.completions.create(
			model="gpt-4o-mini",
			response_format={"type": "json_object"},
			messages=[
				{"role": "system", "content": "Ti si precizan generator poetskih struktura i vraćaš isključivo validan JSON."},
				{"role": "user", "content": prompt},
			],
		)


        data = json.loads(response.choices[0].message.content)

        try:
            data = json.loads(content)

            if len(data.get("questions", [])) != 10:
                raise ValueError("Pogrešan broj pitanja")

            return data

        except Exception as e:
            if attempt == retries:
                raise RuntimeError("GPT vratio nevalidan JSON") from e


# =====================
# GPT – KONAČNA PRIČA
# =====================

def build_story(answers: list, keywords: str) -> str:
    answers_text = "\n".join(f"- {a}" for a in answers)

    prompt = f"""
Na osnovu sljedećih ključnih riječi:

{keywords}

i sljedećih emotivnih izbora korisnika:

{answers_text}

Napiši završnu priču.

PRAVILA:
- Jezik: bosanski
- 10 do 15 rečenica
- Stil: lično pismo (obraćanje sa "ti")
- Ton: nježan, introspektivan
- Bez naslova
- Bez objašnjenja
- Bez markdowna

Vrati samo tekst priče.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ti si književni pisac intimne poezije u prozi na bosanskom jeziku."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# =====================
# TELEGRAM HANDLERI
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = "WAITING_KEYWORDS"

    await update.message.reply_text(
        "Počinje nova igra.\n\nUnesi ključne riječi ili misli."
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
    if context.user_data.get("locked"):
        return

    state = context.user_data.get("state")
    text = update.message.text.strip()

    if state is None:
        await update.message.reply_text("Za početak napiši /start")
        return

    if state == "WAITING_KEYWORDS":
        context.user_data["locked"] = True

        try:
            game = generate_game_structure(text)
        except Exception:
            context.user_data["locked"] = False
            await update.message.reply_text("Došlo je do greške. Pokušaj ponovo.")
            return

        context.user_data["keywords"] = text
        context.user_data["title"] = game["title"]
        context.user_data["questions"] = game["questions"]
        context.user_data["q_index"] = 0
        context.user_data["answers"] = []
        context.user_data["state"] = "IN_GAME"
        context.user_data["locked"] = False

        await update.message.reply_text(game["title"])
        await send_question(update, context)
        return

    if state == "IN_GAME":
        if text not in ("1", "2", "3"):
            await update.message.reply_text("Unesi 1, 2 ili 3.")
            return

        choice = int(text) - 1
        q_index = context.user_data["q_index"]
        q = context.user_data["questions"][q_index]

        desc = q["descriptions"][choice]
        context.user_data["answers"].append(desc)

        # === OVDJE JE PROMJENA ===
        # Prikaži samo opis, bez "Odabrao si:"
        await update.message.reply_text(desc)

        context.user_data["q_index"] += 1

        if context.user_data["q_index"] >= 10:
            context.user_data["locked"] = True

            story = build_story(
                context.user_data["answers"],
                context.user_data["keywords"]
            )

            context.user_data["locked"] = False

            title_upper = context.user_data.get("title", "").upper()

            final_text = f"{title_upper}\n\n{story}"

            await update.message.reply_text(
                final_text,
                reply_markup=inline_menu()
            )

            context.user_data["state"] = "END"
            return

        await send_question(update, context)


# =====================
# INLINE MENU HANDLER
# =====================

async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "NEW_GAME":
        context.user_data.clear()
        context.user_data["state"] = "WAITING_KEYWORDS"
        await query.edit_message_text("Počinje nova igra.\n\nUnesi ključne riječi ili misli.")

    elif query.data == "END":
        await query.edit_message_text("Hvala ti na igri.")
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
