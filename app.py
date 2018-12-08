import numpy as np 
import requests
from emoji import emojize

from PIL import Image

import database
from io import BytesIO

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)


from telegram.ext import (
        Updater,
        CommandHandler,
        CallbackQueryHandler,
        RegexHandler,
        MessageHandler,
        ConversationHandler,
        Filters)



from telegram import ChatAction,ParseMode
from telegram import ReplyKeyboardMarkup




import sqlite3

import cv2


from image_processing import add_logo,add_caption,adjust_logo_size

BOTNAME = 'مانالوگو'


db_name = 'data/botdb3'

LANG = 'Fa'

from functools import wraps

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(*args, **kwargs):
        bot, update = args
        bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(bot, update, **kwargs)

    return command_func

def echo(bot,update):
  # emoji_char = {'one':' ','two':' ' ,'info':'\x31\xE2\x83\xA3'.decode('utf8')}
  bot.send_message(chat_id=update.message.chat_id, text= emojize(':+1:',use_aliases=True))


def about_us(bot,update):
  query = update.callback_query
  chat_id = query.message.chat_id
  aboutUs = '''
  امروزه یک از از دغدغه‌های مدیران کانال‌ها و گروه‌های تلگرامی، سرقت اطلاعات است. در واقع بسیاری افراد اطلاعات کانال یا گروه های دیگر را به راحتی کپی و سپس در کانال خود درج می‌کنند. 
   در این میان، تصاویر نیز به راحتی قابل کپی کردن هستند. که یکی از راه های حفظ مالکیت معنوی، درج لوگو یا نشان تجاری در تصویر است که تا حدی می‌تواند مالکیت اثر را حفظ کند. 
  *{}* یک سرویس دهنده مبتنی بر بات تلگرام است که به مدیران کانالها و گروه های تلگرامی این 
  امکان را فراهم می آورد تا نشان (لوگو) خود را قبل از ارسال آن به کانال یا گروه اضافه کنند. 
  *{}* دارای قالب های مختلف شامل قالب ساده، خبری و فروشگاهی است تا هر یک از کاربران با توجه به نیاز خود 
  نشان لوگو و متن مربوطه را در تصاویر درج کنند.
  '''.format(BOTNAME,BOTNAME)
  

  bot.edit_message_text(chat_id=chat_id,
                        message_id=query.message.message_id,
                        text=aboutUs,
                        reply_markup=main_menu_keyboard())


def start(bot,update):
    # Check userID in Databse
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    uid = update.message.chat_id
    cursor.execute('''SELECT stateCode FROM tbl_users WHERE user_ID=?''', (uid,))
    state_code = cursor.fetchone()

    if state_code is None:
        msg = ''' به ربات تلگرامی مانالوگو خوش آمدید.
         این ربات امکان افزودن آرم(لوگو) تجاری، متن و یا واترمارک را به عکس های شما فراهم کرده
          و حق مالکیت شما را برای تصاویر ارسالی در کانال یا گروه تلگرامی محفوض نگاه می دارد :cake:.'''
        msg = emojize(msg, use_aliases=True)
        update.message.reply_text(msg)
        
        cursor.execute('''INSERT INTO tbl_users(user_ID,stateCode,balance,logo_location , bg_font_color,font_color,selected_template) VALUES(?,?,?,?,?,?,?)''', (update.message.chat_id, 0 , 0,'top_left',1,1,1))
        bot.send_message(chat_id=uid, text=' لطفا شماره همراه خود را وارد کنید. شماره شما جهت فعالسازی حساب کاربری الزامی است. کد فعالسازی به شماره شما ارسال خواهد شد')

    
    elif state_code[0]==0:
        bot.send_message(chat_id=uid, text=' لطفا شماره همراه خود را وارد کنید. شماره شما جهت فعالسازی حساب کاربری الزامی است. کد فعالسازی به شماره شما ارسال خواهد شد')

    elif state_code[0]==1:
        bot.send_message(chat_id=uid, text='لطفا کد فعالسازی را وارد کنید و یا برای ارسال مجدد کد فعالسازی عدد 1 را وارد کنید')
    
    elif state_code[0]==2:   
        update.message.reply_text(main_menu_message(),reply_markup=main_menu_keyboard())


    db.commit()
    db.close()
    

