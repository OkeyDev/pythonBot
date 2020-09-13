from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import mysql.connector # База данных
from mysql.connector import pooling # Мультипоточность
from mysql.connector.errors import Error
from datetime import time, datetime, timedelta
import re

######################################
#           Author: OkeyDev          #
# Github: https://github.com/OkeyDev #
# About: This is example telegram    #
# About: chat bot for victorines     #
######################################

TOKEN = '' # Введите токен, который вы можете узнать у BotFather

class Conn:
    def __init__(self):
        self.pool = mysql.connector.pooling.MySQLConnectionPool( # Для работы вам нужно создать пользователя bot с паролем sc8KCek9aaVf3Fnn или ввести свои данные в поля user и passwd
        pool_name="pynative_pool",
        pool_size=3,
        pool_reset_session=True,
        host="localhost",
        user="bot",
        #sc8KCek9aaVf3Fnn
        passwd="sc8KCek9aaVf3Fnn",
        database="bot",
        collation="utf8mb4_general_ci",
        auth_plugin='mysql_native_password'
        ) # ВАЖНО! Измените тут на ваши данные
    def get_connection(self):
        return DataBase(self.pool.get_connection(), self.pool)
    
class DataBase: #
    def __init__(self, db, pool):
        self.db = db
        self.pool = pool
    def commit(self):
        try:
            self.db.commit()
        except mysql.connector.Error as err: # Тут мы делаем проверку на случай, если БД отключилась.
            print  (err.errno)
            if (err.errno == 2013 or err.errno == 2055):
                self.cursord.reconnect()
                self.commit()
            else:
                raise err
    def cursor(self, buffered=False): 
        self.cursord = Cursor(self.db.cursor(buffered=buffered), self)
        return self.cursord
    def close(self):
        self.db.close()
    def reconnect(self): # Переподключение
        self.db.reconnect(attempts=5, delay=3)
        return self

class Cursor:
    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db
    def execute(self,sql, data=None, multi=False): # С помощью этой функции мы отправляем запросы в БД
        try:
            self.cursor.execute(sql, data, multi=multi) 
        except mysql.connector.Error as err:# Тут мы делаем проверку на случай, если БД отключилась.
            print("sql", sql)
            if (err.errno == 2013 or err.errno == 2055):
                self.reconnect()
                self.cursor.execute(sql, data, multi=multi) 
            else:
                raise err
    def fetchone(self):
        return self.cursor.fetchone() 
    def fetchall(self):
        return self.cursor.fetchall() 
    def close(self):
        self.cursor.close()
    def reconnect(self):
        db = self.db.reconnect()
        self.db = db
        self.cursor = self.db.db.cursor()

pool = Conn() # Используем пулы, для многопоточности
mydb = pool.get_connection()
jobdb =  pool.get_connection()  
cursor = mydb.cursor(buffered=True)
job_cursor = jobdb.cursor(buffered=True)


def exist_user(user_id): # функция для проверки, существует ли пользователь в БД
    global mydb
    cursor.execute("SELECT user_id FROM `users` WHERE `user_id`={0}".format(user_id))
    res = cursor.fetchall()
    if (len(res) == 0): #  Если не существует пользователя, то создаем его
        cursor.execute("INSERT INTO `users` (`user_id`, `state`) VALUES ({0}, 0)".format(user_id))
        cursor.execute("UPDATE `statistic` SET `value` = value + 1 WHERE `str_id` = 'new users'")
        mydb.commit()
        return False # Только создали
    return True # Уже существует

def is_admin(user_id, bot=None ): # Эта фукция проверяет, являеться ли пользователь админом
    cursor.execute("SELECT * FROM `admins` WHERE `user_id` = {0}".format(user_id))
    data = cursor.fetchone()
    if (data == None and bot != None): # Если пользователь знает ключевые слова непонятно откуда
        bot.send_message(user_id, "Извините, но вы не администратор. ")
        return False
    elif (data == None):
        return False # Возвращает ничего, то есть админа не существует
    return data[0]

def get_start_markup(user_id): # Эта функция отправляет основные кнопочки внизу
    is_user_admin = is_admin(user_id)
    cursor.execute("SELECT * FROM `admins` WHERE `user_id` = {0} AND `is_admin_edit` = 1;".format(user_id))
    resu = cursor.fetchone()
    if (is_user_admin != False and resu == None): # Если админ и не находиться в меню админа
        return ReplyKeyboardMarkup([[KeyboardButton("🎲 Играть"), KeyboardButton("💰 Баланс")],[KeyboardButton("🔔 Реклама"), KeyboardButton("💬 Канал и чат")],[KeyboardButton("Админка")]],resize_keyboard=True)
    if (resu != None): # Eсли находиться в меню админа
        return ReplyKeyboardMarkup([[KeyboardButton("Редактировать вопросы"),KeyboardButton("Статистика")],
        [KeyboardButton("Установить время запуска викторины"), KeyboardButton("Отправить рекламу"), KeyboardButton("Установить баланс")],
        [KeyboardButton("В главное меню")]], resize_keyboard=True) # Возвращаем кнопочки с админскими функциями
    
    return ReplyKeyboardMarkup([[KeyboardButton("🎲 Играть"), KeyboardButton("💰 Баланс")],[KeyboardButton("🔔 Реклама"), KeyboardButton("💬 Канал и чат")]],resize_keyboard=True) # Если это просто пользователь

def start (update, context): # Стартовое сообщение
    user_id = update.message.from_user.id
    markup = get_start_markup(user_id)
    if (exist_user(user_id)):
        context.bot.send_message(user_id,"Добро пожаловать обратно!",reply_markup=markup) # Приветствие для старичков
        cursor.execute("UPDATE `users` SET `state` = 0 WHERE `user_id` = {0}; ".format(user_id))
        end_game(user_id)
    else:
        cursor.execute("UPDATE `statistic` SET `value` = value + 1 WHERE `str_id` = 'new users'")
        context.bot.send_message(user_id,"Привет! Этот бот умеет то-то то-то...", reply_markup=markup) # Приветствие для новичков
    mydb.commit()


def hello(update, context): #  Просто тестовая функция
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))


def get_guestion_number(user_id, lcursor=cursor): # Получает номер вопроса. Предполагаеться, что время уже идёт
    lcursor.execute("SELECT `question_number` FROM `cache` WHERE `user_id` = {0} ".format(user_id))
    data = lcursor.fetchone()
    if (data == None):
        return -1
    return data[0]



