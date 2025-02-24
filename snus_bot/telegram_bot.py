from dotenv import load_dotenv
import logging
import os
import string
import random
import json
from functools import partial
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
import threading
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler
)
from telegram.constants import ParseMode
import copy

file_lock = threading.Lock()

snus_assortment = {}
ORDERS_DICT = {}


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SELECTING_ACTION = "S"
SELECTING_SNUS = "3"
SELECTING_FLAVOR = "4"
SELECTING_AMOUNT = "90"
CONFIRMATION_ROUTES = 5
# Callback data
ONE, TWO, THREE, FOUR = range(4)
emoji = "⤵️"
CART = 'cart'

TYPING_COMMENT = "tp_com"

GO_HOME = "home"
CART_MANAGEMENT = "CART"

CONFIRM_RESERV = "15"

(MAIN_MENU, SNUS_MENU, FLAVOR_MENU, AMOUNT_MENU) = ('main_menu', 'snus_menu', 'flavor_menu', 'amount_menu')

FROM_BACK = "fmb"

RESERVATION = "reservation"
CURRENT_LEVEL = "6"
DISPLAY_CART = "c"
CONFIRM_RESERVATION = "8"
APPLY_RESERV = "9"
DECREASE_RESERVATION = "-"
INCREASE_RESERVATION = "+"

DELETE_RESERVATION_SLOT = "x"
EDIT_RESERV = "12"
END = "END"

ORDER = "order"
FORM_ORDER = "form_order"

SELECTED_SNUS = "1001"

ADD_TO_CART = "2002"

CURRENT_SHOP_LEVEL = "250"
DELETE_RESERVATION = 'DEL_RES'
TYPING = "10101"
CONTACT = 'contact'
REVIEWS = 'review'
ADD_COMMENT = 'add_comment'

CART_FROM_BEGINNING = "cb"
CANCEL_ORDER = "cancel"
COMMENT = "comment"
NO_COMMENT = 'no_comment'
ORDERS_FROM_MENU = "orders_from_menu"
PAGE_INDEX = 'pageindex'
NEXT_PAGE = 'next_page'
PREVIOUS_PAGE = 'prev_page'
BOSS_MANAGEMENT = 'boss_management'

CURRENT_ORDERS = "current_orders_for_boss"
EDITING_ORDERS = "editing_orders"
PROMOTIONS = "promotion"


SNUS_LOCAL_COPY = 'snus_local_copy'

SNUS_ASSORTIMENT_SNIPPET = 'snippet'

DEBUG = True

BOSSES = ["5069549772"]
BANNED_USERS = []

def update_database():
    file_lock.acquire()
    global snus_assortment
    global ORDERS_DICT
    with open('orders.json', 'r', encoding='utf-8') as file:
        ORDERS_DICT = json.load(file)

    with open('assortiment.json', 'r', encoding='utf-8') as file:
        snus_assortment = json.load(file)
    
    file_lock.release()



def save_database(changes, reverse, assort_changes=True):
    file_lock.acquire()
    global snus_assortment
    
    with open('orders.json', 'w', encoding='utf-8') as file:
        json.dump(ORDERS_DICT, file, ensure_ascii=False, indent=4)

    if reverse and assort_changes:
        for elem in changes:
            if elem[0] in snus_assortment:
                snus_assortment[elem[0]][elem[1]]['amount'] = snus_assortment[elem[0]][elem[1]]['amount'] + elem[2]
                if snus_assortment[elem[0]][elem[1]]['amount'] > 0:
                    snus_assortment[elem[0]][elem[1]]['availability'] = 1
    elif not reverse and assort_changes:
        for elem in changes:
            if elem[0] in snus_assortment:
                snus_assortment[elem[0]][elem[1]]['amount'] = snus_assortment[elem[0]][elem[1]]['amount'] - elem[2]
                if snus_assortment[elem[0]][elem[1]]['amount'] == 0:
                    snus_assortment[elem[0]][elem[1]]['availability'] = 0

    with open('assortiment.json', 'w', encoding='utf-8') as file:
        json.dump(snus_assortment, file, ensure_ascii=False, indent=4)

    file_lock.release()