@send_typing_action
def help(bot,update):
  bot.send_message(chat_id=update.message.chat_id, 
                  text="*این گزینه هنوز تکمیل نشده است*", 
                  parse_mode=ParseMode.MARKDOWN)


@send_typing_action
def msgHandler(bot, update):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction .TYPING )
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    uid = update.message.chat_id
    cursor.execute('''SELECT stateCode FROM tbl_users WHERE user_ID=?''', (uid,))
    state_code = cursor.fetchone()
    
    if state_code[0]==0:
        # update phone in table
        phone = update.message.text

        # CREATE AND SEND VERIFICATION CODE
        verCode = np.random.randint(10000,99999)
        # send sms
        bot.send_message(chat_id=uid, text=str(verCode))
        cursor.execute('''UPDATE tbl_users SET phone = ? , verification_code = ? , stateCode =?  WHERE user_ID = ? ''', (phone,verCode,state_code[0]+1, uid))

        bot.send_message(chat_id=uid, text='لطفا کد فعالسازی را وارد کنید و یا برای ارسال مجدد کد فعالسازی عدد 1 را وارد کنید')

    elif state_code[0]==1:
        verCode = update.message.text

        if verCode==str(1):
             # CREATE AND SEND VERIFICATION CODE 
            verCode = np.random.randint(10000,99999)
            bot.send_message(chat_id=uid, text=str(verCode))
            cursor.execute('''UPDATE tbl_users SET verification_code = ?  WHERE user_ID = ? ''', (verCode, uid))

        else:
            cursor.execute('''SELECT verification_code FROM tbl_users WHERE user_ID=?''', (uid,))
            stored_verCode = cursor.fetchone()[0]
            print(type(stored_verCode),type(verCode))
            if (stored_verCode == verCode):
                cursor.execute('''UPDATE tbl_users SET verification_code='ok', stateCode =?  WHERE user_ID = ? ''', (state_code[0]+1, uid))
                bot.send_message(chat_id=uid,text='حساب کاربری شما تایید شد. هم اکنون میتوانید از منوی کاربری از امکانات مانالوگو بهره مند شوید.')
                update.message.reply_text(main_menu_message(),reply_markup=main_menu_keyboard())
            
            else: 
                bot.send_message(chat_id=uid, text=' کدفعالسازی وارد شده نادرست است. لطفا مجددا کد فعالسازی را وارد کنید و یا برای ارسال مجدد کد فعالسازی عدد 1 را وارد کنید')
    


    # Get avtivation Code
    db.commit()
    db.close()
    






############################ Keyboards #########################################
from telegram import InlineKeyboardButton , InlineKeyboardMarkup 
def main_menu_keyboard():
  keyboard = [[InlineKeyboardButton('مدیریت لوگو', callback_data='manage_logo_manu'),
              InlineKeyboardButton('حساب کاربری', callback_data='account_info_manu')],
              [InlineKeyboardButton('درج لوگو روی تصویر', callback_data='aplly_logo')],
              [InlineKeyboardButton('راهنما', callback_data='help_manu'),
              InlineKeyboardButton('درباره مانالوگو', callback_data='about_us_manu')],
              ]
  return InlineKeyboardMarkup(keyboard)

def manage_logo_menu_keyboard():
  keyboard = [[InlineKeyboardButton('انتخاب قالب (خبری، فروشگاهی، ...', callback_data='template_menu')],
              [InlineKeyboardButton('ثبت یا تغییر لوگو', callback_data='set_logo')],
              [InlineKeyboardButton('ثبت جایگاه لوگو', callback_data='location_menu')],
              [InlineKeyboardButton('ثبت عنوان ثابت', callback_data='set_title')],
              [InlineKeyboardButton('ثبت رنگ پس زمینه متن', callback_data='set_bg_color')],
              [InlineKeyboardButton('ثبت رنگ متن', callback_data='set_font_color')],
              [InlineKeyboardButton('بازگشت به منوی اصلی', callback_data='main_manu')]]
  return InlineKeyboardMarkup(keyboard)