def get_question(user_id,is_next_question=False, lcursor=cursor): # Данная функция берет основные данные о вопросу
    question_number =  get_guestion_number(user_id, lcursor)
    if (is_next_question):
        question_number += 1
    lcursor.execute("SELECT `data` FROM `questions` WHERE `number` = {0}  AND type=1;".format(question_number))
    question = lcursor.fetchone() # Получаем вопрос
    if (question == None): #  Если вопроса не существует (закончились/Админ не создал), то возращаем ничего
        return None
    question = question[0]
    lcursor.execute("SELECT `data` FROM `questions` WHERE `number` = {0}  AND type=0;".format(question_number))
    variants = lcursor.fetchall()
    return {"question": question, "variants": variants} # Словарь данных, в котором записаны данные вопроса


def generate_markup(variants): # Создаёт нормальное отображение кнопочек внизу
    first_array = []
    second_array = []
    for i in range(0,len(variants)):
        if (i % 2):
            first_array.append(KeyboardButton(variants[i][0]))
        else:
            second_array.append(KeyboardButton(variants[i][0]))
    markup = ReplyKeyboardMarkup([first_array, second_array], resize_keyboard=True)
    return markup


def get_question_data(user_id, is_next=False, lcursor=cursor): #  Готовим данные к отправки 
    data = get_question(user_id, is_next, lcursor)
    if (data == None):
        return None
    question = data["question"]
    markup = generate_markup(data["variants"])
    return {"text": question, "markup":markup}


def time_controller(context): #  Функция контролирует таймеры всех пользователей
    jobdb.commit()
    job_cursor.execute("SELECT `user_id`,`time_message_id` FROM `cache` WHERE `time_left` > 0 AND `question_number` > 0;")
    #print("Get users")
    res = job_cursor.fetchall()
    for data in res:
        user_id = data[0]
        time_left = time_left_func(user_id,job_cursor)
        message_id = data [1]
        if (message_id == 0):
            message_id = None
        if (time_left == 0):
            job_cursor.execute("UPDATE `users` SET `state` = 0  WHERE `user_id` = {0} ; ".format(user_id))
            end_game(user_id, job_cursor)
            #job_cursor.execute("UPDATE `users` SET `time_left` = '00:00:00', `question_number` = 0 WHERE `user_id` = {0}".format(user_id))
            markup = get_start_markup(user_id)
            context.bot.send_message(user_id,"Время вышло!", reply_markup=markup)
        else:
            try:
                context.bot.edit_message_text("Осталось времени: *{0}*".format(time_left), user_id, message_id, parse_mode="Markdown")
            except Exception:
                pass
        #print("work_time =", counter, "s")
        #print("message_id: ",message_id)
def do_action(data=1):
    job_cursor.execute("UPDATE `bot_settings` SET `data` = {} WHERE `id` = 2;".format(data))
    print("STARTED with data -", data)
    job_cursor.execute("UPDATE `users` SET `is_do_victorine` = 0;")
    print("USERS UPDATED")
    jobdb.commit()

def delayed_start(context):
    jobdb.commit()
    job_cursor.execute("SELECT `date` FROM `bot_settings` WHERE `id` = 1 LIMIT 1")
    before = job_cursor.fetchone()[0]
    job_cursor.execute("SELECT `date` FROM `bot_settings` WHERE `id` = 3 LIMIT 1")
    after = job_cursor.fetchone()[0]
    job_cursor.execute("SELECT `data` FROM `bot_settings` WHERE `id` = 2 LIMIT 1")
    is_started = job_cursor.fetchone()[0]
    now = datetime.now()
    if (before == None or after == None):
        return
    raznica = before.minute + before.hour * 60 - (now.minute + now.hour * 60)
    if (raznica == 15):
        job_cursor.execute("SELECT `user_id` FROM `users` WHERE `state` = 3")
        while True:
            temp = job_cursor.fetchone()
            if (temp == None):
                break
            temp = temp[0]
            try:
                context.bot.send_message(temp, "Осталось 15 минут! Приготовся!")
            except Exception:
                continue
    elif (raznica <= 5 and raznica > 0):
        job_cursor.execute("SELECT `user_id` FROM `users` WHERE `state` = 3")
        while True:
            temp = job_cursor.fetchone()
            if (temp == None):
                break
            temp = temp[0]
            try:
                context.bot.send_message(temp, "{} мин!".format(raznica))
            except Exception:
                continue
    elif (raznica == 0):
        job_cursor.execute("SELECT `user_id` FROM `users` WHERE `state` = 3")
        all_id = job_cursor.fetchall()
        for i in all_id:
            temp_id = i[0]
            job_cursor.execute("INSERT INTO `cache` (`user_id`) VALUES ({})".format(temp_id))
            try:
                send_question(temp_id, context.bot, job_cursor)
            except Exception:
                job_cursor.execute("DELETE FROM `cache` WHERE `user_id` = {}".format(temp_id))
                continue
            job_cursor.execute("UPDATE `users` SET `state` = 2 WHERE `user_id` = {}".format(temp_id))
            jobdb.commit()
    if (before != None):
        if (before.day < now.day  and is_started == 0 and after.day > now.day):
            do_action()
        elif(before.day == now.day and is_started == 0):
            if (before.hour < now.hour and is_started == 0 and after.hour > now.hour):
                print("hour -",before.hour, now.hour)
                do_action()
            elif(before.hour == now.hour and is_started == 0):
                if (before.minute < now.minute and is_started == 0 and after.minute > now.minute):
                    do_action()
                elif(before.minute == now.minute and is_started == 0):
                    do_action()
    job_cursor.execute("SELECT `data` FROM `bot_settings` WHERE `id` = 2 LIMIT 1")
    is_started = job_cursor.fetchone()[0]
    if (after != None):
        if ((after.day < now.day or before.day > now.day)  and is_started == 1):
            do_action(0)
        elif(after.day == now.day and is_started == 1 and is_started == 1):
            if ((after.hour < now.hour or before.hour > now.hour) and is_started == 1):
                do_action(0)
            elif(after.hour == now.hour):
                if ((after.minute < now.minute or before.minute > now.minute) and is_started == 1):
                    do_action(0)
                elif(after.minute == now.minute and is_started == 1):
                    do_action(0)
    
    

def time_left_func(user_id, cursor):# Функция которая берёт время из БД и превращает в оставшееся время
    cursor.execute("SELECT `time_left` FROM `cache` WHERE `user_id` = {0} LIMIT 1".format(user_id))
    to_time = cursor.fetchone()[0]
    now = datetime.now()
    time_left = to_time.total_seconds() - timedelta(seconds=now.second, minutes=now.minute, hours=now.hour).total_seconds()
    return time_left

def to_datetime(add=60):
    now = datetime.now()
    to_time = (now + timedelta(seconds=add)).strftime("%H:%M:%S")
    return to_time