def chunk_snus_assortment(snus_assortment, chunk_size=10):
    available_items = [key for key, value in snus_assortment.items() if value["AVAILABILITY"] == 1]
    return [available_items[i:i+chunk_size] for i in range(0, len(available_items), chunk_size)]

def snus_local_copy():
    return copy.deepcopy(snus_assortment)


def cache_finished_order(file_path, f_order, cost):
    from datetime import datetime

    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Prepare new data
    new_data = {
        current_date: {
            f_order[0]: {
                f_order[1]: {
                "cart": f_order[2],
                "cost": cost
                }
            }
        }
    }

    file_path = 'finished_orders.json'

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = {}

    # Update data
    if current_date not in existing_data:
        existing_data[current_date] = {}

    for user_id, user_orders in new_data[current_date].items():
        if user_id not in existing_data[current_date]:
            existing_data[current_date][user_id] = {}

        for order_id, ordered_items in user_orders.items():
            if order_id not in existing_data[current_date][user_id]:
                existing_data[current_date][user_id][order_id] = ordered_items
            else:
                # Merge ordered items, avoiding duplicates
                existing_items = existing_data[current_date][user_id][order_id]
                for item in ordered_items:
                    if item not in existing_items:
                        existing_items.append(item)

    # Write updated data back to file
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


def search_products(query) -> list:
    results = []
    query = query.lower()
    
    for product, details in snus_assortment.items():
        if query in product.lower():
            if details['AVAILABILITY'] == 1:
                results.append((product, details['PRICE']))
        else:
            for flavor in details:
                if isinstance(details[flavor], dict) and 'availability' in details[flavor]:
                    if query in flavor.lower() and details[flavor]['availability'] == 1:
                        results.append((f"{product} - {flavor}", details['PRICE']))
    
    return results




