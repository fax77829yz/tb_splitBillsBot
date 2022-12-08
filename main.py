import time
from telebot import types
from core import (bot, app, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH)


user_dict = {}

class User:
  def __init__(self, name):
    self.name = name
    self.bill = 0
    self.pg = 0

class ShareBill:
  def __init__(self):
    self.tips = 0
    self.tax = 0
    self.share_dishes = 0
    self.total = 0

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
  msg = bot.reply_to(message, "請輸入用餐人數")
  bot.register_next_step_handler(msg, process_ppl_bn_step)

def process_ppl_bn_step(message):
  try:
    chat_id = message.chat.id
    ppl_num = int(message.text)
    user_dict[chat_id] = {}
    user_dict[chat_id]["modified"] = None
    user_dict[chat_id]["num_of_ppl"] = ppl_num
    user_dict[chat_id]["user"] = []
    user_dict[chat_id]["share"] = ShareBill()
    msg = bot.send_message(chat_id, "輸入第1個人的姓名")
    bot.register_next_step_handler(msg, process_name_step)
  except Exception as e:
    bot.reply_to(message, 'oooops')

def process_name_step(message):
  try:
    chat_id = message.chat.id
    name = message.text
    user = User(name)
    user_dict[chat_id]["user"].append(user)
    msg = bot.reply_to(message, f'{name}的金額')
    bot.register_next_step_handler(msg, process_bill_step)
  except Exception as e:
    bot.reply_to(message, 'oooops')


def process_bill_step(message):
  chat_id = message.chat.id
  try:
    bill = float(message.text)
  except ValueError:
    msg = bot.reply_to(message, '請輸入金額')
    bot.register_next_step_handler(msg, process_bill_step)
    return
  try:
    user = user_dict[chat_id]["user"][-1]
    user.bill = bill
    count = len(user_dict[chat_id]["user"])
    if user_dict[chat_id]["num_of_ppl"] == count:
      markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
      markup.add('小費', '税', '共食', '完成')
      msg = bot.send_message(chat_id, '請輸入共同項目', reply_markup=markup)
      bot.register_next_step_handler(msg, process_share_step)
    else:
      msg = bot.send_message(chat_id, f"輸入第{count+1}個人的姓名")
      bot.register_next_step_handler(msg, process_name_step)
  except Exception as e:
    bot.reply_to(message, 'oooops')


def process_share_step(message):
  try:
    chat_id = message.chat.id
    share = message.text
    if share != u'完成':
      msg = bot.reply_to(message, f"請輸入{share}金額:")
    if (share == u'小費'):
      bot.register_next_step_handler(msg, process_tips_step)
    elif (share == u'税'):
      bot.register_next_step_handler(msg, process_tax_step)
    elif (share == u'共食'):
      bot.register_next_step_handler(msg, process_share_dishes_step)
    elif (share == u'完成'):
      check_str = parsing_input(chat_id)
      markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
      markup.add('修改', '確認')
      msg = bot.send_message(chat_id, check_str, reply_markup=markup)
      bot.register_next_step_handler(msg, process_result_step)
    else:
      bot.reply_to(message, 'oooops')
  except Exception as e:
    print(e)
    bot.reply_to(message, 'oooops')

def get_input(message, category):
  chat_id = message.chat.id
  value = float(message.text)
  if category == "tips":
    user_dict[chat_id]['share'].tips = value
  elif category == "tax":
    user_dict[chat_id]['share'].tax = value
  else:
    user_dict[chat_id]['share'].share_dishes = value
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
  markup.add('小費', '税', '共食', '完成')
  msg = bot.send_message(chat_id, '請輸入共同項目', reply_markup=markup)
  return msg

def process_tips_step(message):
  msg = get_input(message, 'tips')
  bot.register_next_step_handler(msg, process_share_step)

def process_tax_step(message):
  msg = get_input(message, 'tax')
  bot.register_next_step_handler(msg, process_share_step)

def process_share_dishes_step(message):
  msg = get_input(message, 'share_dishes')
  bot.register_next_step_handler(msg, process_share_step)

def parsing_input(chat_id):
  cost = 0.0
  bill = user_dict[chat_id]
  check_input = f"""請確認輸入是否正確
共{bill['num_of_ppl']}人用餐
"""
  for i in range(len(bill['user'])):
    user = bill['user'][i]
    cost += user.bill
    p_str = f"""
第{i+1}位
姓名：{user.name}
個人金額：{user.bill}
"""
    check_input += p_str

  tips = bill['share'].tips
  tax = bill['share'].tax
  share_dishes = bill['share'].share_dishes
  total = cost + share_dishes
  bill['share'].total = total
  cost = total + tips + tax
  check_input = check_input + f"\n小費：{tips}\n税：{tax}\n共食：{share_dishes}\n\n{'-'*10}\n總計：{cost}"
  return check_input

def process_result_step(message):
  chat_id = message.chat.id
  ans = message.text
  if ( ans == u'修改'):
    pass
  elif ( ans == u'確認'):
    calculate_split(chat_id)
    bot.send_message(chat_id, final_result(chat_id))
  else:
    bot.reply_to(message, 'oooops')

def calculate_split(chat_id):
  bill = user_dict[chat_id]
  extra = bill["share"].tips + bill["share"].tax
  share_dish_per_person = bill["share"].share_dishes/bill['num_of_ppl']
  for i in range(bill['num_of_ppl']):
    user = bill['user'][i]
    user.bill += share_dish_per_person
    user.pg = user.bill/bill["share"].total
    user.bill = round(user.bill + user.pg*extra, 2)

def final_result(chat_id):
  bill = user_dict[chat_id]
  result_str = "計算結果\n"
  for i in range(len(bill['user'])):
    user = bill['user'][i]
    p_str = f"""
第{i+1}位
姓名：{user.name}
個人金額：{user.bill}
"""
    result_str += p_str
  
  return result_str
  

# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()

# bot.infinity_polling()


# Remove webhook
bot.remove_webhook()

time.sleep(0.1)

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

if __name__ == "__main__":
    app.run(host=WEBHOOK_URL_BASE)