def send_question(user_id, bot, lcursor=cursor):
    data = get_question_data(user_id,False, lcursor)
    if (data == None):
        bot.send_message(user_id, "Не-а)")
        return
    time = to_datetime(15)
    message_id = bot.send_message(user_id, "Осталось времени: *{}*".format(15), parse_mode="Markdown").message_id
    cursor.execute("UPDATE `cache` SET `time_message_id` = {1}, `time_left` = '{2}'  WHERE `user_id` = {0};".format(user_id, message_id,time))
    bot.send_message(user_id, data["text"], reply_markup=data["markup"])

def end_game(user_id, lcursor=cursor):
    lcursor.execute("DELETE FROM `cache` WHERE `user_id` = {0}".format(user_id))

def Victorine(update, context): # функция, обрабатывающая викторину
    mydb.commit()
    question_time = 15
    subscribe_time = 14
    user_id = update.message.from_user.id 
    cursor.execute("SELECT `user_id` FROM `users` WHERE `user_id` = {0}  AND `state` = 2;".format(user_id))
    is_game_started =  cursor.fetchone()
    if (is_game_started == None): # Если пользователь только запустил викторину, то идёт эта функция
        cursor.execute("SELECT `data` FROM `questions` WHERE `number` = 1  AND type = 1;")
        result = cursor.fetchone()
        if (result == None): # Если админ ещё не сделал/запустил викторину, то отправляеться это сообщеник
            context.bot.send_message(user_id, "К сожалению, сейчас нет никаких викторин. Приходите каждый день в 13:00 или в 20:00")
            return
        cursor.execute("SELECT `data` FROM `bot_settings` WHERE `id` = 2;")
        result = cursor.fetchone()
        if (result[0] == 0): # Если админ ещё не сделал/запустил викторину, то отправляеться это сообщеник
            cursor.execute("UPDATE `users` SET `state` = 3 WHERE `user_id` = {}".format(user_id))
            context.bot.send_message(user_id, "К сожалению, сейчас нет никаких викторин. Вам придет сообщение, за 15 мин до начала викторины")
            mydb.commit()
            return
        cursor.execute("SELECT `user_id` FROM `users` WHERE `user_id` = {} AND `is_do_victorine` = 0".format(user_id))
        res = cursor.fetchone()
        if (res != None):
            context.bot.send_message(user_id, "Ты уже играл, приходи завтра в 13:00 или сегодня в 20:00 по МСК")
            return
        cursor.execute("UPDATE `users` SET `is_do_victorine` = 1 WHERE `user_id` = {}".format(user_id))
        context.bot.send_message(user_id, "Игра началась!")
        message_id = context.bot.send_message(user_id, "Осталось времени: *{}*".format(question_time), parse_mode="Markdown").message_id
        now = datetime.now()
        to_time = (now + timedelta(seconds=question_time)).strftime("%H:%M:%S")
        cursor.execute("UPDATE `users` SET `state` = 2  WHERE `user_id` = {0} ;".format(user_id))
        cursor.execute("INSERT INTO `cache` (user_id, question_number, time_left, time_message_id, can_continue) VALUES ({0}, 1, '{1}', {2}, 1)".format(user_id, to_time, message_id))
        first_question = get_question_data(user_id)
        context.bot.send_message(user_id, first_question["text"], reply_markup=first_question["markup"])
        mydb.commit()
    else: # Если продолжаеться Викторина
        cursor.execute("SELECT `can_continue` FROM `cache` WHERE `user_id` = {} LIMIT 1".format(user_id))
        res = cursor.fetchone()[0]
        if (res == 0):
            context.bot.send_message(user_id, "Подтвердите подписку")
            return
        question_number = get_guestion_number(user_id) # Получаем номер вопросв
        otvet = update.message.text # Обрабатываем данные
        cursor.execute("SELECT MAX(number) FROM `questions`")
        max_number = cursor.fetchone()[0]
        if (max_number - 1 == question_number and otvet == "Продолжить игру"):
            time = to_datetime(question_time)
            cursor.execute("UPDATE `cache` SET `time_left` = '{1}' WHERE `user_id` = {0}".format(user_id,time))
        elif (max_number - 1 == question_number and otvet == "Получить 100 рублей"):
            cursor.execute("UPDATE `users` SET `balance` = balance + 100, `state` = 0 WHERE `user_id` = {0}; ".format(user_id))
            end_game(user_id)
            markup = get_start_markup(user_id)
            context.bot.send_message(user_id, "Готово! Ваши деньги зачислены на счёт. Вывести вы их можете через кнопку 'баланс'", reply_markup=markup)
            mydb.commit()
            return
        else:
            cursor.execute("SELECT `data` FROM `questions` WHERE `number` = %s  AND type = 0 AND data COLLATE utf8mb4_unicode_ci = %s AND is_right_answer = 1 LIMIT 1;", (question_number, otvet))
            result = cursor.fetchone()
            if (result == None): # Правильный/Неправильный вариант
                #cursor.execute("UPDATE `users` SET `time_left` = '00:00:00', `time_message_id` = 0  WHERE `user_id` = {0} ;".format(user_id))
                markup = get_start_markup(user_id)
                if (question_number == max_number):
                    cursor.execute("UPDATE `users` SET `state` = 0  WHERE `user_id` = {0}; ".format(user_id))
                    end_game(user_id)
                    context.bot.send_message(user_id, "Неправильно! Надо будет тебе ещё подучить...", reply_markup=markup)
                    mydb.commit()
                    return
                context.bot.send_message(user_id, "Неправильно! Может в следующий раз повезёт :)")
                cursor.execute("SELECT `link`, `id`, `channel_id` FROM `adtab`")
                res = cursor.fetchall()
                if (len(res) == 0):
                    context.bot.send_message(user_id, "Извините, но пока нет никакой рекламы", reply_markup=markup) 
                    cursor.execute("UPDATE `users` SET `state` = 0  WHERE `user_id` = {0} ; ".format(user_id))
                    end_game(user_id)
                    mydb.commit()
                    return
                link = None
                for channels in res:
                    try:
                        print("Try get channel")
                        r = context.bot.get_chat_member(channels[2],user_id)
                        if (r.status == r.LEFT or r.status == r.KICKED): 
                            r = None
                            print("Channel seted")
                            link = (channels[0], channels[1]) 
                            break
                        print("User exist and you - ", r.user.username)
                    except Exception as e:
                        print("Non Exist or another error")
                        print(e)
                        r = None
                    if (r == None):
                        print("Channel seted")
                        link = (channels[0], channels[1]) 
                        break
                if (link == None):
                    print("No one channel exist")
                    context.bot.send_message(user_id, "Извините, но вы уже подписаны на все каналы", reply_markup=markup) 
                    cursor.execute("UPDATE `users` SET `state` = 0 WHERE `user_id` = {0} ; ".format(user_id))
                    end_game(user_id)
                    mydb.commit()
                    return
                if (link[0][0] == "@"):
                    link = ("https://t.me/" + link[0][1:], link[1])
                inline_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Подписаться", url=link[0])],[InlineKeyboardButton("Проверить",callback_data="c:{}".format(link[1]))]])
                context.bot.send_message(user_id, "У вас осталось {} секунд!\n\n1) Подпишитесь на канала\n2)Проверьте подписку\n3)игра продолжиться автоматически".format(subscribe_time), reply_markup=inline_markup)
                time = to_datetime(subscribe_time)
                cursor.execute("UPDATE `cache` SET `time_left` = '{1}',`can_continue` = 0 WHERE `user_id` = {0}".format(user_id,time))
                mydb.commit()
                return
            else:
                cursor.execute("UPDATE `statistic` SET `value` = value + 1 WHERE `str_id` = '{}' ".format("q:" + str(question_number)))
                context.bot.send_message(user_id, "Правильно! Сегодня твой день! :)")
                if (max_number - 1 == question_number): # Если это предпоследний вопрос, то
                    markup = ReplyKeyboardMarkup([[KeyboardButton("Получить 100 рублей")],[KeyboardButton("Продолжить игру")]], resize_keyboard=True)
                    cursor.execute("UPDATE `cache` SET `time_left` = '00:00:00' WHERE `user_id` = {0}".format(user_id))
                    context.bot.send_message(user_id, "Поздравляем!\n\nВы правильно ответили на {} вопросов. Ты можешь продолжить игру и получить больше или же получить 100 рублей на qiwi сейчас же.".format(question_number), reply_markup=markup)
                    mydb.commit()
                    return
                time = to_datetime(question_time)
                cursor.execute("UPDATE `cache` SET `time_left` = '{1}' WHERE `user_id` = {0}".format(user_id,time))
        
        is_sended = get_question_data(user_id, is_next=True)
        if (is_sended == None): # Если вопросы закончились, то отправляем сообщение и  выходим
            markup = get_start_markup(user_id)
            username = update.message.from_user.username
            cursor.execute("UPDATE `users` SET `state` = 0  WHERE `user_id` = {0} ; ".format(user_id))
            end_game(user_id)
            cursor.execute("SELECT `user_id` FROM `admins`")
            adm = cursor.fetchall()
            cursor.execute("SELECT `balance` FROM `users` WHERE `user_id` = {}".format(user_id))
            balance = cursor.fetchone()[0]
            for a in adm:
                context.bot.send_message(a[0], "Пользователь с ником @{0} ответил на все вопросы. user id - {1}. Его баланс - {2}".format(username, user_id, balance))
                mydb.commit() 
            context.bot.send_message(user_id, "Поздравляю! Вы правильно ответили на все вопросы! Бот обрабатывает данные. Вы получите сообщение, после того, как баланс измениться.", reply_markup=markup)
            return
        # Если нет, то продолжаем задавать вопросы
        time_left = time_left_func(user_id, cursor)
        message_id = context.bot.send_message(user_id, "Осталось времени: *{0}*".format(time_left), parse_mode="Markdown").message_id
        cursor.execute("UPDATE `cache` SET `time_message_id` = {1},`question_number` = '{2}'  WHERE `user_id` = {0};".format(user_id, message_id, question_number + 1))
        context.bot.send_message(user_id, is_sended["text"], reply_markup=is_sended["markup"])
        mydb.commit() # Сохраняем значения в БД

