import ast
import logging
import math
import os
import re

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_NAME = "Kalkulator Telegram Interaktif"
MAX_EXPRESSION_LENGTH = 80

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_valid_expression(text: str) -> bool:
    if not text or len(text) > MAX_EXPRESSION_LENGTH:
        return False
    if re.search(r"[^0-9+\-*/().%\s^]", text):
        return False
    return True


def safe_eval_math(expression: str) -> float:
    expr = expression.replace("%", "/100")
    expr = expr.replace("÷", "/").replace("×", "*")
    expr = expr.replace("^", "**")
    expr = expr.strip()

    if not is_valid_expression(expr):
        raise ValueError("Ekspresi tidak valid")

    tree = ast.parse(expr, mode="eval")

    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            value = float(node.value)
            if not math.isfinite(value):
                raise ValueError("Nilai tidak valid")
            return value

        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("Pembagian dengan nol")
                result = left / right
            elif isinstance(node.op, ast.Pow):
                result = left ** right
            else:
                raise ValueError("Operator tidak didukung")

            if not math.isfinite(result):
                raise ValueError("Hasil terlalu besar")
            return result

        if isinstance(node, ast.UnaryOp):
            operand = evaluate(node.operand)
            if isinstance(node.op, ast.UAdd):
                result = +operand
            elif isinstance(node.op, ast.USub):
                result = -operand
            else:
                raise ValueError("Operator unary tidak didukung")
            if not math.isfinite(result):
                raise ValueError("Hasil terlalu besar")
            return result

        if isinstance(node, ast.Call):
            raise ValueError("Fungsi tidak didukung")

        raise ValueError("Ekspresi tidak valid")

    return evaluate(tree.body)


def format_result(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return format(value, ".12g")


def build_calculator_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("C", callback_data="clear"),
            InlineKeyboardButton("DEL", callback_data="del"),
            InlineKeyboardButton("(", callback_data="("),
            InlineKeyboardButton(")", callback_data=")"),
        ],
        [
            InlineKeyboardButton("7", callback_data="7"),
            InlineKeyboardButton("8", callback_data="8"),
            InlineKeyboardButton("9", callback_data="9"),
            InlineKeyboardButton("÷", callback_data="/"),
        ],
        [
            InlineKeyboardButton("4", callback_data="4"),
            InlineKeyboardButton("5", callback_data="5"),
            InlineKeyboardButton("6", callback_data="6"),
            InlineKeyboardButton("×", callback_data="*"),
        ],
        [
            InlineKeyboardButton("1", callback_data="1"),
            InlineKeyboardButton("2", callback_data="2"),
            InlineKeyboardButton("3", callback_data="3"),
            InlineKeyboardButton("-", callback_data="-"),
        ],
        [
            InlineKeyboardButton("0", callback_data="0"),
            InlineKeyboardButton(".", callback_data="."),
            InlineKeyboardButton("=", callback_data="="),
            InlineKeyboardButton("+", callback_data="+"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_message_text(expression: str) -> str:
    safe_expression = expression if expression else "0"
    return f"🧮 <b>{APP_NAME}</b>\n\nEkspresi: <code>{safe_expression}</code>"


def extract_expression(text: str) -> str:
    if "Ekspresi:" not in text:
        return "0"
    snippet = text.split("Ekspresi:", 1)[1]
    cleaned = re.sub(r"<.*?>", "", snippet).strip()
    return cleaned or "0"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await update.message.reply_text(
            build_message_text("0"),
            parse_mode="HTML",
            reply_markup=build_calculator_keyboard(),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🧮 <b>Panduan Kalkulator</b>\n\n"
        "• Gunakan tombol di keyboard untuk memasukkan angka dan operasi\n"
        "• <b>C</b> = reset\n"
        "• <b>DEL</b> = hapus satu karakter\n"
        "• <b>=</b> = hitung hasil\n\n"
        "Contoh: 12+7, (8*5)-2, 2^8"
    )
    if update.message is not None:
        await update.message.reply_text(help_text, parse_mode="HTML")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()

    if user_text.startswith("/"):
        return

    if not is_valid_expression(user_text):
        await update.message.reply_text(
            "❌ Format tidak valid. Gunakan angka dan operator matematika seperti +, -, *, /, %, ^, ().",
        )
        return

    try:
        result = safe_eval_math(user_text)
        formatted = format_result(result)
        await update.message.reply_text(
            f"✅ Hasil: <b>{formatted}</b>",
            parse_mode="HTML",
        )
    except ZeroDivisionError:
        await update.message.reply_text("❌ Error: Tidak bisa dibagi dengan nol (0).")
    except Exception:
        await update.message.reply_text(
            "❌ Terjadi kesalahan dalam perhitungan. Periksa kembali ekspresi Anda."
        )


async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return

    await query.answer()
    current_text = query.message.text or ""
    current_expression = extract_expression(current_text)

    if current_expression in {"Error", "Invalid", "Error (Bagi 0)"}:
        current_expression = "0"

    action = query.data or ""

    if action == "clear":
        new_expression = "0"
    elif action == "del":
        if len(current_expression) <= 1:
            new_expression = "0"
        else:
            new_expression = current_expression[:-1]
    elif action == "=":
        try:
            result = safe_eval_math(current_expression)
            new_expression = format_result(result)
        except ZeroDivisionError:
            new_expression = "Error (Bagi 0)"
        except Exception:
            new_expression = "Error"
    else:
        if current_expression == "0" and (action.isdigit() or action == "."):
            new_expression = action
        elif current_expression == "Error" or current_expression == "Invalid":
            new_expression = action
        else:
            if len(current_expression) >= MAX_EXPRESSION_LENGTH:
                new_expression = current_expression
            else:
                new_expression = current_expression + action

    updated_text = build_message_text(new_expression)
    if updated_text == current_text:
        return

    try:
        await query.edit_message_text(
            updated_text,
            parse_mode="HTML",
            reply_markup=build_calculator_keyboard(),
        )
    except BadRequest as exc:
        logger.warning("Gagal memperbarui pesan: %s", exc)
    except Exception:
        logger.exception("Error saat edit message calculator")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN belum diatur. Buat file .env dengan isi: BOT_TOKEN=TOKEN_BOT_KAMU"
        )

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("kalkulator", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(CallbackQueryHandler(button_click))

    logger.info("Bot kalkulator siap berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