def account_info_menu_keyboard():
  keyboard = [[InlineKeyboardButton('میزان بافیمانده شارژ', callback_data='m2_1')],
              [InlineKeyboardButton('تاریخچه پرداخت ها', callback_data='m2_2')],
              [InlineKeyboardButton('تاریخچه مصرف', callback_data='m2_2')],
              [InlineKeyboardButton('بازگشت به منوی اصلی', callback_data='main_manu')]]
  return InlineKeyboardMarkup(keyboard)


def select_template_menu_keyboard():
  keyboard = [[InlineKeyboardButton('قالب لوگو (فقط لوگو)', callback_data='naive_template')],
              [InlineKeyboardButton('قالب لوگوپلاس (لوگو + عنوان ثابت)', callback_data='simple_template')],
              [InlineKeyboardButton('قالب خبری (لوگو + عنوان ثابت + عنوان خبر)', callback_data='news_template')],
              [InlineKeyboardButton('قالب فروشگاهی (لوگو + عنوان ثابت + کد کالا + نام کالا + قیمت کالا )', callback_data='shop_template')],
              [InlineKeyboardButton('بازگشت به منوی مدیریت لوگو', callback_data='manage_logo_manu')]]
  return InlineKeyboardMarkup(keyboard)


def select_location_menu_keyboard():
  keyboard = [[InlineKeyboardButton('بالا - راست', callback_data='top_right')],
              [InlineKeyboardButton('بالا - چپ', callback_data='top_left')],
              [InlineKeyboardButton('پایین - چپ', callback_data='bottom_left')],
              [InlineKeyboardButton('پایین - راست', callback_data='bottom_right')],
              [InlineKeyboardButton('انتخاب هوشمندانه', callback_data='best')],
              [InlineKeyboardButton('انتخاب تصادفی', callback_data='random')],
              [InlineKeyboardButton('بازگشت به منوی مدیریت لوگو', callback_data='manage_logo_manu')]]
  return InlineKeyboardMarkup(keyboard)



def select_bg_color_menu_keyboard():
  keyboard = [[InlineKeyboardButton('سبز', callback_data='green_bg_color'),
               InlineKeyboardButton('آبی', callback_data='blue_bg_color'),
               InlineKeyboardButton('قرمز', callback_data='red_bg_color')],
              [InlineKeyboardButton('سفید', callback_data='white_bg_color'),
              InlineKeyboardButton('خاکستری', callback_data='gray_bg_color'),
              InlineKeyboardButton('زرد', callback_data='yellow_bg_color')],
              [InlineKeyboardButton('نارنجی', callback_data='orange_bg_color'),
              InlineKeyboardButton('صورتی', callback_data='pink_bg_color'),
              InlineKeyboardButton('رنگ هوشمندانه', callback_data='auto_bg_color')],
              [InlineKeyboardButton('بازگشت به منوی مدیریت لوگو', callback_data='manage_logo_manu')]]
  return InlineKeyboardMarkup(keyboard)


def select_font_color_menu_keyboard():
  keyboard = [[InlineKeyboardButton('سبز', callback_data='green_font_color'),
               InlineKeyboardButton('آبی', callback_data='blue_font_color'),
               InlineKeyboardButton('قرمز', callback_data='red_font_color')],
              [InlineKeyboardButton('سفید', callback_data='white_font_color'),
              InlineKeyboardButton('خاکستری', callback_data='gray_font_color'),
              InlineKeyboardButton('زرد', callback_data='yellow_font_color')],
              [InlineKeyboardButton('نارنجی', callback_data='orange_font_color'),
              InlineKeyboardButton('صورتی', callback_data='pink_font_color'),
              InlineKeyboardButton('رنگ هوشمندانه', callback_data='auto_font_color')],
              [InlineKeyboardButton('بازگشت به منوی مدیریت لوگو', callback_data='manage_logo_manu')]]
  return InlineKeyboardMarkup(keyboard)
