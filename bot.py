import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Sozlamalar
TOKEN = "8844139610:AAFJ5yvdgaiOnDfTR9SHCYlfmIH58I3mFk8"
ADMIN_ID = 8893636852  # Yangi Admin Telegram ID raqami
DEFAULT_CHANNEL = "@androiduz_official"  # Boshlang'ich kanal

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

MOVIES_FILE = "movies.json"
SETTINGS_FILE = "settings.json"

# Fayldan kinolarni yuklash
def load_movies():
    if os.path.exists(MOVIES_FILE):
        try:
            with open(MOVIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# Faylga kinolarni saqlash
def save_movies(data):
    with open(MOVIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Kanal sozlamasini yuklash
def load_channel():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("channel", DEFAULT_CHANNEL)
        except Exception:
            return DEFAULT_CHANNEL
    return DEFAULT_CHANNEL

# Kanal sozlamasini saqlash
def save_channel(channel_username):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"channel": channel_username}, f, ensure_ascii=False, indent=4)

MOVIES = load_movies()
CHANNEL_USERNAME = load_channel()


# FSM (Holatlar) - Kino va Kanal qo'shish uchun
class AddMovie(StatesGroup):
    code = State()
    file_id = State()

class ChangeChannel(StatesGroup):
    channel_username = State()


# Majburiy obunani tekshirish funksiyasi
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, user_id=user_id
        )
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception:
        return False


# Obunani tekshirish uchun klaviatura
def subscribe_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
                )
            ],
            [InlineKeyboardButton(text="Obunani tekshirish 🔄", callback_data="check_sub")],
        ]
    )


# /start buyrug'i
@router.message(Command("start"))
async def cmd_start(message: Message):
    is_subbed = await check_subscription(message.from_user.id)

    if not is_subbed:
        await message.answer(
            "Botdan foydalanish uchun quyidagi kanalga obuna bo'ling:",
            reply_markup=subscribe_kb(),
        )
        return

    # Admin uchun maxsus tugmalar
    if message.from_user.id == ADMIN_ID:
        admin_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Kino qo'shish", callback_data="add_movie"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 Kanalni o'zgartirish", callback_data="change_channel"
                    )
                ]
            ]
        )
        await message.answer(
            f"Salom, Admin!\nJoriy kanal: {CHANNEL_USERNAME}\n\nKerakli bo'limni tanlang:",
            reply_markup=admin_kb
        )
    else:
        await message.answer("Salom! Kinoni ko'rish uchun uning kodini yuboring.")


# Obunani tekshirish tugmasi bosilganda
@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery):
    is_subbed = await check_subscription(callback.from_user.id)
    if is_subbed:
        await callback.message.delete()
        await callback.message.answer(
            "Rahmat! Obuna tasdiqlandi. Endi kino kodini yuborishingiz mumkin."
        )
    else:
        await callback.answer(
            "Siz hali kanalga obuna bo'lmadingiz!", show_alert=True
        )


# Admin: Kino qo'shishni boshlash
@router.callback_query(F.data == "add_movie", F.from_user.id == ADMIN_ID)
async def start_add_movie(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Kino kodini kiriting (masalan: 1, kino5):")
    await state.set_state(AddMovie.code)
    await callback.answer()


# Kino kodini qabul qilish
@router.message(AddMovie.code, F.from_user.id == ADMIN_ID)
async def process_movie_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await message.answer("Endi kino 🎥 videosini yuboring:")
    await state.set_state(AddMovie.file_id)


# Kino faylini qabul qilish va saqlash
@router.message(AddMovie.file_id, F.from_user.id == ADMIN_ID)
async def process_movie_file(message: Message, state: FSMContext):
    if not message.video:
        await message.answer("Iltimos, video yuboring!")
        return

    data = await state.get_data()
    code = data["code"]
    file_id = message.video.file_id

    MOVIES[code] = file_id
    save_movies(MOVIES)
    
    await state.clear()
    await message.answer(f"✅ Kino muvaffaqiyatli qo'shildi!\nKodi: {code}")


# Admin: Kanalni o'zgartirishni boshlash
@router.callback_query(F.data == "change_channel", F.from_user.id == ADMIN_ID)
async def start_change_channel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Yangi kanal username'sini @ belgisi bilan yuboring:\n(Masalan: @yangi_kanal)\n\n"
        "⚠️ Eslatma: Bot yangi kanalda ham ADMIN bo'lishi kerak!"
    )
    await state.set_state(ChangeChannel.channel_username)
    await callback.answer()


# Yangi kanal username'sini qabul qilish
@router.message(ChangeChannel.channel_username, F.from_user.id == ADMIN_ID)
async def process_change_channel(message: Message, state: FSMContext):
    global CHANNEL_USERNAME
    new_channel = message.text.strip()

    if not new_channel.startswith("@"):
        await message.answer("Xato! Kanal username'si @ belgisi bilan boshlanishi kerak. Qayta kiriting:")
        return

    CHANNEL_USERNAME = new_channel
    save_channel(CHANNEL_USERNAME)

    await state.clear()
    await message.answer(f"✅ Majburiy kanal muvaffaqiyatli o'zgartirildi!\nYangi kanal: {CHANNEL_USERNAME}")


# Foydalanuvchi kino kodini yuborganda
@router.message()
async def get_movie(message: Message):
    is_subbed = await check_subscription(message.from_user.id)
    if not is_subbed:
        await message.answer(
            "Botdan foydalanish uchun avval kanalga obuna bo'ling:",
            reply_markup=subscribe_kb(),
        )
        return

    code = message.text.strip()
    if code in MOVIES:
        await message.answer_video(
            video=MOVIES[code], caption=f"Mana siz so'ragan kino! (Kod: {code})"
        )
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())