# TODO add search feature

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a message with three inline buttons attached."""
    if str(update.effective_user.id) in BANNED_USERS:
        return 
    if update.message:
        if update.message.text == "/start":
            context.user_data[FROM_BACK] = False
            context.user_data[SNUS_LOCAL_COPY] = True

    if str(update.effective_chat.id) in BOSSES:
        greeting_message = f"Здравствуйте, Босс!"
        keyboard = [
            [InlineKeyboardButton("Текущие заказы", callback_data=CURRENT_ORDERS)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if context.user_data.get(FROM_BACK):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text=greeting_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(f"{greeting_message}", reply_markup=reply_markup)
        context.user_data[FROM_BACK] = False
        return BOSS_MANAGEMENT
    else:
        global ORDERS_DICT
        update_database()
        if context.user_data[SNUS_LOCAL_COPY]:
            context.user_data[SNUS_ASSORTIMENT_SNIPPET] = snus_local_copy()
            context.user_data[SNUS_LOCAL_COPY] = False
        if not ORDERS_DICT.get(str(update.effective_user.id)) and not ORDERS_DICT.get(FROM_BACK):
            ORDERS_DICT[update.effective_user.id] = {ORDER:{}}
            context.user_data[CART] = []
            context.user_data[ORDER] = []
            save_database(changes=[], reverse=False, assort_changes=False)
            update_database()
        else:
            context.user_data[ORDER] = ORDERS_DICT[str(update.effective_user.id)][ORDER]
            context.user_data[CART] = context.user_data[CART] if context.user_data.get(CART) else []


        context.user_data
        context.user_data[RESERVATION] = []
        context.user_data[CURRENT_SHOP_LEVEL] = MAIN_MENU
        
        
        greeting_message = f"Здравствуйте, {update.effective_user.first_name}! Добро пожаловать в лучший магазин СНЮСа в Череповце!"

        keyboard = [
            [InlineKeyboardButton("Товары🏪", callback_data=SNUS_MENU)],
            [InlineKeyboardButton("Акции🎉", callback_data=PROMOTIONS)],
            [
                InlineKeyboardButton("Контакт✉️", callback_data=CONTACT),
                InlineKeyboardButton("Отзывы (в разработке...)", callback_data=REVIEWS)
            ],
        ]
        if context.user_data[CART]:
            context.user_data[CART_FROM_BEGINNING] = True
            keyboard.append([InlineKeyboardButton("Корзина🛒", callback_data=SELECTING_ACTION)])
        if context.user_data[ORDER]: # CHANGE IT!!!!!
            keyboard.append([InlineKeyboardButton("Текущие заказы📋", callback_data=FORM_ORDER)])
            context.user_data[ORDERS_FROM_MENU] = True

        reply_markup = InlineKeyboardMarkup(keyboard)
        if context.user_data.get(FROM_BACK):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text=greeting_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(f"{greeting_message}\nНавигация:", reply_markup=reply_markup)
        context.user_data[FROM_BACK] = False
        context.user_data[PAGE_INDEX] = 0
        return SELECTING_ACTION


async def send_msg_to_boss(order_info, chat_id, user_first_name, cancel=False) -> int:
    """Sends a message with three inline buttons attached."""
    bot = Bot(os.getenv('BOT_TOKEN'))
    async with bot:
        if cancel:
            text = f"Заказ с ID - {order_info} от <a href='tg://user?id={chat_id}'>{user_first_name}</a> отменен!🛑"
        else:
            text = f"Заказ с ID - {order_info} от <a href='tg://user?id={chat_id}'>{user_first_name}</a> принят!✅"
        for boss_id in BOSSES:
            await bot.send_message(text=text, chat_id=boss_id, parse_mode=ParseMode.HTML)


async def select_snus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a message with snus menu inline buttons attached."""
    query = update.callback_query
    if context.user_data.get(FROM_BACK) is not None or context.user_data.get(PAGE_INDEX) is not None:
        await query.answer()
        if query.data == NEXT_PAGE:
            context.user_data[PAGE_INDEX] = context.user_data[PAGE_INDEX] + 1
        elif query.data == PREVIOUS_PAGE:
            context.user_data[PAGE_INDEX] = context.user_data[PAGE_INDEX] - 1

    pages = chunk_snus_assortment(snus_assortment)

    pairs = pages[context.user_data[PAGE_INDEX]]
    keyboard = [
        [InlineKeyboardButton(f"{emoji}{key}", callback_data=key)] for key in pairs
    ]
    nav_board = []
    if context.user_data[PAGE_INDEX] > 0:
        nav_board.append(InlineKeyboardButton("⏪ Назад", callback_data=PREVIOUS_PAGE))
    if context.user_data[PAGE_INDEX] < len(pages) - 1:
        nav_board.append(InlineKeyboardButton("Далее ⏩", callback_data=NEXT_PAGE))

    keyboard.append(nav_board)
    keyboard.append([InlineKeyboardButton("На главную🧭", callback_data=FROM_BACK)])
    context.user_data[CURRENT_SHOP_LEVEL] = SNUS_MENU

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Что есть в продаже🌿:"
    if context.user_data.get(FROM_BACK):
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
        context.user_data[FROM_BACK] = False
    else:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    return SELECTING_FLAVOR

async def select_flavor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != FROM_BACK:
        context.user_data[RESERVATION].append(query.data)
    
    keyboard = [
        [InlineKeyboardButton(f"{emoji}{flavor}", callback_data=flavor)]
        for flavor in context.user_data[SNUS_ASSORTIMENT_SNIPPET][context.user_data[RESERVATION][0]] if flavor != "PRICE" and flavor != "AVAILABILITY"
        and context.user_data[SNUS_ASSORTIMENT_SNIPPET][context.user_data[RESERVATION][0]][flavor]["availability"] == 1
    ]
    keyboard.append([
        InlineKeyboardButton("🔙Назад", callback_data=FROM_BACK)
    ])
    context.user_data[CURRENT_SHOP_LEVEL] = FLAVOR_MENU
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    price = context.user_data[SNUS_ASSORTIMENT_SNIPPET][context.user_data[RESERVATION][0]]["PRICE"]
    text = f"Наявные вкусы🍬 для {context.user_data[RESERVATION][0]}:\nЦена: {price}₽"
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_AMOUNT


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    keyboard = [
        [InlineKeyboardButton("Посмотреть корзину🛒", callback_data=SELECTING_ACTION)], 
        [InlineKeyboardButton("В магазин🛍️", callback_data=SNUS_MENU)],
    ]

    context.user_data[CART_FROM_BEGINNING] = False
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text="Ваш выбор добавлен в корзину! Хотите заказать еще?", reply_markup=reply_markup)
    else:
        query = update.callback_query
        await query.answer()
        context.user_data[RESERVATION].append(int(query.data))
        await update.callback_query.edit_message_text(text="Ваш выбор добавлен в корзину! Хотите заказать еще?", reply_markup=reply_markup)

    snus_name = context.user_data[RESERVATION][0]
    snus_flavor = context.user_data[RESERVATION][1]
    snus_amount = context.user_data[RESERVATION][2]

    context.user_data[SNUS_ASSORTIMENT_SNIPPET][snus_name][snus_flavor]['amount'] = context.user_data[SNUS_ASSORTIMENT_SNIPPET][snus_name][snus_flavor]['amount'] - snus_amount
    if context.user_data[SNUS_ASSORTIMENT_SNIPPET][snus_name][snus_flavor]['amount'] == 0:
        context.user_data[SNUS_ASSORTIMENT_SNIPPET][snus_name][snus_flavor]['availability'] = 0
    
    print(context.user_data[SNUS_ASSORTIMENT_SNIPPET][snus_name][snus_flavor]['amount'])

    for elem in context.user_data[CART]:
        if elem[0] == snus_name and elem[1] == snus_flavor:
            elem[2] = int(elem[2]) + snus_amount
            break
    else:
        context.user_data[CART].append(context.user_data[RESERVATION])
    print(context.user_data[CART])
    context.user_data[RESERVATION] = []

    return SELECTING_ACTION