############################### Bot ############################################


@send_typing_action
def main_menu(bot, update):
  query = update.callback_query
  bot.edit_message_text(chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        text=main_menu_message(),
                        reply_markup=main_menu_keyboard())

@send_typing_action
def manage_logo_menu(bot, update):
  query = update.callback_query
  bot.edit_message_text(chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        text=first_menu_message(),
                        reply_markup=manage_logo_menu_keyboard())

@send_typing_action
def template_menu(bot, update):
  query = update.callback_query
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  uid = query.message.chat_id
  cursor.execute('''SELECT selected_template FROM tbl_users WHERE user_ID=?''', (uid,))
  template = cursor.fetchone()[0]
  template_farsi = {0:'ثبت نشده', 1:'قالب لوگو' ,2:'قالب لوگوپلاس' ,3:'قالب خبری' ,4:'قالب فروشگاهی' }


  query = update.callback_query
  bot.edit_message_text(chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        text='لطفاً قالب مورد نظر خود را انتخاب کنید (قالب فعلی : {})'.format(template_farsi[template]),
                        reply_markup=select_template_menu_keyboard())


@send_typing_action
def location_menu(bot, update):
  query = update.callback_query
  uid = query.message.chat_id
  user_data = database.get_user_data(uid)
  location = user_data['logo_location']
  location_farsi = {'top_right':'بالا-راست' ,'top_left':'بالا-چپ' ,'bottom_left':'پایین-چپ' ,'bottom_right':'پایین-راست' , 'best':'انتخاب هوشمندانه', 'random':'انتخاب تصادفی' }
  bot.edit_message_text(chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        text='لطفاً جایگاه لوگو در تصویر را انتخاب کنید. (جایگاه فعلی : {})'.format(location_farsi[location]),
                        reply_markup=select_location_menu_keyboard())

@send_typing_action
def bg_color_menu(bot, update):
  query = update.callback_query
  
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  uid = query.message.chat_id
  cursor.execute('''SELECT bg_font_color FROM tbl_users WHERE user_ID=?''', (uid,))
  prev_bg_color = cursor.fetchone()[0]
  color_farsi = { 1:'سبز' , 2:'آبی' , 3:'قرمز' , 4:'سفید' , 5:'خاکستری' , 6:'زرد', 7:'نارنجی', 8:'صورتی', 9:'هوشمندانه' }
  bot.edit_message_text(chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        text='لطفاً رنگ پس‌زمینه متن راانتخاب کنید. (رنگ فعلی  : {})'.format(color_farsi[prev_bg_color]),
                        reply_markup=select_bg_color_menu_keyboard())


@send_typing_action
def font_color_menu(bot, update):
  query = update.callback_query  
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  uid = query.message.chat_id
  cursor.execute('''SELECT font_color FROM tbl_users WHERE user_ID=?''', (uid,))
  prev_font_color = cursor.fetchone()[0]
  color_farsi = { 1:'سبز' , 2:'آبی' , 3:'قرمز' , 4:'سفید' , 5:'خاکستری' , 6:'زرد', 7:'نارنجی', 8:'صورتی', 9:'هوشمندانه' }
  bot.edit_message_text(chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        text='لطفاً رنگ متن راانتخاب کنید. (رنگ فعلی  : {})'.format(color_farsi[prev_font_color]),
                        reply_markup=select_font_color_menu_keyboard())


