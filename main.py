import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, add_movie, get_movie

BOT_TOKEN = "8946353183:AAGShaLJw1IE0d1AdVMprjQp0ATUHQtUIhM"
ADMIN_ID = 8189726048

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Inline tugmalarni yasash funksiyasi
def get_movie_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍 Yoqdi", callback_data="like"),
                InlineKeyboardButton(text="👎 Yoqmadi", callback_data="dislike")
            ],
            [
                InlineKeyboardButton(text="📢 Kanalimiz", url="https://t.me/telegram_kanal_havolasi")
            ]
        ]
    )
    return keyboard

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Kino kodini kiriting:")

# Admin video yuborganda bazaga saqlash
@dp.message(F.video & (F.from_user.id == ADMIN_ID))
async def save_movie_handler(message: types.Message):
    caption = message.caption.strip() if message.caption else ""
    
    if caption.isdigit():
        movie_id = int(caption)
        file_id = message.video.file_id
        add_movie(movie_id, file_id, f"🎬 Kino kodi: {movie_id}")
        await message.reply(f"✅ Kino saqlandi! Kodi: {movie_id}")
    else:
        await message.reply("⚠️ Videoga izoh (caption) sifatida faqat kino kodini yozing!")

# Foydalanuvchi raqam yozganda kinoni knopkalar bilan berish
@dp.message(F.text & F.text.isdigit())
async def get_movie_handler(message: types.Message):
    movie_id = int(message.text)
    data = get_movie(movie_id)

    if data:
        file_id, caption = data
        await message.answer_video(
            video=file_id, 
            caption=caption,
            reply_markup=get_movie_keyboard()  # Knopkalarni biriktirish
        )
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())