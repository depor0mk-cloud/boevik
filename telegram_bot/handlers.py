from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from contextvars import ContextVar

router = Router()
current_user_ctx = ContextVar("current_user")

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Добро пожаловать в Боевик Бот! (Python Version)\nИспользуйте /правило чтобы узнать как играть.")

@router.message(Command("правило"))
async def cmd_rules(message: Message):
    await message.answer(
        "📜 <b>Правила игры:</b>\n"
        "1. Создавайте кланы или вступайте в существующие.\n"
        "2. Работайте (/работа), чтобы пополнять казну клана.\n"
        "3. Стройте заводы для пассивного дохода.\n"
        "4. Лидеры могут объявлять войны и проводить мобилизацию.\n"
        "5. Разрабатывайте ракеты для сокрушительных ударов.\n"
        "6. Уважайте других игроков.",
        parse_mode="HTML"
    )

# Add other handlers as needed to match the TypeScript version