@send_typing_action
def set_template(bot, update):
  temp_dict = {'naive_template':1 ,'simple_template':2 ,'news_template':3 ,'shop_template':4  }
  temp_farsi = {'naive_template':'لوگو' ,'simple_template':'لوگوپلاس ' ,'news_template':'خبری' ,'shop_template':'فروشگاهی'}
  query = update.callback_query
  uid = query.message.chat_id 
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  cursor.execute('''UPDATE tbl_users SET selected_template = ?  WHERE user_ID = ? ''', (temp_dict[query.data],uid))
  db.commit()
  db.close()
  bot.edit_message_text(chat_id=uid,
                        message_id=query.message.message_id,
                        text='قالب {} برای شما ثبت شد'.format(temp_farsi[query.data]),
                        reply_markup=manage_logo_menu_keyboard())


@send_typing_action
def set_location(bot, update):
  location_farsi = {'top_right':'بالا-راست' ,'top_left':'بالا-چپ' ,'bottom_left':'پایین-چپ' ,'bottom_right':'پایین-راست' , 'best':'انتخاب هوشمندانه', 'random':'انتخاب تصادفی' }
  query = update.callback_query
  uid = query.message.chat_id 
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  cursor.execute('''UPDATE tbl_users SET logo_location = ?  WHERE user_ID = ? ''', (query.data,uid))
  db.commit()
  db.close()
  bot.edit_message_text(chat_id=uid,
                        message_id=query.message.message_id,
                        text='موقعیت {} برای شما ثبت شد'.format(location_farsi[query.data]),
                        reply_markup=manage_logo_menu_keyboard())


@send_typing_action
def set_bg_color(bot, update):
  color_farsi = { 1:'سبز' , 2:'آبی' , 3:'قرمز' , 4:'سفید' , 5:'خاکستری' , 6:'زرد', 7:'نارنجی', 8:'صورتی', 9:'هوشمندانه' }

  color_dict = {'green_bg_color':1 ,'blue_bg_color':2 ,'red_bg_color':3 ,'white_bg_color':4 , 'yellow_bg_color':5, 'gray_bg_color':6 ,'orange_bg_color':7,'pink_bg_color':8,'auto_bg_color':9}
  color_farsi = {'green_bg_color':'سبز' ,'blue_bg_color':'آبی' ,'red_bg_color':'قرمز' ,'white_bg_color':'سفید' , 'yellow_bg_color':'زرد', 'gray_bg_color':'خاکستری','orange_bg_color':'نارنجی','pink_bg_color':'صورتی','auto_bg_color':'هوشمندانه' }
  query = update.callback_query
  uid = query.message.chat_id 
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  cursor.execute('''UPDATE tbl_users SET bg_font_color = ?  WHERE user_ID = ? ''', (color_dict[query.data],uid))
  db.commit()
  db.close()
  bot.edit_message_text(chat_id=uid,
                        message_id=query.message.message_id,
                        text='رنگ {} برای شما ثبت شد'.format(color_farsi[query.data]),
                        reply_markup=manage_logo_menu_keyboard())

@send_typing_action
def set_font_color(bot, update):
  color_farsi = { 1:'سبز' , 2:'آبی' , 3:'قرمز' , 4:'سفید' , 5:'خاکستری' , 6:'زرد', 7:'نارنجی', 8:'صورتی', 9:'هوشمندانه' }

  color_dict = {'green_font_color':1 ,'blue_font_color':2 ,'red_font_color':3 ,'white_font_color':4 , 'yellow_font_color':5, 'gray_font_color':6 ,'orange_font_color':7,'pink_font_color':8,'auto_font_color':9}
  color_farsi = {'green_font_color':'سبز' ,'blue_font_color':'آبی' ,'red_font_color':'قرمز' ,'white_font_color':'سفید' , 'yellow_font_color':'زرد', 'gray_font_color':'خاکستری','orange_font_color':'نارنجی','pink_font_color':'صورتی','auto_font_color':'هوشمندانه' }
  query = update.callback_query
  uid = query.message.chat_id 
  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  cursor.execute('''UPDATE tbl_users SET font_color = ?  WHERE user_ID = ? ''', (color_dict[query.data],uid))
  db.commit()
  db.close()
  bot.edit_message_text(chat_id=uid,
                        message_id=query.message.message_id,
                        text='رنگ {} برای شما ثبت شد'.format(color_farsi[query.data]),
                        reply_markup=manage_logo_menu_keyboard())

