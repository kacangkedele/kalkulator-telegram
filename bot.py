import ast
import logging
import math
import operator
import os
from typing import Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")
MAX_EXPRESSION_LENGTH = 100

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


Number = Union[int, float]


# Hanya operator matematika yang diizinkan oleh evaluator aman ini.
_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_calculate(expression: str) -> Number:
    """Evaluasi ekspresi matematika sederhana tanpa mengekspos builtins Python."""
    if not expression or len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("Ekspresi tidak valid")

    tree = ast.parse(expression, mode="eval")

    def evaluate(node: ast.AST) -> Number:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool) or not math.isfinite(float(node.value)):
                raise ValueError("Angka tidak valid")
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError
            result = _BINARY_OPERATORS[type(node.op)](left, right)
            if not math.isfinite(float(result)):
                raise ValueError("Hasil terlalu besar")
            return result

        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            result = _UNARY_OPERATORS[type(node.op)](evaluate(node.operand))
            if not math.isfinite(float(result)):
                raise ValueError("Hasil terlalu besar")
            return result

        raise ValueError("Ekspresi tidak valid")

    return evaluate(tree)


def format_result(result: Number) -> str:
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    if isinstance(result, float):
        return format(result, ".12g")
    return str(result)


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
            InlineKeyboardButton("−", callback_data="-"),
        ],
        [
            InlineKeyboardButton("0", callback_data="0"),
            InlineKeyboardButton(".", callback_data="."),
            InlineKeyboardButton("=", callback_data="="),
            InlineKeyboardButton("+", callback_data="+"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def calculator_text(expression: str) -> str:
    return f"🧮 <b>Kalkulator Telegram</b>\n\nEkspresi: <code>{expression}</code>"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await update.message.reply_text(
            calculator_text("0"),
            parse_mode="HTML",
            reply_markup=build_calculator_keyboard(),
        )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return

    await query.answer()
    current_text = query.message.text or ""
    expression = "0"

    if "Ekspresi:" in current_text:
        expression = current_text.split("Ekspresi:", 1)[1]
        expression = expression.replace("<code>", "").replace("</code>", "").strip()

    if expression in {"Error", "Error (Bagi 0)", "Invalid"}:
        expression = "0"

    action = query.data or ""

    if action == "clear":
        new_expression = "0"
    elif action == "del":
        new_expression = expression[:-1] if len(expression) > 1 else "0"
    elif action == "=":
        try:
            new_expression = format_result(safe_calculate(expression))
        except ZeroDivisionError:
            new_expression = "Error (Bagi 0)"
        except (SyntaxError, ValueError, TypeError, OverflowError):
            new_expression = "Error"
    else:
        if len(expression) >= MAX_EXPRESSION_LENGTH:
            new_expression = expression
        elif expression == "0" and (action.isdigit() or action == "."):
            new_expression = action
        else:
            new_expression = expression + action

    updated_text = calculator_text(new_expression)
    if updated_text == current_text:
        return

    try:
        await query.edit_message_text(
            updated_text,
            parse_mode="HTML",
            reply_markup=build_calculator_keyboard(),
        )
    except BadRequest as error:
        # Misalnya pesan sudah diedit oleh klik ganda; tidak perlu mematikan bot.
        logger.warning("Pesan tidak dapat diperbarui: %s", error)
    except Exception:
        logger.exception("Gagal memperbarui pesan kalkulator")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN belum diatur. Jalankan: export BOT_TOKEN='token-dari-BotFather'"
        )

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(["start", "kalkulator"], start_command))
    application.add_handler(CallbackQueryHandler(button_click))

    logger.info("Bot kalkulator berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
