import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

import sqlite3
db_name = 'data/botdb3'

fields = ['id',
          'phone' ,
          'verification_code'  , 
          'user_ID'       ,
          'balance'       ,
          'stateCode'     ,
          'selected_template' ,
          'last_visit'    ,
          'logo_upload'   ,
          'logo_location' ,
          'bg_font_color' ,
          'font_color'    , 
          'fixed_title']

def get_user_data(uid):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM tbl_users WHERE user_ID=?''', (uid,))
    user_data = cursor.fetchone()
    user_data = dict(zip(fields,user_data))
    return user_data