def edit_question(update, context): # Админская функция для редактирования вопросов и вариантов ответов
    user_id = update.callback_query.from_user.id
    cursor.execute("UPDATE `admins` SET `state` = 1, `which_question_edit` = {1} WHERE `user_id` = {0};".format(user_id, update.callback_query.data.split(":")[1]))
    context.bot.send_message(user_id, "Отправьте, новый вопрос", reply_markup=ReplyKeyboardRemove())

def admin_func(update, context): # Запуск админского меню
    user_id = update.message.from_user.id
    is_user_admin = is_admin(user_id, context.bot) 
    if (not is_user_admin):
        return # Если это просто обычный пользователь, то мы останавливаем выполнение функции
    cursor.execute("UPDATE `admins` SET `is_admin_edit` = 1 WHERE `user_id` = {0};".format(user_id))
    markup = get_start_markup(user_id)
    context.bot.send_message(user_id, "Добро пожаловать обратно, админ!", reply_markup=markup)

def back_to_main_menu(update, context): # Возвращаем обратно в обычное меню
    user_id = update.message.from_user.id
    is_user_admin = is_admin(user_id, context.bot)
    if (not is_user_admin):
        return
    cursor.execute("UPDATE `admins` SET `is_admin_edit` = 0 WHERE `user_id` = {0};".format(user_id))
    markup = get_start_markup(user_id)
    context.bot.send_message(user_id, "Возвращаем кнопочки", reply_markup=markup)


def get_id(update, context): #  Отправляем id пользователя
    context.bot.send_message(update.message.from_user.id,update.message.from_user.id)

def edit_opros(update, context): # Админская функция: отображает все вопросы и дает выбор, какое редактировать
    user_id = update.message.from_user.id
    is_user_admin = is_admin(user_id)
    if (not is_user_admin):
        return
    question_number = 1
    send_text = "Выберете,что редактировать \nВаши вопросы: \n"
    inline_markup = []
    while True:
        cursor.execute("SELECT `data`, `is_right_answer`,`type` FROM `questions` WHERE `number` = {0};".format(question_number))
        result = cursor.fetchall()
        if (len(result) == 0):
            break
        variants = ""
        question = ""
        for questions in result: # Перебираем вопросы 
            if (questions[2] == 0): # Если это правильный вариант ответа
                if (questions[1] == 1):
                    variants += questions[0] + "\t - Правильно\n"
                else: # Если это неправильный вариант ответа
                    variants += questions[0] + "\n"
            else:
                question = questions[0]
        send_text += str(question_number) + ". " + question + "\n" + variants + "\n"
        inline_markup.append([InlineKeyboardButton(question_number,callback_data=("q:{}".format(question_number)))])
        question_number += 1
    inline_markup = InlineKeyboardMarkup(inline_markup)
    button_markup = ReplyKeyboardMarkup([[KeyboardButton("Создать новый вопрос"), KeyboardButton("Удалить вопрос")],[KeyboardButton("Отмена")]], resize_keyboard=True)
    context.bot.send_message(user_id, send_text, reply_markup=inline_markup)
    context.bot.send_message(user_id, "Выберете действие", reply_markup=button_markup)

