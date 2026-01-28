from openai import OpenAI
client = OpenAI()
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8585359399:AAFCCa0cudK9J4xpeh_2BvcxcUGuAge0FHw"


QUESTIONS = [
    {
        "sl": {
            "question": "Ko te sanje potegnejo stran, kaj narediš?",
            "options": ["Ustavim se", "Zbežim", "Zaprem oči"],
            "descriptions": [
                "Obstaneš za hip, kot da poslušaš tišino v sebi.",
                "Noge te odnesejo proč, še preden misli dohajajo korak.",
                "Tema postane mehka, misli pa počasnejše.",
            ],
        },
        "bs": {
            "question": "Kad te snovi povuku dalje, šta učiniš?",
            "options": ["Zastanem", "Pobjegnem", "Zatvorim oči"],
            "descriptions": [
                "Zastaneš na trenutak, kao da slušaš tišinu u sebi.",
                "Noge te nose dalje prije nego misli stignu.",
                "Tama postane mekša, a misli sporije.",
            ],
        },
    },
    {
        "sl": {
            "question": "Kaj v tebi ostane najdlje?",
            "options": ["Utrujenost", "Jeza", "Tišina"],
            "descriptions": [
                "Utrujenost se uleže globoko, brez upora.",
                "Jeza se skriva, a ne izgine.",
                "Tišina počasi prevzame prostor.",
            ],
        },
        "bs": {
            "question": "Šta u tebi ostane najduže?",
            "options": ["Umor", "Bijes", "Tišina"],
            "descriptions": [
                "Umor se smjesti duboko, bez otpora.",
                "Bijes se sakrije, ali ne nestane.",
                "Tišina polako preuzme prostor.",
            ],
        },
    },
    {
        "sl": {
            "question": "Kako se želiš vrniti k sebi?",
            "options": ["Počasi", "Brez besed", "Skozi sanje"],
            "descriptions": [
                "Korak za korakom, brez pritiska.",
                "Brez razlage, samo z občutkom.",
                "Sanje odprejo pot nazaj.",
            ],
        },
        "bs": {
            "question": "Kako se želiš vratiti sebi?",
            "options": ["Polako", "Bez riječi", "Kroz snove"],
            "descriptions": [
                "Korak po korak, bez pritiska.",
                "Bez objašnjenja, samo s osjećajem.",
                "Snovi otvore put nazad.",
            ],
        },
    },
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = "WAITING_KEYWORDS"

    await update.message.reply_text(
        "Začenjava novo igro.\n\n"
        "Vnesi ključne besede ali misli."
    )


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data["q_index"]
    q = QUESTIONS[q_index]

    text = (
        f"{q_index + 1}. {q['sl']['question']}\n"
        f"a) {q['sl']['options'][0]}\n"
        f"b) {q['sl']['options'][1]}\n"
        f"c) {q['sl']['options'][2]}\n\n"
        f"{q_index + 1}. {q['bs']['question']}\n"
        f"a) {q['bs']['options'][0]}\n"
        f"b) {q['bs']['options'][1]}\n"
        f"c) {q['bs']['options'][2]}\n\n"
        "Vpiši / Unesi: 1, 2, 3."
    )

    await update.message.reply_text(text)


def build_story(answers_sl, answers_bs, keywords):
    prompt = (
        "Na podlagi ključnih besed:\n"
        f"{keywords}\n\n"
        "in izbranih čutnih odzivov (slovenščina):\n"
        + "\n".join(answers_sl) +
        "\n\nUstvari poetično, intimno zgodbo dolgo 10–15 stavkov. "
        "Ton naj bo nežen, introspektiven, brez eksplicitnosti."
    )

    resp_sl = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Si poetičen pripovedovalec."},
            {"role": "user", "content": prompt},
        ],
    )
    story_sl = resp_sl.choices[0].message.content.strip()

    resp_bs = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Prevedi v bosanščino, poetično."},
            {"role": "user", "content": story_sl},
        ],
    )
    story_bs = resp_bs.choices[0].message.content.strip()

    return story_sl, story_bs



async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    text = update.message.text.strip()

    if state is None:
        await update.message.reply_text("Za začetek napiši /start")
        return

    if state == "WAITING_KEYWORDS":
        context.user_data["keywords"] = text
        context.user_data["state"] = "IN_GAME"
        context.user_data["q_index"] = 0
        context.user_data["answers"] = []

        await update.message.reply_text(
            f"Shranjene ključne besede:\n{text}\n"
        )

        await send_question(update, context)
        return

    if state == "IN_GAME":
        if text not in ("1", "2", "3"):
            await update.message.reply_text("Vpiši 1, 2 ali 3.")
            return

        choice = int(text) - 1
        q_index = context.user_data["q_index"]
        q = QUESTIONS[q_index]

        sl_desc = q["sl"]["descriptions"][choice]
        bs_desc = q["bs"]["descriptions"][choice]

        context.user_data["answers"].append((sl_desc, bs_desc))

        await update.message.reply_text(
            f'Možnost {text} – "{sl_desc}"\n'
            f'Opcija {text} – "{bs_desc}"'
        )

        context.user_data["q_index"] += 1

        if context.user_data["q_index"] >= len(QUESTIONS):
            answers_sl = [a[0] for a in context.user_data["answers"]]
            answers_bs = [a[1] for a in context.user_data["answers"]]

            story_sl, story_bs = build_story(
				answers_sl,
				answers_bs,
				context.user_data["keywords"]
			)


            await update.message.reply_text(
                "\nZBRANI ODGOVORI (SL):\n" + "\n".join(answers_sl)
            )
            await update.message.reply_text(
                "\nZBRANI ODGOVORI (BS):\n" + "\n".join(answers_bs)
            )

            await update.message.reply_text(
                "\nKONČNA ZGODBA (SL):\n" + story_sl
            )
            await update.message.reply_text(
                "\nKONAČNA PRIČA (BS):\n" + story_bs
            )

            await update.message.reply_text(
                "\n1. Nova igra\n2. Konec"
            )

            context.user_data["state"] = "END"
            return

        await send_question(update, context)
        return

    if state == "END":
        if text == "1":
            await start(update, context)
        else:
            await update.message.reply_text("Hvala za igro.")
        return


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot teče...")
    app.run_polling()


if __name__ == "__main__":
    main()
