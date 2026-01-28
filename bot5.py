import os
import json
import random
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Nedostaje TELEGRAM_TOKEN environment varijabla")

client = OpenAI()

# =====================
# UI TEKSTOVI
# =====================

INTRO_TEXTS = [
    "Tvoje riječi polako pronalaze svoj oblik, kao da se bude iz sna.\n"
    "Pretvaraju se u tiha pitanja koja još ne traže glas.\n\n"
    "Ne tražimo tačne odgovore koji se mogu provjeriti.\n"
    "Tražimo one koji ti pripadaju dok šutiš.\n\n"
    "Iz tvojih misli nastaje mala, krhka igra.\n"
    "Sastavljena od deset tihih dodira u obliku pitanja.\n\n"
    "Odgovaraš brojevima 1, 2 ili 3, sasvim jednostavno.\n"
    "Bez obaveze da budeš sigurna.\n\n"
    "Bez potrebe da budeš tačna.\n"
    "Samo polako, u svom ritmu.",

    "Nekoliko riječi koje si upisala već se pomjeraju ispod površine.\n"
    "Traže svoj ritam, kao disanje u mraku.\n\n"
    "Traže svoju tišinu, u kojoj je sve dopušteno.\n"
    "Traže svoj smisao, bez objašnjenja.\n\n"
    "Od njih se plete igra, lagana kao misao pred san.\n"
    "Nježna i spora, bez početka i bez kraja.\n\n"
    "Sa deset pitanja koja ne žure.\n"
    "Sa tri izbora koji ništa ne zahtijevaju.\n\n"
    "Sa jednim osjećajem koji ostaje.\n"
    "Onim koji je samo tvoj.",

    "Tvoje riječi ne ostaju na mjestu gdje si ih ostavila.\n"
    "One se zadržavaju u dahu, između dva treptaja.\n\n"
    "Kao trag na staklu koji se ne briše odmah.\n"
    "Iz tog traga nastaju pitanja, tiha i blaga.\n\n"
    "Jedno po jedno, bez reda.\n"
    "Bez potrebe za znanjem.\n\n"
    "Samo sa prisutnošću.\n"
    "Biraš brojeve, gotovo usput.\n\n"
    "Ali osjećaš sebe malo jasnije.\n"
    "Tiho, iznutra.",

    "Mapa tvog trenutka se crta polako, bez linija.\n"
    "Ne bojama, ne riječima.\n\n"
    "Već osjećajem koji se ne objašnjava.\n"
    "Od riječi nastaje igra.\n\n"
    "Od igre pitanja.\n"
    "Od pitanja bliskost.\n\n"
    "Od izbora trag u tišini.\n"
    "Od tog traga kratka priča.\n\n"
    "Bez tačnosti koja steže.\n"
    "Samo sa tobom.",

    "Riječi koje si ostavila iza sebe sada se okupljaju.\n"
    "Kao tiha skupina misli pred san.\n\n"
    "Koja želi oblik, ali ne ime.\n"
    "Koja želi glas, ali ne buku.\n\n"
    "Koja želi ritam, ali ne brzinu.\n"
    "Postaju igra.\n\n"
    "Postaju pitanja.\n"
    "Postaju izbori.\n\n"
    "Postaju bliskost.\n"
    "Postaju početak nečega nježnog."
]

BEFORE_TITLE_TEXTS = [
    "Na osnovu tvojih misli, evo kako se ova igra zove.\n"
    "Ime je nastalo tiho, iz onoga što nisi rekla naglas.",
    "Da joj dam ime, izgovorio bih ga ovako.\n"
    "Kao da ga šapćem blizu tvog uha, da ga čuje samo tvoja pažnja.",
    "Riječi si dala ti, ali ime je pronašlo tebe.\n"
    "Izgovaram ga polako, kao malu tajnu između mene i tebe."
]

BEFORE_QUESTION_TEXTS = [
    "Sada ti postavljam pitanje koje nije sasvim obično.",
    "Svaki izbor kaže nešto o tebi — ali bez težine.",
    "Odgovori kako osjećaš, ne kako razmišljaš.",
    "Samo izaberi. Priča već sluša."
]