def admin_input(update, context, state): # Взаимодействует с вводом данных админа
    user_id = update.message.from_user.id
    data = update.message.text
    if (state == 1): # в этом случае мы создаем/обновляем вопрос из админки
        cursor.execute("SELECT `which_question_edit` FROM `admins` WHERE `user_id` = {0};".format(user_id))
        num = cursor.fetchone()[0]
        cursor.execute("SELECT `number` FROM `questions` WHERE `number` = {0} AND `type` = 1 LIMIT 1".format(num))
        res = cursor.fetchone()
        if (res == None):
            cursor.execute("INSERT INTO `questions` (`number`, `data`, `type`) VALUES (%s, %s, 1)", (num, data))
        cursor.execute("UPDATE `questions` SET `data` = %s WHERE `number` = %s AND `type` = 1",(data,num)) # Делаю так для защиты от mysql Injection
        markup = ReplyKeyboardMarkup([[KeyboardButton("Готово")]], resize_keyboard=True)
        context.bot.send_message(user_id, "Вопрос изменён, теперь отправте варианты ответа на вопрос {};".format(num), reply_markup=markup)
        cursor.execute("UPDATE `admins` SET `state` = 2 WHERE `user_id` = {};".format(user_id))
        cursor.execute("DELETE FROM `questions` WHERE `number` = {} AND `type` = 0;".format(num))
    elif (state == 2):
        cursor.execute("SELECT `which_question_edit` FROM `admins` WHERE `user_id` = {0};".format(user_id))
        num = cursor.fetchone()[0]
        if (data == "Готово"):
            cursor.execute("UPDATE `admins` SET `state` = 3 WHERE `user_id` = {};".format(user_id))
            cursor.execute("SELECT `data` FROM `questions` WHERE `type` = 0 AND `number` = {};".format(num))
            res = cursor.fetchall()
            markup = []
            for v in res:
                markup.append([KeyboardButton(v[0])])
            markup = ReplyKeyboardMarkup(markup, resize_keyboard=True)
            context.bot.send_message(user_id, "Отлично! Теперь выберете правильный вариант", reply_markup=markup)
            return
        cursor.execute("INSERT INTO `questions` (number,data,type) VALUES (%s,%s,0);",(num,data))
        context.bot.send_message(user_id, "Вариант добавлен. Добавьте отправьте ещё или нажмите готово")
    elif (state == 3):
        cursor.execute("SELECT `which_question_edit` FROM `admins` WHERE `user_id` = {0};".format(user_id))
        num = cursor.fetchone()[0]
        cursor.execute("UPDATE `questions` SET `is_right_answer` = 1 WHERE `data` = %s AND `number` = %s AND `type` = 0;", (data,num))
        markup = get_start_markup(user_id)
        context.bot.send_message(user_id, "Готово! Значения обновлены", reply_markup=markup)
        cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {};".format(user_id))
    elif (state == 4): # Добавление канла первый этап
        if (data == "Отмена"):
            cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {};".format(user_id))
            markup = get_start_markup (user_id)
            context.bot.send_message(user_id, "Возвращаем кнопочки", reply_markup=markup)
            return
        if (update.message.forward_from_chat == None):
            context.bot.send_message(user_id, "Вы отправили неправильные данные, попробуйте ещё раз")
            return
        link =  update.message.forward_from_chat.link
        chat_id = update.message.forward_from_chat.id
        if (link == None):
            cursor.execute("INSERT INTO `adtab` (`link`, `channel_id`) VALUES ('', %s)", (chat_id,))
            context.bot.send_message(user_id, "chat id добавлен, теперь отправьте ссылку на канал", markup=ReplyKeyboardRemove())
            cursor.execute("UPDATE `admins` SET `state` = 10, `tmp` = {1}  WHERE `user_id` = {0}".format(user_id, chat_id))
            return
        cursor.execute("INSERT INTO `adtab` (`link`, `channel_id`) VALUES (%s, %s)", (link, chat_id))
        markup = get_start_markup(user_id)
        context.bot.send_message(user_id, "Канал добавлен", reply_markup=markup)
        cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {}".format(user_id))
    elif (state == 5):
        send_all(update.message, context.bot)
    elif (state == 6):
        res = update_time_data(data, 1)
        if (res == False):
            context.bot.send_message(user_id, "Неправильный формат")
            return
        cursor.execute("UPDATE `admins` SET `state` = 7 WHERE `user_id` = {}".format(user_id))
        context.bot.send_message(user_id, "Значение изменено, теперь напишите время окончания действия викторины (такой же формат)")
    elif (state == 7):
        res = update_time_data(data, 3)
        if (res == False):
            context.bot.send_message(user_id, "Неправильный формат")
            return
        cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {}".format(user_id))
        markup = get_start_markup(user_id)
        context.bot.send_message(user_id, "Готово! Значение изменено", reply_markup=markup)
    elif (state == 8): # Обновление баланса, первый этап
        if (data == "Отмена"):
            cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {};".format(user_id))
            markup = get_start_markup (user_id)
            context.bot.send_message(user_id, "Возвращаем кнопочки", reply_markup=markup)
            return
        try:
            cursor.execute("UPDATE `admins` SET `tmp` = %s WHERE `user_id` = %s", (int(data),user_id))
        except Exception:
            context.bot.send_message(user_id, "Неправильные данные.")
        context.bot.send_message(user_id, "Отлично! Теперь перешлите новый баланс пользователя ")
        cursor.execute("UPDATE `admins` SET `state` = 9 WHERE `user_id` = {}".format(user_id))
    elif (state == 9): # Обновлени баланса, второй этап
        if (data == "Отмена"):
            cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {};".format(user_id))
            markup = get_start_markup (user_id)
            context.bot.send_message(user_id, "Возвращаем кнопочки", reply_markup=markup)
            return
        cursor.execute("SELECT `tmp` FROM `admins` WHERE `user_id` = {}".format(user_id))
        u_id = cursor.fetchone()[0]
        try:
            cursor.execute("UPDATE `users` SET `balance` = %s WHERE `user_id` = %s",(int(data), u_id))
        except Exception:
            context.bot.send_message(user_id, "Неправильные данные")
            return
        markup = get_start_markup(user_id)
        context.bot.send_message(user_id, "Данные обновлены", reply_markup=markup)
        cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {}".format(user_id))
        context.bot.send_message(u_id, "Проверьте ваш баланс")
    elif (state == 10): # Добавление канала второй этап
        res = re.match('https://t.me/joinchat/*', data)
        if (res == None):
            context.bot.send_message(user_id, "Неправильная ссылка, поппробуйте ещё раз")
        else:
            cursor.execute("SELECT `tmp` FROM `admins` WHERE `user_id` = {}".format(user_id))
            chat_id = cursor.fetchone()[0]
            cursor.execute("UPDATE `adtab` SET `link` = %s WHERE `channel_id` = %s",(data, chat_id))
            markup = get_start_markup(user_id)
            context.bot.send_message(user_id, "Канал добавлен", reply_markup=markup)
            cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {};".format(user_id))
    mydb.commit()
    