async def cart_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    print(query.data)
    if query.data[-1] == '-':
        removing_data = query.data[:-1].rsplit('-', 1)
        print("HERE's your removing data - ", removing_data)
        for elem in context.user_data[CART]:
            if elem[0] == removing_data[0] and context.user_data[CART].index(elem) == int(removing_data[1]):
                elem[2] = int(elem[2]) - 1
            if elem[2] == 0:
                context.user_data[CART].remove(elem)
    elif query.data[-1] == 'x':
        removing_data = query.data[:-1].rsplit('-', 1)
        for elem in context.user_data[CART]:
            if elem[0] == removing_data[0] and context.user_data[CART].index(elem) == int(removing_data[1]):
                context.user_data[CART].remove(elem)
    elif query.data[-1] == '+':
        removing_data = query.data[:-1].rsplit('-', 1)
        for elem in context.user_data[CART]:
            if elem[0] == removing_data[0] and context.user_data[CART].index(elem) == int(removing_data[1]):
                elem[2] = int(elem[2]) + 1
    keyboard = []
    number = 1
    text = "Ваша корзина🛒:\n"
    total_amount = 0
    id = 0

    offer = 500
    total_cost = 0
    print(context.user_data[CART])
    for reserv in context.user_data[CART]:
        snus_name = reserv[0]
        snus_flavor = reserv[1]
        max_amount = snus_assortment[snus_name][snus_flavor]['amount']
        keyboard.append(
            [
                    InlineKeyboardButton(text=f"#{number}", callback_data="30"),
                    InlineKeyboardButton(text="➖", callback_data=f"{reserv[0]}-{id}{DECREASE_RESERVATION}"),
            ])
        if int(reserv[2]) < max_amount:
            keyboard[id].append(InlineKeyboardButton(text="➕", callback_data=f"{reserv[0]}-{id}{INCREASE_RESERVATION}"))
        total_amount = total_amount + int(reserv[2])
        keyboard[id].append(InlineKeyboardButton(text="❌", callback_data=f"{reserv[0]}-{id}{DELETE_RESERVATION_SLOT}"))
        text = text + f"Товар #{number}:\nСнюс {reserv[0]} со вкусом {reserv[1]}. Количество - {reserv[2]}\n"
        number = number + 1
        id = id + 1
        total_cost = total_cost + (snus_assortment[reserv[0]]["PRICE"] * int(reserv[2]))
    if context.user_data.get(CART_FROM_BEGINNING):
        keyboard.append([InlineKeyboardButton("Назад", callback_data=MAIN_MENU)])
        context.user_data[FROM_BACK] = True
    else:
        keyboard.append([InlineKeyboardButton("В магазин", callback_data=SNUS_MENU)])

    skidka = (total_amount // 10) * offer

    total_cost = total_cost - skidka

    if skidka > 0:
        text = text + f"Скидка - {skidka}₽\n"
    
    text = text + f"Итого к оплате: {total_cost}₽" # CALCULATING
    if number == 1:
        text = "Ваша корзина пуста.🛒"
    else:
        keyboard.append([InlineKeyboardButton("Подтвердить заказ✅", callback_data=ADD_COMMENT)])
        context.user_data[ORDERS_FROM_MENU] = False

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return SELECTING_ACTION

def check_availability(cart_comparison):
    update_database()
    for elem in cart_comparison:
        if snus_assortment[elem[0]][elem[1]]["amount"] - int(elem[2]) < 0:
            return False
    return True

async def processing_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    # form previous order
    if not context.user_data[ORDERS_FROM_MENU]:
        if not check_availability(context.user_data[CART]):
            text = 'К сожалению, при формировании вашего заказа произошла ошибка ❌😕. Скорее всего это из-за того, что во время формирования вашей корзины, кто-то успел заказать оставшийся товар раньше Вас ⏱️. \
            \nВернитесь в главное меню 🏠 и попробуйте ещё раз 🔄.'
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("На главную🧭", callback_data=str(MAIN_MENU)),]])
            if not update.message:
                await query.answer()
                await query.edit_message_text(text=text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text=text, reply_markup=reply_markup)
            return SELECTING_ACTION
        generated_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ORDERS_DICT[str(update.effective_user.id)][ORDER][generated_id] = {"cart": context.user_data[CART]}
        if context.user_data.get(COMMENT):
            ORDERS_DICT[str(update.effective_user.id)][ORDER][generated_id]["comment"] = context.user_data[COMMENT]
            context.user_data[COMMENT] = ""
        else:
            ORDERS_DICT[str(update.effective_user.id)][ORDER][generated_id]["comment"] = ""
        save_database(changes=context.user_data[CART], reverse=False, assort_changes=True)
        update_database()
        context.user_data[RESERVATION] = []
        context.user_data[CART] = []
        await send_msg_to_boss(generated_id, str(update.effective_user.id), update.effective_user.first_name)
    
    context.user_data[FROM_BACK] = True

    
    text = "Ваши заказы:\n"
    i = 1
    total_cost = 0
    keyboard = [[]]
    total_amount = 0
    offer = 500
    skidka = 0

    # fix representation !!
    # check also db changes


    for key, item in ORDERS_DICT[str(update.effective_user.id)][ORDER].items():
        segment_cost = 0
        text = text + f"Заказ #{i} с ID - {key}:\nТовары:\n"
        for elem in item["cart"]:
            text = text + f"{elem[2]} х {elem[0]} ({elem[1]})\n"
            total_amount = total_amount + int(elem[2])
            total_cost = total_cost + (snus_assortment[elem[0]]["PRICE"] * int(elem[2]))
            segment_cost = segment_cost + (snus_assortment[elem[0]]["PRICE"] * int(elem[2]))

        keyboard.append([InlineKeyboardButton(f"🛑Отменить заказ #{key}", callback_data=f"{key}|{CANCEL_ORDER}"),])
        skidka = (total_amount // 10) * offer
        if skidka > 0:
            text = text + f"Скидка - {skidka}₽\n"
            segment_cost = segment_cost - skidka
            total_cost = total_cost - skidka
        if item['comment'] != "":
            text = text + f"Комментарий - {item['comment']}\n"
        text = text + f"Стоимость данного заказа: {segment_cost}₽\n"
        text = text + "---------------\n"
        i = i + 1
    if not context.user_data[ORDERS_FROM_MENU]:
        ORDERS_DICT[str(update.effective_user.id)][ORDER][generated_id]["total_cost"] = segment_cost
    text = text + f"Итого к оплате: {total_cost}₽\n" # CALCULATING
        

    if not context.user_data[ORDERS_FROM_MENU]:
        save_database(changes=context.user_data[CART], reverse=False, assort_changes=True)
        update_database()
        context.user_data[SNUS_LOCAL_COPY] = True

    text = text + "Для получения товара, пожалуйста, отправляйтесь по \
    адресу <a href='https://yandex.ru/maps/-/CDCniIOl'>ул. Устюженская 18. </a> 🛍️📍\n"
    keyboard.append([InlineKeyboardButton("На главную🧭", callback_data=str(MAIN_MENU)),])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not update.message:
        await query.answer()
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    return SELECTING_ACTION

async def save_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if update.message:
        context.user_data[COMMENT] = update.message.text
    else:
        context.user_data[COMMENT] = None
    await processing_order(update, context)
    return SELECTING_ACTION

async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("Далее⏩", callback_data=str(NO_COMMENT))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Если нужно можете добавить комментарий к заказу 📝. Просто напишите его и нажмите отправить ✉️.Если комментарий не нужен - просто нажмите 'Далее' ⏩.", reply_markup=reply_markup)
    return TYPING_COMMENT

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    deleted_order_id = query.data.split("|")[0]
    context.user_data[ORDER] = []
    temp = ORDERS_DICT[str(update.effective_user.id)][ORDER][deleted_order_id][CART]
    del ORDERS_DICT[str(update.effective_user.id)][ORDER][deleted_order_id]
    save_database(changes=temp, reverse=True)
    update_database()
    await send_msg_to_boss(deleted_order_id, str(update.effective_user.id), update.effective_user.first_name, True)
    await query.edit_message_text(text=f"Ваш заказ c ID - {deleted_order_id} отменен!✅", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("На главную", callback_data=str(MAIN_MENU))]]))
    context.user_data[FROM_BACK] = True
    return SELECTING_ACTION