DESCRIPTION_PREFIX_TEXTS = [
    "Ovaj izbor sam osjetio ovako…",
    "Tvoje slovo mi je reklo sljedeće.",
    "Na osnovu onoga što si izabrala…"
]

BEFORE_STORY_TEXTS = [
    "Sada su svi tvoji izbori ovdje, mirni i tihi.\n"
    "Ne kao brojevi na ekranu, već kao tragovi daha koji se još zadržavaju u prostoru.\n\n"
    "Slušao sam ih jedan po jedan, bez potrebe da ih razumijem.\n"
    "Svaki je ostavio malu sjenku, malu toplinu, jedva primjetan pomak unutra.\n\n"
    "Neki su bili sigurni, neki krhki, neki jedva izgovoreni.\n"
    "Ali svi su nosili tvoje ime, čak i kad ga nisu spomenuli.\n\n"
    "Sada ih skupljam polako, kao što se skupljaju komadi sna poslije buđenja.\n"
    "Ne da bih ih složio u red, već da bih ih sačuvao zajedno.\n\n"
    "Od njih nastaje priča.\n"
    "Tiha, i samo tvoja.",

    "Deset pitanja je prošlo kroz tebe, jedno po jedno.\n"
    "Deset tihih odgovora ostalo je da lebdi, kao prašina u svjetlu kasnog popodneva.\n\n"
    "U svakom se sakrio dio tvog glasa koji ne traži da bude čut.\n"
    "Onaj koji govori tek kada prestaneš objašnjavati.\n\n"
    "Neki odgovori su bili laki, gotovo neprimjetni.\n"
    "Neki su se zadržali malo duže nego što si očekivala.\n\n"
    "Sada ih spajam, ne da bih ih razjasnio.\n"
    "Već da bih čuo kako zvuče zajedno, bez pitanja.\n\n"
    "Kao jedan dah.\n"
    "Kao jedno priznanje.",

    "Iz svakog tvog izbora nastala je jedna tanka nit.\n"
    "Gotovo nevidljiva, ali dovoljno jaka da nešto zadrži na okupu.\n\n"
    "Skupljao sam ih polako, kao što se skupljaju misli pred san.\n"
    "Bez žurbe, bez straha da će se rasuti.\n\n"
    "Nijedna nije ista, ali se međusobno prepoznaju.\n"
    "Kao da su oduvijek znale jedna za drugu.\n\n"
    "Sada ih vežem u cjelinu koja ne steže.\n"
    "Samo drži, koliko treba.\n\n"
    "Pročitaj kako dišu zajedno.\n"
    "U istom ritmu."
]


def pick(lst):
    return random.choice(lst)

# =====================
# INLINE MENI
# =====================

def inline_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Nova igra", callback_data="NEW_GAME"),
         InlineKeyboardButton("Kraj", callback_data="END")]
    ])

# =====================
# GPT – STRUKTURA IGRE
# =====================

def generate_game_structure(keywords: str, retries: int = 3) -> dict:
    prompt = f"""
Na osnovu sljedećih ključnih riječi:

{keywords}

Kreiraj poetsku i intimnu strukturu interaktivne igre.

OBAVEZNA PRAVILA:

JEZIK:
- Svi tekstovi moraju biti isključivo na bosanskom jeziku.

SADRŽAJ:
- Kreiraj tačno jedan naslov igre (2–5 riječi, poetičan).
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
"""

    last_error = None

    for _ in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Vraćaš isključivo validan JSON. Bez dodatnog teksta."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            data = json.loads(response.choices[0].message.content)

            if len(data.get("questions", [])) != 10:
                raise ValueError("Pogrešan broj pitanja")

            return data

        except Exception as e:
            last_error = e
            print("JSON greška:", e)

    raise RuntimeError("GPT vratio nevalidan JSON") from last_error

# =====================
# GPT – ZAVRŠNA PRIČA
# =====================

