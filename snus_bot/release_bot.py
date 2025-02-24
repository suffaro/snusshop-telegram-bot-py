from dotenv import load_dotenv
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler
)

import logging

from assortiment import snus_assortment

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO
)

DEBUG = True

# STATES
SELECTING_ACTION = "s"



# patterns (steps)
CART = 'cart'
ORDER = 'order'
CURRENT_SHOP_LEVEL = 'current_shop_level'
MAIN_MENU = 1
TWO = 2
THREE = 3
FROM_BACK = "b"
CART_FROM_BEGINNING = 'cart_from_beginning'
SNUS_MENU = "sn_menu"
REVIEWS = "reviews"
CONTACT = 'contact'




emoji = "⤵️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a message with three inline buttons attached."""
    if DEBUG:
        ORDERS_DICT = {}

    if not ORDERS_DICT.get(update.effective_user.id) and not context.user_data.get(CART):
        ORDERS_DICT[update.effective_user.id] = {CART: [], ORDER: {}}
        context.user_data[CART] = []
        context.user_data[ORDER] = []
    else:
        context.user_data[CART] = ORDERS_DICT[update.effective_user.id][CART]
        context.user_data[ORDER] = ORDERS_DICT[update.effective_user.id][ORDER]

    context.user_data[CURRENT_SHOP_LEVEL] = MAIN_MENU # do i need this??
    
    
    greeting_message = f"Здравствуйте, {update.effective_user.first_name}! Добро пожаловать в лучший магазин СНЮСа в Череповце!"

    keyboard = [
        [InlineKeyboardButton("Отзывы", callback_data=REVIEWS)],
        [
            InlineKeyboardButton("Меню", callback_data=SNUS_MENU),
            InlineKeyboardButton("Контакт", callback_data=CONTACT),
        ],
    ]
    if context.user_data[CART]:
        context.user_data[CART_FROM_BEGINNING] = True
        keyboard.append([InlineKeyboardButton("Корзина🛒", callback_data=CART)])
    if context.user_data[ORDER]: # CHANGE IT!!!!!
        keyboard.append([InlineKeyboardButton("Текущий заказ", callback_data=ORDER)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data.get(FROM_BACK):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=f"{greeting_message}\nНавигация:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"{greeting_message}\nНавигация:", reply_markup=reply_markup)
    context.user_data[FROM_BACK] = False
    
    return SELECTING_ACTION


async def select_snus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  """Sends a message with snus menu inline buttons attached."""

  keyboard = []
  pairs = [list(snus_assortment.keys())[i:i+2] for i in range(0, len(snus_assortment.keys()), 3)]
  keyboard = [
    [InlineKeyboardButton(f"{emoji}{key}", callback_data=key) for key in pair]
    for pair in pairs
  ]
  keyboard.append([
    InlineKeyboardButton("Назад", callback_data=FROM_BACK)
  ])
  context.user_data[CURRENT_SHOP_LEVEL] = SNUS_MENU

  reply_markup = InlineKeyboardMarkup(keyboard)

  text = "Наявный снюс:"
  if context.user_data.get(FROM_BACK):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    context.user_data[FROM_BACK] = False
  else:
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  pages = [start, select_snus, select_flavor, ask_for_input]
  funcs = [partial(x, update, context) for x in pages]
  states = [END, SELECTING_SNUS, SELECTING_FLAVOR, SELECTING_AMOUNT]
  ids = [MAIN_MENU, SNUS_MENU, FLAVOR_MENU, AMOUNT_MENU]
  mapped_pages = dict(zip(ids, funcs))
  previous_shop_level = str(int(context.user_data[CURRENT_SHOP_LEVEL]) - 1)
  context.user_data[FROM_BACK] = True
  current_state = states[ids.index(context.user_data[CURRENT_SHOP_LEVEL])]
  await mapped_pages[previous_shop_level]()
  context.user_data[RESERVATION] = context.user_data[RESERVATION][:-1]
  print(f"state- {current_state}")
  return current_state




menu_handlers = [
  CallbackQueryHandler(select_snus, pattern="^" + SNUS_MENU + "$"),
  
]


def main():
  load_dotenv()
  bot_token = os.getenv('BOT_TOKEN')
  application = Application.builder().token(bot_token).build()

  test_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start, pattern="^" + SNUS_MENU + "$")],
    states = {
      SELECTING_ACTION: menu_handlers,
    }
    )



  application.add_handler(test_handler)

  # Run the bot until the user presses Ctrl-C
  application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
  main()