@send_typing_action
def set_logo(bot, update):
  query = update.callback_query
  uid = query.message.chat_id 
  text_msg=''' لطفا نشان لوگو را وارد کنید. در ارسال لوگو به موارد زیر دقت کنید 
   :point_left: تصویر با پسوند png ارسال شود
   :point_left: تصویر را به صورت فایل ارسال کنید نه به صورت عکس 
  در صورت انصراف از ثبت لوگو عدد 0 را وارد کنید.
  .
  ''' 
  text_msg = emojize(text_msg,use_aliases=True)
  bot.send_message(chat_id=uid,text=text_msg )
  return 0

@send_typing_action
def apply_logo_menu(bot, update):
  query = update.callback_query
  uid = query.message.chat_id 
  text_msg=''' لطفا تصویر مورد نظر خود را وارد کنید.  
  در صورت انصراف عدد 0 را وارد کنید.
  .
  ''' 
  bot.send_message(chat_id=uid,text=text_msg )
  return 0

@send_typing_action
def set_title(bot, update):
  query = update.callback_query
  uid = query.message.chat_id 

  db = sqlite3.connect(db_name)
  cursor = db.cursor()
  uid = query.message.chat_id
  cursor.execute('''SELECT fixed_title FROM tbl_users WHERE user_ID=?''', (uid,))
  prev_title= cursor.fetchone()[0]

  text_msg=''' لطفا عنوان ثابت را وارد کنید. عنوان ثابت مانند لوگو در تمامی تصاویر درج می‌شوند.
  عنوان فعلی شما "{}"  میباشد.   در صورتی که نمیخواهید عنوان ثابت را تغییر دهید عدد 0 را وارد کنید.
  
  .
  '''.format(prev_title)
  bot.send_message(chat_id=uid,text=text_msg )
  return 0




# and so on for every callback_data option
def first_submenu(bot, update):
  pass

def second_submenu(bot, update):
  pass

@send_typing_action
def unknown(bot, update):
      bot.send_message(chat_id=update.message.chat_id, text="متاسفم، دستور داده شده قابل تشخیص نیست. لطفا برای اطلاع از دستورات معتبر از دستور help/ استفاده کنید.")

@send_typing_action
def getphoto(bot,update):
  print('.............................................')

############################# Messages #########################################
def main_menu_message():
  main_menu_caption= {'En':'Main Menu',
                    'Fa':'منوی اصلی'}
  return main_menu_caption[LANG]

def first_menu_message():
  logo_menu_caption= {'En':'Logo Setting',
                    'Fa':'تنظیمات لوگو'}
  return logo_menu_caption[LANG]

def second_menu_message():
  return 'Choose the submenu in second menu:'