def build_story(answers: list, keywords: str) -> str:
    answers_text = "\n".join(f"- {a}" for a in answers)

    prompt = f"""
Ključne riječi:
{keywords}

Izbori:
{answers_text}

Napiši nježnu završnu priču (10–12 rečenica, obraćanje sa "ti").
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Pišeš poetično intimno pismo na bosanskom jeziku."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()

# =====================
# HANDLERI
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = "WAITING_KEYWORDS"
    await update.message.reply_text(
        "Počinje nova igra.\n\n"
        "Unesi nekoliko ključnih riječi, misao, osjećaj ili kratku sliku iznutra.\n"
        "To može biti nešto što te raduje, nešto što ti nedostaje, ili nešto što još nema ime.\n\n"
        "Iz tvojih riječi nastat će tiha, poetična igra od deset pitanja.\n"
        "Ne tražimo tačne odgovore — samo one koji su tvoji.\n\n"
        "Kada budeš spremna, napiši svoje ključne riječi."
    )


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data["q_index"]
    q = context.user_data["questions"][q_index]

    intro = pick(BEFORE_QUESTION_TEXTS)

    text = (
        f"{intro}\n\n"
        f"<b>{q_index+1}. {q['question']}</b>\n"
        f"a) {q['options'][0]}\n"
        f"b) {q['options'][1]}\n"
        f"c) {q['options'][2]}\n\n"
        "Unesi: 1, 2 ili 3."
    )

    await update.message.reply_text(text, parse_mode="HTML")

	
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    text = update.message.text.strip()

    if state == "WAITING_KEYWORDS":

    # 1. Zaženi GPT v ozadju TAKOJ
        game_task = asyncio.create_task(
            asyncio.to_thread(generate_game_structure, text)
        )

    # 2. Izpiši intro (medtem GPT teče)
        intro_text = pick(INTRO_TEXTS)
        await send_in_five_parts(update, intro_text, delay=3)

    # 3. Počakaj na GPT rezultat (če še ni končan)
        game = await game_task

    # 4. Shrani podatke
        context.user_data.update({
            "keywords": text,
            "title": game["title"],
            "questions": game["questions"],
            "q_index": 0,
            "answers": [],
            "state": "IN_GAME"
        })

    # 5. Izpiši naslov
        title_intro = pick(BEFORE_TITLE_TEXTS)
        title_upper = game["title"].upper()

        formatted_title = f"{title_intro}\n\n<b>\t{title_upper}</b>\n\n"
        await update.message.reply_text(formatted_title, parse_mode="HTML")

    # 6. Prvo vprašanje
        await send_question(update, context)
        return


    if state == "IN_GAME":
        if text not in ("1", "2", "3"):
            await update.message.reply_text("Unesi 1, 2 ili 3.")
            return

        idx = int(text) - 1
        q_index = context.user_data["q_index"]
        q = context.user_data["questions"][q_index]

        desc = q["descriptions"][idx]

        prefix = pick(DESCRIPTION_PREFIX_TEXTS)
        await asyncio.sleep(0.5)
        await update.message.reply_text(
            f"{prefix}\n\n<b>„{desc}“</b>\n\n",
            parse_mode="HTML"
        )

        context.user_data["answers"].append(desc)
        context.user_data["q_index"] += 1

        if context.user_data["q_index"] >= 10:
            await asyncio.sleep(3)
            story_intro = pick(BEFORE_STORY_TEXTS)
            await send_in_five_parts(update, story_intro, delay=3)

            story = build_story(
                context.user_data["answers"],
                context.user_data["keywords"]
            )

            final_text = f"{context.user_data['title'].upper()}\n\n{story}"

            await update.message.reply_text(
                final_text,
                reply_markup=inline_menu(),
                parse_mode="HTML"
            )

            context.user_data["state"] = "END"
            return

        await send_question(update, context)

# =====================
# COMMANDS
# =====================

async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "NEW_GAME":
        context.user_data.clear()
        context.user_data["state"] = "WAITING_KEYWORDS"
        await query.edit_message_text("Počinje nova igra.\n\nUnesi ključne riječi ili misli.")
    else:
        await query.edit_message_text("Hvala ti na igri.")
        context.user_data.clear()

async def send_in_two_parts(update, full_text: str, delay: float = 1.0):
    parts = full_text.strip().split("\n\n", 1)

    if len(parts) == 1:
        await update.message.reply_text(parts[0])
        return

    await update.message.reply_text(parts[0])
    await asyncio.sleep(delay)
    await update.message.reply_text(parts[1])

async def send_in_three_parts(update, full_text: str, delay: float = 1.5):
    parts = full_text.strip().split("\n\n")

    if len(parts) <= 1:
        await update.message.reply_text(full_text)
        return

    if len(parts) == 2:
        await update.message.reply_text(parts[0])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[1])
        return

    # 3 ali več delov → združi presežek v tretji del
    part1 = parts[0]
    part2 = parts[1]
    part3 = "\n\n".join(parts[2:])

    await update.message.reply_text(part1)
    await asyncio.sleep(delay)

    await update.message.reply_text(part2)
    await asyncio.sleep(delay)

    await update.message.reply_text(part3)

async def send_in_four_parts(update, full_text: str, delay: float = 2.0):
    parts = full_text.strip().split("\n\n")

    if len(parts) <= 1:
        await update.message.reply_text(full_text)
        return

    if len(parts) == 2:
        await update.message.reply_text(parts[0])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[1])
        return

    if len(parts) == 3:
        await update.message.reply_text(parts[0])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[1])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[2])
        return

    # 4 ali več delov → presežek združi v 4. del
    part1 = parts[0]
    part2 = parts[1]
    part3 = parts[2]
    part4 = "\n\n".join(parts[3:])

    await update.message.reply_text(part1)
    await asyncio.sleep(delay)

    await update.message.reply_text(part2)
    await asyncio.sleep(delay)

    await update.message.reply_text(part3)
    await asyncio.sleep(delay)

    await update.message.reply_text(part4)

async def send_in_five_parts(update, full_text: str, delay: float = 2.0):
    parts = full_text.strip().split("\n\n")

    if len(parts) <= 1:
        await update.message.reply_text(full_text)
        return

    if len(parts) == 2:
        await update.message.reply_text(parts[0])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[1])
        return

    if len(parts) == 3:
        await update.message.reply_text(parts[0])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[1])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[2])
        return

    if len(parts) == 4:
        await update.message.reply_text(parts[0])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[1])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[2])
        await asyncio.sleep(delay)
        await update.message.reply_text(parts[3])
        return

    # 5 ali več delov → presežek združi v 5. del
    part1 = parts[0]
    part2 = parts[1]
    part3 = parts[2]
    part4 = parts[3]
    part5 = "\n\n".join(parts[4:])

    await update.message.reply_text(part1)
    await asyncio.sleep(delay)

    await update.message.reply_text(part2)
    await asyncio.sleep(delay)

    await update.message.reply_text(part3)
    await asyncio.sleep(delay)

    await update.message.reply_text(part4)
    await asyncio.sleep(delay)

    await update.message.reply_text(part5)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = "WAITING_KEYWORDS"
    await update.message.reply_text(
        "Počinje nova igra.\n\n"
        "Unesi nekoliko ključnih riječi ili misao."
    )

async def cmd_newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = "WAITING_KEYWORDS"
    await update.message.reply_text(
        "Počinje nova igra.\n\n"
        "Unesi nekoliko ključnih riječi, misao, osjećaj ili kratku sliku iznutra.\n"
        "To može biti nešto što te raduje, nešto što ti nedostaje, ili nešto što još nema ime.\n\n"
        "Iz tvojih riječi nastat će tiha, poetična igra od deset pitanja.\n"
        "Ne tražimo tačne odgovore — samo one koji su tvoji.\n\n"
        "Kada budeš spremna, napiši svoje ključne riječi."
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kako igrati:\n"
        "1) Unesi ključne riječi\n"
        "2) Odgovaraj na pitanja (1, 2 ili 3)\n"
        "3) Na kraju dobiješ poetičnu priču"
    )

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "My Poetic Game\n"
        "Interaktivna poetična igra.\n"
        "Ti biraš – priča nastaje."
    )

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Igra je prekinuta. Ako želiš, napiši /start.")


# =====================
# MAIN
# =====================

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("newgame", cmd_newgame))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_menu_click))

    print("Bot radi...")
    app.run_polling()

if __name__ == "__main__":
    main()