def update_time_data(data,id_data):
    now = datetime.now()
    if (re.match("[0-1][0-9].[0-3][0-9] [0-2][0-9]:[0-5][0-9]",data) != None): # MM.DD HH:MM:SS
        res = re.match("[0-1][0-9].[0-3][0-9] [0-2][0-9]:[0-5][0-9]",data)
        date = str(now.year) + "-" + res.group(0).replace('.', '-')
        cursor.execute("UPDATE `bot_settings` SET `date` = '{0}' WHERE `id` = {1}".format(date,id_data))
    elif (re.match("[0-3][0-9] [0-2][0-9]:[0-5][0-9]",data) != None): # DD HH:MM:SS
        res = re.match("[0-3][0-9] [0-2][0-9]:[0-5][0-9]",data)
        date = str(now.year) + "-" + str(now.month) + res.group(0)
        cursor.execute("UPDATE `bot_settings` SET `date` = '{0}' WHERE `id` = {1}".format(date,id_data))
    elif (re.match("[0-2][0-9]:[0-5][0-9]",data) != None): # HH:MM:SS
        res = re.match("[0-2][0-9]:[0-5][0-9]",data)
        date = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + " " + res.group(0)
        cursor.execute("UPDATE `bot_settings` SET `date` = '{0}' WHERE `id` = {1}".format(date,id_data))
    else:
        return False
    return True
def send_all(message, bot):
    user_id = message.from_user.id 
    if (message.text != None and message.text == "Готово!"):
        cursor.execute("UPDATE `admins` SET `state` = 0 WHERE `user_id` = {}".format(user_id))
        markup = get_start_markup(user_id)
        bot.send_message(user_id, "Сообщения отправлены!", reply_markup=markup)
        return
    cursor.execute("SELECT `user_id` FROM `users`")
    counter = 0
    while True:
        user_id_temp = cursor.fetchone()
        if (user_id_temp == None):
            break
        user_id_temp = user_id_temp[0]
        try:
            if (message.text != None):
                bot.send_message(user_id_temp, message.text)
            elif (message.audio != None):
                bot.send_audio(user_id_temp, message.audio)
            elif (message.document != None):
                bot.send_document(user_id_temp, message.document)
            elif (message.animation != None):
                bot.send_animation(user_id_temp, message.animation)
            elif (len(message.photo) != 0):
                bot.send_photo(user_id_temp, message.photo[0], caption=message.caption)
            elif (message.sticker != None):
                bot.send_sticker(user_id_temp, message.sticker)
            elif (message.video != None):
                bot.send_video(user_id_temp, message.video, caption=message.caption)
            elif (message.voice != None):
                bot.send_voice(user_id_temp, message.voice)
        except Exception:
            counter += 1
    bot.send_message(user_id, "{} пользователей остановило бота. Невозможно отправить сообщение.".format(counter))
    bot.send_message(user_id, "Отправлено!")

def add_question(update, context):
    user_id = update.message.from_user.id
    if (not is_admin(user_id, context.bot)):
        return
    cursor.execute("SELECT MAX(number) FROM `questions`")
    question_number = cursor.fetchone()
    if (question_number == None or question_number[0] == None):
        question_number = 0
    else:
        question_number = question_number[0]
    question_number = question_number + 1
    cursor.execute("UPDATE `admins` SET `state` = 1, `which_question_edit` = {1} WHERE `user_id` = {0}".format(user_id, question_number))
    cursor.execute("INSERT INTO `statistic` (`str_id`) VALUES ('{}')".format("q:" + str(question_number)))
    context.bot.send_message(user_id, "Отправьте новый вопрос")

def delete_questions(update, context):
    if (update.callback_query != None):
        user_id = update.callback_query.from_user.id
        if (not is_admin(user_id)):
            return
        data = update.callback_query.data.split(":")[1] # Информация, которую мы получаем - "d:{}" Где вместо {} номер вопросы
        if (data == "all"):
            cursor.execute("DELETE FROM `questions`")
            cursor.execute("DELETE FROM `statistic` WHERE `str_id` REGEXP('q:*')")
            context.bot.send_message(user_id, "Все вопросы удалены")
            return
        cursor.execute("DELETE FROM `questions` WHERE `number` = {0} ".format(data))
        cursor.execute("DELETE FROM `statistic` WHERE `str_id` = 'q:{}'".format(data))
        question_number = int(data) + 1
        while True: # Перемещаем все следующие вопросы на значение ниже.
            cursor.execute("SELECT `number` FROM `questions` WHERE `number` = {0} LIMIT 1".format(question_number))
            res = cursor.fetchone()
            if (res == None):
                break
            cursor.execute("UPDATE `questions` SET `number` = {0} WHERE `number` = {1}".format(question_number - 1, question_number)) 
            cursor.execute("UPDATE `statistic` SET `str_id` = 'q:{0}' WHERE `str_id` = 'q:{1}'".format(question_number - 1, question_number)) 
            question_number += 1
        context.bot.send_message(user_id, "Вопрос удалён")
        return
    user_id = update.message.from_user.id
    if (not is_admin(user_id, context.bot)):
            return
    cursor.execute("SELECT `number`, `data` FROM `questions` WHERE `type` = 1")
    result = cursor.fetchall()
    send = "выберете, какой вопрос удалить\n"
    inline_remove = []
    for q in result:
        send += str(q[0]) + ". " + q[1] + "\n"
        inline_remove.append([InlineKeyboardButton(q[0],callback_data="d:{0}".format(q[0]))])
    inline_remove.append([InlineKeyboardButton("Все",callback_data="d:all")])
    markup = InlineKeyboardMarkup(inline_remove)
    context.bot.send_message(user_id, send, reply_markup=markup)

def check_question(update, context):
    user_id = update.callback_query.from_user.id
    c_id = int(update.callback_query.data.split(":")[1])
    cursor.execute("SELECT `channel_id` FROM `adtab` WHERE `id` = {}".format(c_id))
    chat_id = cursor.fetchone()[0]
    time_left = to_datetime()
    cursor.execute("UPDATE `cache` SET `time_left` = '{0}' WHERE `user_id` = {1}".format(time_left, user_id))
    try:
        res = context.bot.get_chat_member(chat_id, user_id)
    except Exception:
        res = None
    if (res == None or res.status == res.LEFT or res.status == res.KICKED):
        context.bot.send_message(user_id, "Подписка не подтверждена")
        return
    cursor.execute("UPDATE `cache` SET `can_continue` = 1 WHERE `user_id` = {}".format(user_id))
    send_question(user_id, context.bot)
    mydb.commit()