def Create_table():
    
    # Creating Tables
    try:
        db = sqlite3.connect(db_name)
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE tbl_users(id INTEGER PRIMARY KEY AUTOINCREMENT,
                            phone TEXT,
                            verification_code TEXT , 
                            user_ID       INTEGER,
                            balance       INTEGER,
                            stateCode     INTEGER,
                            selected_template INTEGER,
                            last_visit    INTEGER,
                            logo_upload   INTEGER,
                            logo_location TEXT,
                            bg_font_color INTEGER,
                            font_color    INTEGER, 
                            fixed_title TEXT
                            )
    ''')
        db.commit()
        db.close()
    except :
        print('Table is already exist')

@send_typing_action
def photo(bot, update):
    user = update.message.from_user


    if update.message.text =='0':
      bot.send_message(chat_id=user.id,
                        text='عملیات ثبت لوگو به درخواست شما لغو شد',
                        reply_markup=manage_logo_menu_keyboard())
    else:
      file = bot.getFile(update.message.document.file_id)
      file.download('logos/{}.png'.format(user.id))
      logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
      db = sqlite3.connect(db_name)
      cursor = db.cursor()
      cursor.execute('''UPDATE tbl_users SET logo_upload = ?  WHERE user_ID = ? ''', (1,user.id))
      db.commit()
      db.close()


      watermark_filename = 'logos/{}.png'.format(user.id)
      watermark = cv2.imread(watermark_filename, cv2.IMREAD_UNCHANGED)
      y,x = watermark[:,:,3].nonzero() # get the nonzero alpha coordinates
      minx = np.min(x)
      miny = np.min(y)
      maxx = np.max(x)
      maxy = np.max(y)
      cropImg = watermark[miny:maxy, minx:maxx]
      cv2.imwrite(watermark_filename, cropImg)
      
      
      bot.send_message(chat_id=user.id,
                          text='نشان لوگوی شما با موفقیت ثبت شد',
                        reply_markup=manage_logo_menu_keyboard())
    return ConversationHandler.END



@send_typing_action
def apply_logo_cancle(bot, update):
    user = update.message.from_user
    text=''':no_entry_sign: عملیات افزودن لوگو به یکی از دلایل زیر لغو شد. 
            :point_left: فایلی از کاربر دریافت نشد.
            :point_left: عملیات به درخواست کاربر لغو شد.
            .'''
    text_msg = emojize(text , use_aliases=True)
    bot.send_message(chat_id=user.id,
                      text = text_msg,
                      reply_markup=main_menu_keyboard())
    return ConversationHandler.END


@send_typing_action
def apply_logo(bot, update):
    user = update.message.from_user
    user_data=database.get_user_data(user.id)
    warning_txt = ''
    if (len(update.message.photo) > 0 ):
      warning_txt='''\n:heavy_exclamation_mark:فایل دریافتی به صورت عکس ارسال شده است و کیفیت آن به دلیل محدودیت‌های سرورهای اصلی تلگرام کاهش می‌یابد. 
      .'''
      file = bot.getFile(update.message.photo[-1].file_id)
      ext = 'jpg'

    if(update.message.document != None):
      mime = update.message.document.mime_type.split('/')  
      if (mime[0]=='image'):
        file = bot.getFile(update.message.document.file_id)
        filename =update.message.document.file_name.split('.')
        ext =filename[-1]
      else :
        text=''':x: فایل دریافت شده بایستی تصویر باشد.
            .'''
        text_msg = emojize(text , use_aliases=True)
        bot.send_message(chat_id=user.id,
                      text = text_msg,
                      reply_markup=main_menu_keyboard())
        return ConversationHandler.END
      
    host_filename = 'photos/{}.{}'.format(user.id,ext)
    watermark_filename = 'logos/{}.png'.format(user.id)
    file.download(host_filename)
    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    

    host = cv2.imread(host_filename)
    # host = Image.open(host_filename)

    watermark = cv2.imread(watermark_filename, cv2.IMREAD_UNCHANGED)
    # watermark = Image.open(watermark_filename)

    watermark = adjust_logo_size(host,watermark)
    # adding Caption to image 
    host = add_caption(host,user_data['fixed_title'],user_data['logo_location'],watermark)
    # adding logo to image 
    host= add_logo(host,watermark,user_data['logo_location'])
    
    cv2.imwrite(host_filename, host,[int(cv2.IMWRITE_JPEG_QUALITY), 100])
    

    bot.send_message(chat_id=user.id,
                        text=emojize( ':white_check_mark:نشان لوگوی شما با موفقیت ثبت شد و تا لحظاتی دیگر برای شما ارسال خواهد شد' +  warning_txt, use_aliases=True) )

    bot.send_photo(chat_id=user.id, photo=open(host_filename,'rb'))
    bot.send_document(chat_id=user.id, document=open(host_filename, 'rb'))

    bot.send_message(chat_id=user.id,
                        text='منوی اصلی' ,
                      reply_markup=main_menu_keyboard())
    return ConversationHandler.END




@send_typing_action
def fixed_title(bot, update):
    user = update.message.from_user
    fixed_title_text = update.message.text 
    
    if (fixed_title_text == '0'):
      bot.send_message(chat_id=user.id,
                        text='عنوان قبلی بدون تغییر برای شما ثبت شد',
                        reply_markup=manage_logo_menu_keyboard())
      return ConversationHandler.END
    
    else :
    
      logger.info("Fixed Title of %s: %s", user.first_name, 'is given')
      db = sqlite3.connect(db_name)
      cursor = db.cursor()
      cursor.execute('''UPDATE tbl_users SET fixed_title = ?  WHERE user_ID = ? ''', (fixed_title_text,user.id))
      db.commit()
      db.close()
      bot.send_message(chat_id=user.id,
                        text='عنوان ثابت شما با موفقیت ثبت شد',
                        reply_markup=manage_logo_menu_keyboard())
      return ConversationHandler.END
    



def cancel(bot, update):
    user = update.message.from_user


    logger.info("User %s canceled the conversation.", user.first_name)
    bot.edit_message_text(chat_id= update.message.chat_id,
                        text='ثبت لوگو به خواسته شما لغو شد!',
                        reply_markup=manage_logo_menu_keyboard())
  
    return ConversationHandler.END

def main():
    print('Hello!')
    Create_table()


    # Create the EventHandler and pass it your bot's token.
    token = '716853396:AAHysRbW9Lq2Z_fX46OtNQNCR6-6PXVTWqo'
    updater = Updater(token)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    set_logo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_logo, pattern='set_logo')],
        states={
            0: [MessageHandler(Filters.document|Filters.text, photo)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(set_logo_handler)




    set_title_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_title, pattern='set_title')],
        states={
            0: [MessageHandler(Filters.text, fixed_title)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(set_title_handler)
    

    apply_logo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(apply_logo_menu, pattern='aplly_logo')],
        states={
            0: [MessageHandler(Filters.document|Filters.photo, apply_logo),
                MessageHandler(Filters.text, apply_logo_cancle)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(apply_logo_handler)


    
    
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('echo', echo))
    dp.add_handler(MessageHandler(Filters.text, msgHandler))
    dp.add_handler(MessageHandler(Filters.document,getphoto))
    dp.add_handler( MessageHandler(Filters.command, unknown))


    ######################## Menu Handler ###################################
    updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main_manu'))
    updater.dispatcher.add_handler(CallbackQueryHandler(manage_logo_menu, pattern='manage_logo_manu'))
    updater.dispatcher.add_handler(CallbackQueryHandler(template_menu, pattern='template_menu'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_template, pattern='naive_template'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_template, pattern='simple_template'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_template, pattern='news_template'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_template, pattern='shop_template'))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(location_menu, pattern='location_menu'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_location, pattern='top_left'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_location, pattern='top_right'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_location, pattern='bottom_left'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_location, pattern='bottom_right'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_location, pattern='best'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_location, pattern='random'))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(bg_color_menu, pattern='set_bg_color'))

    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='green_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='blue_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='red_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='white_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='yellow_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='gray_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='orange_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='pink_bg_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_bg_color, pattern='auto_bg_color'))


    updater.dispatcher.add_handler(CallbackQueryHandler(font_color_menu, pattern='set_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='green_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='blue_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='red_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='white_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='yellow_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='gray_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='orange_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='pink_font_color'))
    updater.dispatcher.add_handler(CallbackQueryHandler(set_font_color, pattern='auto_font_color'))





    updater.dispatcher.add_handler(CallbackQueryHandler(first_submenu, pattern='_manu'))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(about_us, pattern='about_us_manu'))
    # 
    # updater.dispatcher.add_handler(CallbackQueryHandler(first_submenu, pattern='_manu'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(second_submenu,pattern='_manu'))    

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':

    main()