async def save_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    class MyException(Exception):
        pass
    try:
        snus_name = context.user_data[RESERVATION][0]
        snus_flavor = context.user_data[RESERVATION][1]
        max_amount = snus_assortment[snus_name][snus_flavor]['amount']
        print(f"user's text - {update.message.text}")
        if update.message.text != FROM_BACK and int(update.message.text) <= max_amount and int(update.message.text) >= 1:
            user_data[RESERVATION].append(int(update.message.text))
        elif int(update.message.text) < 1 or int(update.message.text) > max_amount:
            raise MyException("MyError")
    
        user_data[FROM_BACK] = True
        await add_to_cart(update, context)
        return SELECTING_ACTION

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите целое число.😊")
        return TYPING
    except MyException:
        await update.message.reply_text("Пожалуйста, введите корректное количество. (от 1 до " + str(max_amount) + ")😉")
        return TYPING



async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    text = "Напишите количество шайб, или нажмите на кнопку ниже. 📝"
    context.user_data[CURRENT_SHOP_LEVEL] = AMOUNT_MENU
    query = update.callback_query
    await query.answer()
    if query.data != FROM_BACK:
        context.user_data[RESERVATION].append(query.data)
    print(context.user_data[RESERVATION])


    snus_name = context.user_data[RESERVATION][0]
    snus_flavor = context.user_data[RESERVATION][1]
    max_amount = snus_assortment[snus_name][snus_flavor]['amount']
    text = text + f"\nВ наличии {max_amount} шайб данного снюса.🛒"
    
    i = 0
    keyboard = []
    while i < max_amount:
        keyboard.append([InlineKeyboardButton(f"{i+1}", callback_data=i+1)])
        i = i + 1
        if i == 3 and i != max_amount:
            if i != max_amount:
                keyboard.append([InlineKeyboardButton(text=max_amount, callback_data=max_amount)])
            break
    
    keyboard.append([InlineKeyboardButton("🔙Назад", callback_data=FROM_BACK)])
    

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

    return TYPING


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pages = [start, select_snus, select_flavor]
    funcs = [partial(x, update, context) for x in pages]
    states = [SELECTING_SNUS, SELECTING_FLAVOR, SELECTING_AMOUNT] # fix it?
    ids = [SNUS_MENU, FLAVOR_MENU, AMOUNT_MENU, CONTACT]
    mapped_pages = dict(zip(ids, funcs))
    previous_shop_level = context.user_data[CURRENT_SHOP_LEVEL]
    context.user_data[FROM_BACK] = True
    current_state = states[ids.index(context.user_data[CURRENT_SHOP_LEVEL])]
    await mapped_pages[previous_shop_level]()
    context.user_data[RESERVATION] = context.user_data[RESERVATION][:-1]
    print(f"state- {current_state}")
    return current_state