def edit_ad(update, context):
    user_id = update.message.from_user.id
    if (not is_admin(user_id, context.bot)):
        return
    cursor.execute("SELECT * FROM `adtab` ")
    res = cursor.fetchall()
    markup = ReplyKeyboardMarkup([[KeyboardButton("Добавить канал")],[KeyboardButton("Разослать всем")],[KeyboardButton("Отмена")]], resize_keyboard=True)
    if (len(res) == 0):
        context.bot.send_message(user_id, "Нет никакой рекламы", reply_markup=markup)
    else:
        send_text = ""
        inline_markup = []
        counter = 1
        for a in res:
            send_text += str(counter) + ". " + a[1] + "\n"
            inline_markup.append([InlineKeyboardButton(counter, callback_data="da:{}".format(a[0]))])
            counter += 1
        inline_markup = InlineKeyboardMarkup(inline_markup)
        context.bot.send_message(user_id, send_text, reply_markup=inline_markup)
        pass
        context.bot.send_message(user_id, "Выберете действие", reply_markup=markup)

def add_channel(update, context):
    user_id = update.message.from_user.id
    if(not is_admin(user_id, context.bot)):
        return
    cursor.execute("UPDATE `admins` SET `state` = 4 WHERE `user_id` = {}".format(user_id))
    context.bot.send_message(user_id, "Отлично! Теперь перешлите сообщение из канала.")
    markup = ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    context.bot.send_message(user_id, "ВНИМАНИЕ! Бот должен быть админом на канале, который вы собираетесь рекламировать!!!", reply_markup=markup)

def delete_channel(update, context):
    user_id = update.callback_query.from_user.id
    c_id = int(update.callback_query.data.split(":")[1])
    cursor.execute("DELETE FROM `adtab` WHERE `id` = {}".format(c_id))
    context.bot.send_message(user_id, "Канал удалён!")
    mydb.commit()
    
def send_to_all(update, context):
    user_id = update.message.from_user.id
    if( not is_admin(user_id)):
        return
    cursor.execute("UPDATE `admins` SET `state` = 5 WHERE `user_id` = {}".format(user_id))
    markup = ReplyKeyboardMarkup([[KeyboardButton("Готово!")]], resize_keyboard=True)
    context.bot.send_message(user_id, "Отправьте сообщение, это может быть что угодно, изображение, аудио, текст и т.д. ", reply_markup=markup)

def statistic_func(update, context):
    user_id = update.message.from_user.id
    if (not is_admin(user_id, context.bot)):
        return
    send_data = "Статистика бота:\n\n"
    cursor.execute("SELECT COUNT(*) FROM `users`")
    res = cursor.fetchone()
    send_data += "Всего пользователей: {} \n".format(res[0])
    cursor.execute("SELECT `value` FROM `statistic` WHERE `str_id` = 'new users' LIMIT 1")
    res = cursor.fetchone()
    send_data += "Новых пользователей за сегодня: {} \n".format(res[0])
    send_data += "\nВопросы, на которые пользователи правильно ответили: \n"
    for i in range(1, 16):
        cursor.execute("SELECT `value` FROM `statistic` WHERE `str_id` = 'q:{}' LIMIT 1".format(i))
        res = cursor.fetchone()
        if (res == None):
            break
        send_data += "На вопрос {0}: правильно ответило {1} человек\n".format(i, res[0])
    context.bot.send_message(user_id, send_data)

def set_delayed_start(update, context):
    user_id = update.message.from_user.id
    if (not is_admin(user_id, context.bot)):
        return
    cursor.execute("UPDATE `admins` SET `state` = 6 WHERE `user_id` = {}".format(user_id))
    context.bot.send_message(user_id, "Отправьте время и дату вида MM.DD HH:MM:SS или только время HH:MM:SS", reply_markup=ReplyKeyboardRemove())

def balance(update, context):
    user_id = update.message.from_user.id
    cursor.execute("SELECT `balance` FROM `users` WHERE `user_id` = {}".format(user_id))
    balance = cursor.fetchone()[0]
    markup = ReplyKeyboardMarkup([[KeyboardButton("Вывести")],[KeyboardButton("Отмена")]], resize_keyboard=True)
    context.bot.send_message(user_id, "Ваш баланс: {}".format(balance), reply_markup=markup)

def out_balance(update, context):
    user_id = update.message.from_user.id
    cursor.execute("SELECT `balance` FROM `users` WHERE `user_id` = {}".format(user_id))
    balance = cursor.fetchone()[0]
    if (balance < 100):
        context.bot.send_message(user_id, "Минимальная сумма вывода - 100 р")
        return
    context.bot.send_message(user_id, "Хорошо! Отправьте ваш QIWI кошелёк. Отправьте в виде +7XXXXXXXXXX", reply_markup=ReplyKeyboardRemove())
    cursor.execute("UPDATE `users` SET `state` = 1 WHERE `user_id` = {}".format(user_id))

def user_input(update, context):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    data = update.message.text
    cursor.execute("SELECT `state` FROM `users` WHERE `user_id` = {}".format(user_id))
    state = cursor.fetchone()[0]
    if (state != 1):
        return False # Ошибка, стадия не найдена
    res = re.match('[0-9\-\+]{9,15}$',data)
    if (res == None):
        context.bot.send_message(user_id, "Неправильный формат. Отправьте в виде +7XXXXXXXXXX")
        return True
    cursor.execute("SELECT `user_id` FROM `admins`")
    adm = cursor.fetchall()
    cursor.execute("SELECT `balance` FROM `users` WHERE `user_id` = {}".format(user_id))
    balance = cursor.fetchone()[0]
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("Готово!", callback_data="r:{}".format(user_id))]])
    for a in adm:
        context.bot.send_message(a[0], "Пользователь @{0} Желает вывести средства. Его баланс - {1}р.; user id - {2}; карта QIWI - {3}".format(username, balance, user_id, res.group(0)),reply_markup=markup)
    markup_u = get_start_markup(user_id)
    context.bot.send_message(user_id, "Запрос на вывод отправлен. В ближайшее время сумма будет переведена на ваш счёт",reply_markup=markup_u)
    cursor.execute("UPDATE `users` SET `state` = 0 WHERE `user_id` = {}".format(user_id))
    return True

def send_ready(update, context):
    user_id = update.callback_query.from_user.id
    u_id = int(update.callback_query.data.split(":")[1])
    context.bot.send_message(u_id, "Проверьте ваш QIWI счёт.")
    cursor.execute("UPDATE `users` SET `balance` = 0 WHERE `user_id` = {}".format(u_id))
    markup = get_start_markup(user_id)
    context.bot.send_message(user_id, "Изменение подтверждено",reply_markup=markup)
    context.bot.delete_message(user_id, update.callback_query.message.message_id)

def set_balance(update, context):
    user_id = update.message.from_user.id
    if (not is_admin(user_id, context.bot)):
        return
    #which_question_edit
    cursor.execute("UPDATE `admins` SET `state` = 8 WHERE `user_id` = {}".format(user_id))
    markup = ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    context.bot.send_message(user_id, "Теперь отправьте user id пользователя, баланс которого желаете изменить",reply_markup=markup)

def reklama(update, context):
    user_id = update.message.from_user.id
    context.bot.send_message(user_id, "По поводу рекламы обращаться @Username")

def channel_chat(update, context):
    user_id = update.message.from_user.id
    context.bot.send_message(user_id, "https://t.me/joinchat/AAAChannel - канал\nhttps://t.me/joinchat/BBBChannel - чат ")

def default(update, context):
    user_id = update.message.from_user.id
    cursor.execute("UPDATE `admins` SET `state` = 0, `which_question_edit` = 0 WHERE `user_id` = {0}".format(user_id))
    markup = get_start_markup(user_id)
    context.bot.send_message(user_id, "Возвращаемся обратно", reply_markup=markup)

def mainFunc(update, context): # Основная функция, через неё проходят все запросы
    global mydb
    mydb.commit()
    functions = {
        "🎲 Играть": Victorine, # Здесь нахордяться все функции бота
        "Админка": admin_func,
        "В главное меню":back_to_main_menu,
        "Редактировать вопросы": edit_opros,
        "Создать новый вопрос":add_question,
        "Удалить вопрос":delete_questions,
        "Отмена": default,
        "Отправить рекламу":edit_ad,
        "Добавить канал":add_channel,
        "Разослать всем": send_to_all,
        "Статистика":statistic_func,
        "Установить время запуска викторины":set_delayed_start,
        "💰 Баланс":balance,
        "Вывести":out_balance,
        "Установить баланс":set_balance,
        "🔔 Реклама":reklama,
        "💬 Канал и чат":channel_chat

    }
    command = update.message.text
    user_id = update.message.from_user.id # Id пользователя, используеться для отправки сообщений
    exist_user(user_id)
    cursor.execute("SELECT `user_id` FROM `users` WHERE `user_id` = {0}  AND `state` = 2;".format(user_id))
    res = cursor.fetchone()
    if (res != None):
        Victorine(update, context)
        return
    cursor.execute("SELECT `state` FROM `admins` WHERE `user_id` = {0} AND `state` > 0 AND `is_admin_edit` = 1;".format(user_id))
    res = cursor.fetchone()
    if (res != None):
        admin_input(update, context, res[0])
        return
    if (command in functions): # Проверяем, есть ли такая функция.
        functions[command](update, context)
    else: # Если нет, то отправляем это сообщение 
        if (user_input(update, context)): 
            return
        markup = get_start_markup(user_id)
        context.bot.send_message(user_id,"Извините, но я не знаю такой команды, воспользуйтесь клавиатурой", reply_markup=markup)


def error_callback (update, context):
    print(context.error)
    try:
        user_id = update.message.from_user.id
        context.bot.send_message(user_id, "Произошла ошибка - {}".format(context.error))
    except Exception:
        context.bot.send_message(613595894, "Произошла ошибка - {}".format(context.error))
    #raise context.error
def log(update, context):
    now = datetime.now()
    cursor.execute("SELECT * FROM `admins`")
    admins = cursor.fetchall()
    cursor.execute("SELECT * FROM `adtab`")
    adtab = cursor.fetchall()
    cursor.execute("SELECT * FROM `bot_settings`")
    bot_settings = cursor.fetchall()
    cursor.execute("SELECT * FROM `cache`")
    cache = cursor.fetchall()
    cursor.execute("SELECT * FROM `questions`")
    questions = cursor.fetchall()
    cursor.execute("SELECT * FROM `statistic`")
    statistic = cursor.fetchall()
    cursor.execute("SELECT * FROM `users`")
    users = cursor.fetchall()
    f = open('/home/bot/log.txt', 'a')
    f.write("Now - " + now.time().strftime("%H:%M:%S") + '\n')
    for adm in admins:
        f.write("admin: " + str(adm) + '\n')
    f.write("adtab" + str(adtab) + '\n')
    
    for b in bot_settings:
        f.write("bot_settings: " + str(b) + '\n')
    f.write('\n')
    for c in cache:
        f.write("cache: " + str(c) + '\n')
    f.write('\n')
    for q in questions:
        f.write("questions: " + str(q) + '\n')
    f.write('\n')
    f.write("statistic" + str(statistic) + '\n')
    f.write('\n')
    for u in users:
        f.write("user: " + str(u) + '\n')
    if (context.error != None):
        f.write("Error - {} \n".format(context.error))
    f.close()
    context.bot.send_message(update.message.from_user.id, "Логи записаны")

def delete_everyday():
    job_cursor.execute("UPDATE `statistic` SET `value` = 0 WHERE `str_id` = 'new users'")

updater = Updater(TOKEN, use_context=True)
#updater = Updater('880375912:AAHqAxX1P_RFCyuU3ers0vnNpQpKyzWMY24', use_context=True)

updater.dispatcher.add_error_handler(error_callback)
updater.dispatcher.add_handler(CommandHandler('id', get_id))
updater.dispatcher.add_handler(CommandHandler('log', log))
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.all, mainFunc))

updater.dispatcher.add_handler(CallbackQueryHandler(edit_question, pattern="q:\d"))
updater.dispatcher.add_handler(CallbackQueryHandler(delete_channel, pattern="da:\d"))
updater.dispatcher.add_handler(CallbackQueryHandler(delete_questions, pattern="d:(\d|all)"))
updater.dispatcher.add_handler(CallbackQueryHandler(check_question, pattern="c:\d"))
updater.dispatcher.add_handler(CallbackQueryHandler(send_ready, pattern="r:\d"))
#run_daily

updater.job_queue.run_repeating(time_controller,1,0)
updater.job_queue.run_repeating(delayed_start,60,0)
date = datetime.now().time()
updater.job_queue.run_daily(delayed_start,date)
try:
    updater.start_polling()
    updater.idle()
except KeyboardInterrupt:
    cursor.close()
    job_cursor.close()
    mydb.close()
    jobdb.close()