async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    query = update.callback_query
    await query.answer()
    context.user_data[FROM_BACK] = True
    context.user_data[CURRENT_SHOP_LEVEL] = SNUS_MENU
    keyboard = [[
        InlineKeyboardButton("Открыть чат с администратором 💬📲", url="https://t.me/mbsclb"), #  TODO insert real link
    ]]

    keyboard.append([InlineKeyboardButton("Назад", callback_data=str(MAIN_MENU))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Свяжитесь с администратором. 📞👨‍💼", reply_markup=reply_markup)
    return SELECTING_ACTION

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data[FROM_BACK] = True
    context.user_data[CURRENT_SHOP_LEVEL] = SNUS_MENU
    keyboard = []

    keyboard.append([InlineKeyboardButton("Назад", callback_data=str(MAIN_MENU))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Этот раздел в разработке. Загляните попозже!", reply_markup=reply_markup)
    return SELECTING_ACTION

async def manage_current_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    update_database()
    context.user_data[FROM_BACK] = True
    await query.answer()
    keyboard = []
    text = "Текущие заказы:\n"
    i = 0
    for key, value in ORDERS_DICT.items():
        if value[ORDER]:
            for new_key, new_value in value[ORDER].items():
                i = i + 1
                text = text + f"Заказ #{i} с ID - {new_key} от <a href='tg://user?id={key}'>пользователя</a>:\n"
                for elem in new_value[CART]:
                    text = text + f"Товары - {elem[2]} х {elem[0]} ({elem[1]})\n"
                text = text + "Цена к оплате - " + str(new_value['total_cost']) + "₽\n"
                if new_value.get('comment'):
                    text = text + f"Комментарий - {new_value['comment']}\n"
                keyboard.append([InlineKeyboardButton(f"#{i}", callback_data=str(MAIN_MENU)),
                                 InlineKeyboardButton("Отменить🛑", callback_data=f"cancel_{key}_{new_key}"),
                                 InlineKeyboardButton("Завершить✅", callback_data=f"finish_{key}_{new_key}")])
                text = text + "------ ------\n"
    if i == 0:
        text = "Текущих заказов нет."
    keyboard.append([InlineKeyboardButton("Назад", callback_data=str(MAIN_MENU))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return EDITING_ORDERS

async def promotions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    text="Текущие акции: 🎉\n"
    text = text + "При покупке любых 10 шайб разом, Вы получаете скидку в размере 500 рублей. (Скидка работает несколько раз, т.е. 20 шайб - скидка 1000 рублей и тд.). 🏒🤑"

    await query.answer()
    context.user_data[FROM_BACK] = True
    keyboard = []
    keyboard.append([InlineKeyboardButton("Назад", callback_data=str(MAIN_MENU))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return SELECTING_ACTION

async def edit_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    processing_data = query.data.split("_")
    temp = ORDERS_DICT[processing_data[1]][ORDER][processing_data[2]][CART]
    total_cost = ORDERS_DICT[processing_data[1]][ORDER][processing_data[2]]['total_cost']
    del ORDERS_DICT[processing_data[1]][ORDER][processing_data[2]]
    bot = Bot(os.getenv('BOT_TOKEN'))
    if processing_data[0] == "cancel":
        save_database(changes=temp, reverse=True)
        text = "Вы отменили заказ от <a href='tg://user?id={}'>пользователя</a> с ID - {}".format(processing_data[1], processing_data[2])
        async with bot:
            await bot.send_message(text="🛑Ваш заказ с ID - {} отменен администратором!".format(processing_data[2]), chat_id=processing_data[1])
    elif processing_data[0] == "finish":
        cache_finished_order('finished_orders.json', [processing_data[1], processing_data[2], temp], total_cost)
        save_database(changes=temp, reverse=False, assort_changes=False)
        async with bot:
            await bot.send_message(text="✅Ваш заказ с ID - {} получен в точке выдачи!\nСпасибо что выбрали наш магазин😃".format(processing_data[2]), chat_id=processing_data[1])
        text = "Вы завершили заказ от <a href='tg://user?id={}'>пользователя</a> с ID - {}".format(processing_data[1], processing_data[2])
    update_database()

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=str(CURRENT_ORDERS))]])
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return BOSS_MANAGEMENT

async def input_search_row(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[InlineKeyboardButton("На главную", callback_data=str(MAIN_MENU))]]
    text = "Введите название товара который ищете."
    if update.message:
        search_query = update.message.text
        results = search_products(search_query)

    else:
        query = update.callback_query
        await query.answer()







TYPING_SEARCH_QUERY = 'typing_search_query'


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    load_dotenv()
    bot_token = os.getenv('BOT_TOKEN')
    application = Application.builder().token(bot_token).build()


    selecting_snus = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_snus, pattern="^" + SNUS_MENU + "$")],

        states={
            SELECTING_SNUS: [
        CallbackQueryHandler(select_snus, pattern="^" + SNUS_MENU + "$"),
    ],
            SELECTING_FLAVOR: [
        CallbackQueryHandler(select_flavor, pattern=f'^(?!{FROM_BACK}$|{PREVIOUS_PAGE}$|{NEXT_PAGE}$).*$'),
            ],
            SELECTING_AMOUNT: [
        CallbackQueryHandler(ask_for_input, pattern=f"^(?!.*{FROM_BACK}).*$")
            ],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_amount),],
            TYPING_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_search_row)]
        },
        #fallbacks=[CallbackQueryHandler(back, pattern="^" + str(END) + "$")],
        fallbacks=[CallbackQueryHandler(add_to_cart, pattern="^\d+$"),
                   CallbackQueryHandler(back, pattern="^" + FROM_BACK + "$"),
                   CallbackQueryHandler(start, pattern="^" + str(MAIN_MENU) + "$"),
                   CallbackQueryHandler(select_snus, pattern=f"^({NEXT_PAGE}|{PREVIOUS_PAGE})$")],
        map_to_parent={
            SELECTING_ACTION: SELECTING_ACTION,
            FROM_BACK: SELECTING_ACTION,
            MAIN_MENU: SELECTING_ACTION
        }

    )

    # current problems
    #fix - don't do anything
    #fix x don't do anything
    #fix 
    #add review section
    #fix problem <button> back from reviews returns cart

    selecting_handlers = [
        selecting_snus,
        # cart
        CallbackQueryHandler(cart_status, pattern='.*[-+xS]$'),
        # reviews
        CallbackQueryHandler(review, pattern="^" + str(REVIEWS) + "$"),
        # orders
        CallbackQueryHandler(processing_order, pattern=f"^{FORM_ORDER}$"),
        # contact
        CallbackQueryHandler(contact_admin, pattern="^" + str(CONTACT) + "$"),
        
        # menu 
        CallbackQueryHandler(start, pattern="^" + str(MAIN_MENU) + "$"),

        #cancel order
        CallbackQueryHandler(cancel_order, pattern=f"^.*{CANCEL_ORDER}$"),

        # promotions

        CallbackQueryHandler(promotions, pattern="^" + str(PROMOTIONS) + "$"),


        # come back
        CallbackQueryHandler(back, pattern="^" + str(GO_HOME) + "$"),

        # add comment 
        CallbackQueryHandler(add_comment, pattern=f"^{ADD_COMMENT}$"),

        CommandHandler("start", start)

    ]

    test_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
        MAIN_MENU: [CallbackQueryHandler(start, pattern="^" + str(MAIN_MENU) + "$")],
        SELECTING_ACTION: selecting_handlers,
        TYPING_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_comment)],
        BOSS_MANAGEMENT: [CallbackQueryHandler(manage_current_orders, pattern="^" + str(CURRENT_ORDERS) + "$")],
        EDITING_ORDERS: [CallbackQueryHandler(edit_order, pattern="^(?:cancel_|finish_).*$")],
        #TEST: [CallbackQueryHandler()]
        },
        fallbacks=[CommandHandler("start", start),
                   CallbackQueryHandler(processing_order, pattern="^" + str(NO_COMMENT) + "$"),
                   CallbackQueryHandler(start, pattern="^" + str(MAIN_MENU) + "$")
                   ],

    )

    #application.add_handler(conv_handler)

    #application.add_handler(current_reserv_conv)
    application.add_handler(test_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=[Update.CALLBACK_QUERY, Update.EDITED_MESSAGE, Update.MESSAGE])

if __name__ == '__main__':
  main()