import sqlite3
from tkinter import *
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from tkinter import PhotoImage
from PIL import Image, ImageTk
from tkinter import END, Button

# Создание базы данных и таблиц
conn = sqlite3.connect('fitness_app.db')
c = conn.cursor()

# Создание таблицы категорий тренировок
c.execute('''
    CREATE TABLE IF NOT EXISTS training_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
''')

# Создание таблицы пользователей
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        phone TEXT NOT NULL
    )
''')

# Создание таблицы тренировок
c.execute('''
    CREATE TABLE IF NOT EXISTS trainings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        duration INTEGER NOT NULL, 
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES training_categories(id) ON DELETE SET NULL
    )
''')

# Создание таблицы регистраций пользователей на тренировки
c.execute('''
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        trening INTEGER NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
        FOREIGN KEY (trening) REFERENCES trainings(id) ON DELETE CASCADE
    )
''')

# Создание таблицы подписок пользователей
c.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        subscription_type TEXT,
        price INTEGER,
        purchase_date DATETIME,
        expiration_date DATETIME,
        FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
    )
''')

# Создание таблицы платежей для подписок
c.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        amount INTEGER NOT NULL,
        payment_date DATETIME NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
    )
''')

conn.commit()

# Переменные для хранения текущего пользователя и статуса администратора
logged_in_user = None
is_admin = False


def get_users():
    c.execute("SELECT username, phone FROM users")
    return c.fetchall()

def get_subscriptions(username):
    try:
        c.execute("SELECT subscription_type, price, purchase_date, expiration_date FROM subscriptions WHERE username=?", (username,))
        return c.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка БД", f"Ошибка при получении абонементов: {e}")
        return []

def get_registrations(username):
    if not username:
        return []

    try:
        c.execute("SELECT id, trening, date FROM registrations WHERE username=?", (username,))
        return c.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка БД", f"Ошибка при получении записей: {e}")
        return []


def show_user_registrations(username):
    registrations = get_registrations(username)  # Получение записей пользователя
    if registrations:
        registration_info = '\n'.join([f"{r[1]} - {r[2]}" for r in registrations])  # Изменено чтобы отображать нужные данные
        messagebox.showinfo(f"Записи пользователя: {username}", registration_info)
    else:
        messagebox.showinfo("Записи", f"У пользователя {username} нет записей на занятия.")

def refresh_users(user_text_widget):
    user_text_widget.delete(1.0, END)
    users = get_users()
    if users:
        for user in users:
            user_info = f"Логин: {user[0]}, Телефон: {user[1]}\n"
            user_text_widget.insert(END, user_info)

            view_subs_button = Button(user_text_widget.winfo_toplevel(), text="Показать абонементы",
                                      command=lambda u=user[0]: show_user_subscriptions(u))
            user_text_widget.window_create(END, window=view_subs_button)

            view_regs_button = Button(user_text_widget.winfo_toplevel(), text="Показать записи",
                                      command=lambda u=user[0]: show_user_registrations(u))
            user_text_widget.window_create(END, window=view_regs_button)

            delete_button = Button(user_text_widget.winfo_toplevel(), text="Удалить",
                                   command=lambda u=user[0]: delete_user(u, user_text_widget))
            user_text_widget.window_create(END, window=delete_button)

            user_text_widget.insert(END, "\n")
    else:
        user_text_widget.insert(END, "Нет пользователей\n")

def show_all_registrations():
    try:
        c.execute("SELECT username, trening, date FROM registrations")
        all_registrations = c.fetchall()

        if all_registrations:
            registration_info = '\n'.join(
                [f"Пользователь: {r[0]}, Тренировка: {r[1]}, Дата: {r[2]}" for r in all_registrations])
            messagebox.showinfo("Все записи на тренировки", registration_info)
        else:
            messagebox.showinfo("Записи", "Нет записей на тренировки.")
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка БД", f"Ошибка при получении всех записей: {e}")


def delete_user(username, user_text_widget):
    try:
        c.execute("DELETE FROM registrations WHERE username=?", (username,))
        c.execute("DELETE FROM subscriptions WHERE username=?", (username,))
        c.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        messagebox.showinfo("Успех", f"Пользователь {username} и все связанные данные успешно удалены.")
        refresh_users(user_text_widget)
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при удалении пользователя: {e}")

def show_user_subscriptions(username):
    subscriptions = get_subscriptions(username)
    if subscriptions:
        subscription_info = '\n'.join(
            [f"{s[0]} - {s[1]} руб, куплено: {s[2]}, срок действия: {s[3]}" for s in subscriptions])
        messagebox.showinfo(f"Абонементы пользователя: {username}", subscription_info)
    else:
        messagebox.showinfo("Абонементы", f"У пользователя {username} нет абонементов.")


def open_user_window():
    user_window = Toplevel(root)
    user_window.title("Пользователи")
    user_window.geometry("520x270")

    users_text = Text(user_window, width=50, height=15, font=("Britannic Bold", 12), bg="#3B4451", fg="#FFFFFF")
    users_text.pack(pady=10)

    refresh_users(users_text)




def login(username, password):
    global logged_in_user, is_admin
    if username == 'admin' and password == '123':
        is_admin = True
        messagebox.showinfo("Успех", "Добро пожаловать, администратор!")
        open_user_window()  # Открываем окно пользователей для администратора
    else:
        logged_in_user = find_user(username, password)
        if logged_in_user:
            messagebox.showinfo("Успех", f"Добро пожаловать, {logged_in_user[0]}!")
            update_profile_info(logged_in_user[0], logged_in_user[1])
            toggle_auth_buttons()  # Обновляем состояние кнопок
        else:
            messagebox.showerror("Ошибка", "Неверные логин или пароль.")


def clear_records():
    if not logged_in_user:
        messagebox.showwarning("Предупреждение", "Сначала войдите в профиль.")
        return
    clear_records_window()


def clear_records_window():
    clear_window = Toplevel(root)
    clear_window.title("Очистить записи")
    clear_window.geometry("500x300")
    clear_window.configure(bg="#232D3F")

    records_listbox = Listbox(clear_window, selectmode=SINGLE)
    records_listbox.pack(pady=10, fill="both", expand=True)

    def display_records():
        records_listbox.delete(0, END)  # Очищаем Listbox
        registrations = get_registrations(logged_in_user[0])  # Обновляем записи для текущего пользователя

        for record in registrations:
            if len(record) < 3:
                messagebox.showwarning("Ошибка", "Некорректные данные записей. Проверьте базу данных.")
                continue  # Пропускаем некорректные записи
            record_info = f"ID: {record[0]}, Тренировка: {record[1]}, Дата: {record[2]}"
            records_listbox.insert(END, record_info)

    def delete_selected_records():
        selected_indices = records_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Информация", "Выберите записи для удаления.")
            return

        try:
            for index in selected_indices:
                record_info = records_listbox.get(index)
                record_id = int(record_info.split(',')[0].split(': ')[1])  # Извлекаем ID из строки

                # Удаляем запись по ID
                c.execute("DELETE FROM registrations WHERE id=?", (record_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Выбранные записи успешно удалены.")
            display_records()  # Обновляем записи в Listbox после удаления
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении записей: {e}")

    delete_button = Button(clear_window, text="Удалить выбранные", background="#CDC3BD",
                           font=("Britannic Bold", 14), command=delete_selected_records)
    delete_button.pack(pady=10)

    # Первичная загрузка записей
    display_records()



def add_registration(username, trening, date):
    if username is None:
        messagebox.showwarning("Ошибка", "Пожалуйста, войдите в профиль, чтобы записаться на занятия.")
        return

    # Преобразуем строку даты в объект datetime для сравнения
    try:
        selected_date = datetime.strptime(date, '%d-%m-%Y').date()  # Преобразуем строку в дату
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты!")
        return

    today = datetime.today().date()  # Получаем сегодняшнюю дату

    # Проверка на прошедшую дату
    if selected_date < today:
        messagebox.showerror("Ошибка", "Нельзя записаться на прошедшую дату!")
        return

    try:
        # Проверка на наличие записи с таким же username, date и trening
        c.execute('SELECT COUNT(*) FROM registrations WHERE username=? AND date=? AND trening=?',
                  (username, date, trening))
        count = c.fetchone()[0]

        if count > 0:
            messagebox.showwarning("Ошибка", "Вы уже записаны на эту тренировку в эту дату!")
            return

        # Вставка новой записи, если всё в порядке
        c.execute('INSERT INTO registrations (username, trening, date) VALUES (?, ?, ?)', (username, trening, date))
        conn.commit()
        messagebox.showinfo("Успех", "Вы успешно записались!")
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при добавлении записи: {e}")

def find_user(username, password):
    c.execute("SELECT username, phone FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()


def register_user(username, password, phone):
    try:
        c.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)", (username, password, phone))
        conn.commit()
        messagebox.showinfo("Успех", "Регистрация прошла успешно!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует.")


def open_purchase_window():
    global logged_in_user
    if logged_in_user is None:
        messagebox.showwarning("Ошибка", "Пожалуйста, войдите в профиль, чтобы купить абонемент.")
        return

    # Проверка на наличие уже купленного абонемента
    c.execute("SELECT * FROM subscriptions WHERE username=?", (logged_in_user[0],))
    existing_subscription = c.fetchone()

    if existing_subscription:
        # Показываем информацию о существующем абонементе
        show_subscription(existing_subscription)
        return

    purchase_window = Toplevel(root)
    purchase_window.title("Покупка абонемента")

    # Заголовок окна по центру
    title_label = Label(purchase_window, text="Абонементы", font=("Britannic Bold", 18), bg="#232D3F", fg="#FFFFFF")
    title_label.grid(row=0, column=0, columnspan=2, pady=10)

    # Создание рамки для годового абонемента
    yearly_frame = Frame(purchase_window, bg="#3B4451", bd=2, relief="groove")
    yearly_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    yearly_info = (
        "На год:\n"
        "    - Круглосуточное посещение фитнес-зала\n"
        "    - Полотенце на каждой тренировке\n"
        "    - Скидка на продление 25%\n"
        "    - Групповые занятия\n"
        "    - Пользование раздевалкой\n"
        "    - Дополнительные услуги: сауна, бассейн, массаж"
    )
    Label(yearly_frame, text=yearly_info, font=("Britannic Bold", 16), bg="#3B4451", fg="#FFFFFF", anchor="w", justify="left").pack(pady=5)

    # Кнопка покупки годового абонемента
    Button(yearly_frame, text="Цена: 30.000 руб.", background="#CDC3BD", font=("Britannic Bold", 14),
           command=lambda: buy_subscription("Годовой", 30000, purchase_window)).pack(pady=5)

    # Создание рамки для месячного абонемента
    monthly_frame = Frame(purchase_window, bg="#3B4451", bd=2, relief="groove")
    monthly_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")

    monthly_info = (
        "На месяц:\n"
        "    - Круглосуточное посещение фитнес-зала\n"
        "    - Скидка на продление 25%\n"
        "    - Групповые занятия\n"
        "    - Пользование раздевалкой"
    )
    Label(monthly_frame, text=monthly_info, font=("Britannic Bold", 16), bg="#3B4451", fg="#FFFFFF", anchor="w", justify="left").pack(pady=5)

    # Кнопка покупки месячного абонемента
    Button(monthly_frame, text="Цена: 3.500 руб.", background="#CDC3BD", font=("Britannic Bold", 14),
           command=lambda: buy_subscription("Месячный", 3500, purchase_window)).pack(pady=5)

    purchase_window.configure(bg="#232D3F")
    purchase_window.geometry("1100x300")  # Увеличил размер окна для лучшего отображения информации

def buy_subscription(subscription_type, price, purchase_window=None):
    purchase_date = datetime.now().strftime("%Y-%m-%d")
    expiration_date = (datetime.now() + timedelta(days=365)).strftime(
        "%Y-%m-%d") if subscription_type == "Годовой" else (
            datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        c.execute(
            "INSERT INTO subscriptions (username, subscription_type, price, purchase_date, expiration_date) VALUES (?, ?, ?, ?, ?)",
            (logged_in_user[0], subscription_type, price, purchase_date, expiration_date))
        conn.commit()
        messagebox.showinfo("Успех", f"Вы успешно купили {subscription_type.lower()} абонемент за {price} рублей!")
        purchase_window.destroy()
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при покупке абонемента: {e}")


def open_registration_window():
    reg_window = Toplevel()
    reg_window.title("Регистрация")
    reg_window.geometry("300x250")

    Label(reg_window, text="Логин:", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 14)).pack(
        pady=5)
    username_entry = Entry(reg_window)
    username_entry.pack(pady=5)

    Label(reg_window, text="Пароль:", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 14)).pack(
        pady=5)
    password_entry = Entry(reg_window, show='*')
    password_entry.pack(pady=5)

    Label(reg_window, text="Телефон:", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 14)).pack(
        pady=5)

    # Настройка проверки ввода для номера телефона
    phone_entry = Entry(reg_window)
    phone_entry.pack(pady=5)

    def validate_phone_input(new_value):
        # Проверяем, что ввод соответствует правилам:
        # - только цифры
        # - длина не больше 11
        if new_value == "":
            return True  # разрешить пустое поле
        if len(new_value) > 11:
            return False  # запрещаем ввод, если больше 11
        if not new_value.isdigit():
            return False  # запрещаем, если не цифры
        return True  # разрешить ввод

    # Регистрация функции валидации и установка ограничения на ввод для телефона
    validate_command = reg_window.register(validate_phone_input)
    phone_entry.configure(validate="key", validatecommand=(validate_command, '%P'))

    reg_window.configure(bg="#232D3F")

    def save_registration():
        username = username_entry.get()
        password = password_entry.get()
        phone = phone_entry.get()

        # Проверка на заполнение всех полей
        if all([username, password, phone]):
            register_user(username, password, phone)
            reg_window.destroy()
            update_profile_info(username, phone)  # Обновление информации в профиле
        else:
            messagebox.showwarning("Ошибка", "Пожалуйста, заполните все поля!")

    reg_button = Button(reg_window, text="Зарегистрироваться", background="#CDC3BD", font=("Britannic Bold", 14),
                        command=save_registration)
    reg_button.pack(pady=10)


def open_login_window():
    login_window = Toplevel()
    login_window.title("Вход")
    login_window.geometry("300x200")

    Label(login_window, text="Логин:",foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 14)).pack(pady=5)
    username_entry = Entry(login_window)
    username_entry.pack(pady=5)

    Label(login_window, text="Пароль:",foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 14)).pack(pady=5)
    password_entry = Entry(login_window, show='*')
    password_entry.pack(pady=5)

    login_button = Button(login_window, text="Войти",background="#CDC3BD",font=("Britannic Bold", 14), command=lambda: login(username_entry.get(), password_entry.get()))
    login_button.pack(pady=10)
    login_window.configure(bg="#232D3F")


def show_records(username=None):
    if username is None:
        username = logged_in_user[0] if logged_in_user else None

    if username is None:
        messagebox.showwarning("Ошибка", "Пожалуйста, войдите в профиль, чтобы увидеть свои записи.")
        return

    try:
        # Изменяем запрос так, чтобы выбирались только записи для текущего пользователя
        c.execute('SELECT * FROM registrations WHERE username=?', (username,))
        records = c.fetchall()

        if records:
            result = f"Записи для пользователя: {username}\n\n" + '\n'.join([
                f'Trening: {r[2]}, Date: {r[3]}'
                for r in records
            ])
            messagebox.showinfo("Записи", result)
        else:
            messagebox.showinfo("Записи", f"У пользователя {username} нет записей.")
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при получении записей: {e}")


# Функция для переключения между страницами
def show_frame(frame):
    frame.tkraise()


# Функция для показа информации о тренировки
def show_workout_info1():
    messagebox.showinfo("Информация о тренировке",
                        "Силовая тренировка — это физическая активность, направленная на развитие и укрепление мышц с помощью различных упражнений и методов.\n Она включает в себя использование свободных весов, тренажеров, а также собственный вес тела.")

def show_workout_info2():
    messagebox.showinfo("Информация о тренировке",
                        "Кардио тренировка — это физическая активность, направленная на улучшение сердечно-сосудистой системы и повышение выносливости.\n Она включает аеробные упражнения, такие как бег, плавание, танцевальные и другие виды активности, которые увеличивают частоту сердечных сокращений.")

def show_workout_info3():
    messagebox.showinfo("Информация о тренировке",
                        "Йога — это древняя практика, основывающаяся на философских и духовных учениях, которая сочетает физические упражнения, дыхательные техники и медитацию.\n Она направлена на развитие тела, ума и духа, способствует улучшению физической гибкости, силы, а также психологического равновесия и душевного спокойствия.\n Йога помогает справиться со стрессом, улучшает общее самочувствие и способствует гармонии между телом и разумом.")

def show_workout_info4():
    messagebox.showinfo("Информация о тренировке",
                        "Спортивные танцы — это дисциплина, которая включает в себя танцы, исполняемые в рамках соревнований, как парные, так и соло.\n Они охватывают различные стили, такие как бальные, латинские танцы и современные направления.\n Спортивные танцы развивают координацию, гибкость, физическую подготовку и чувство ритма, а также способствуют социализации и укреплению эмоционального состояния.\n Занятия танцами помогают улучшить настроение, снять стресс и повысить уверенность в себе.")

def show_workout_info11():
    messagebox.showinfo("Иванихин Алексей",
                        "Алексей — профессиональный спортсмен в таких направлениях, как Кикбоксинг и борьба, "
                        "победитель и призёр множества соревнований.\n\n"
                        "Мастер спорта России по пауэрлифтингу и кикбоксингу, рекордсмен, призёр и абсолютный чемпион Москвы, МО и ЦФО.\n\n"
                        "Работает с:\n"
                        "- коррекцией веса и фигуры,\n"
                        "- улучшением скоростно-силовых качеств,\n"
                        "- реабилитацией после травм,\n"
                        "- подготовкой к соревнованиям по пауэрлифтингу.")

def show_workout_info22():
    messagebox.showinfo( "Прокопович Анна",
        "Инструктор по кардио тренировкам.\n\n"
        "Рожденная в спортивной семье, Анна не смогла остаться к этому равнодушной.\n"
        "С детства увлекается игровыми видами спорта, посвятила себя легкой атлетике и современной хореографии.\n\n"
        "Любит заряжать энергетикой и позитивом даже после самого тяжелого дня, чтобы люди не только ощущали пользу занятий, "
        "но и были частью большой семьи!")

def show_workout_info33():
        messagebox.showinfo("Шаргородская Яна",
                            "Инструктор по йоге.\nОпыт работы 16 лет. \nНравится видеть изменения в людях и на физическом и на эмоциональном уровне.")


def show_workout_info44():
        messagebox.showinfo("Игантьева Екатерина",
        "Инструктор по спортивным танцам.\n\n"
        "Екатерина пришла в фитнес из профессионального спорта, является кандидатом в мастера спорта по плаванию.\n"
        "Во время обучения на геодезическую специальность в КМПО РАНХиГС она поняла, что хочет работать с людьми и "
        "погрузилась в изучение преподавания танцев. Теперь она развивается в обоих направлениях.\n\n"
        "Групповые тренировки полюбила с первого взгляда за положительные эмоции и отличную нагрузку.\n"
        "Больше всего в работе ей нравится видеть улыбки клиентов и радоваться их результатам!")


def show_main_window():
    # Удаление окна приветствия
    welcome_window.destroy()

    # Теперь запускаем основное приложение
    root.deiconify()  # Показываем главное окно


# Окно приветствия
def show_welcome_window():
    global welcome_window
    welcome_window = Toplevel()
    welcome_window.title("Добро пожаловать в ALEX-FIT")
    welcome_window.geometry("520x450")
    welcome_window.configure(bg="#232D3F")

    # Загрузка изображения с использованием Pillow
    logo_image = Image.open(r"C:\Users\alexs\OneDrive\Рабочий стол\pic\logo_1.png")  # Замените на файл с вашим логотипом
    logo_image = logo_image.resize((480, 320), Image.LANCZOS)  # Изменение размера изображения, если необходимо
    logo_image = ImageTk.PhotoImage(logo_image)

    # Виджет с изображением
    logo_label = Label(welcome_window, image=logo_image, bg="#232D3F")
    logo_label.image = logo_image  # Сохраните ссылку для предотвращения сборки мусора
    logo_label.pack(pady=20)

    # Кнопка "Продолжить"
    continue_button = Button(welcome_window, text="Продолжить", command=show_main_window, bg="#CDC3BD",
                             font=("Britannic Bold", 18))
    continue_button.pack(pady=20)

    welcome_window.protocol("WM_DELETE_WINDOW", root.quit)  # Закрытие приложения при закрытии окна приветствия

# GUI основного приложения
root = Tk()
root.title("ALEX-FIT")
root.geometry("520x450")
root.configure(bg="#232D3F")

# Ограничение возможности изменения размера окна
root.resizable(False, False)

# Скрываем основное окно пока не нажмем "Продолжить"
root.withdraw()  # Скрываем главное окно

show_welcome_window()  # Показываем окно приветствия


# Создаем фреймы для каждой страницы
club_frame = Frame(root)
workout_frame = Frame(root)
profile_frame = Frame(root)
schedule_frame = Frame(root)

for frame in (club_frame, workout_frame, profile_frame, schedule_frame):
    frame.grid(row=0, column=0, sticky='news')


# Кнопки для переключения страниц
def create_navigation_buttons():
    button_frame = Frame(root)
    button_frame.grid(row=2, column=0, sticky='ew')

    # Настраиваем грид для заполнения всего пространства
    button_frame.grid_rowconfigure(0, weight=1)
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    button_frame.grid_columnconfigure(2, weight=1)
    button_frame.grid_columnconfigure(3, weight=1)

    # Функция для создания кнопок с изображениями
    def create_button(image_path, command, text="", row=0, column=0):
        # Загружаем изображение
        img = Image.open(image_path)
        img = img.resize((55, 55), Image.LANCZOS)  # Изменяем размер изображения, сохраняя пропорции
        photo = ImageTk.PhotoImage(img)  # Создаем объект PhotoImage

        # Создаем кнопку с изображением и текстом
        button = Button(button_frame, image=photo, text=text, compound='top',
                        background="#CDC3BD", font=("Britannic Bold", 12),
                        command=command)

        button.image = photo  # Сохраняем ссылку на изображение
        button.grid(row=row, column=column, sticky='nsew')  # Размещаем кнопку в гриде

    # Создаем кнопки с изображениями
    create_button(r"C:\Users\alexs\OneDrive\Рабочий стол\pic\place.png", lambda: show_frame(club_frame), "Клубы", row=0, column=0)
    create_button(r"C:\Users\alexs\OneDrive\Рабочий стол\pic\hand_1.png", lambda: show_frame(workout_frame), "Тренировки", row=0, column=1)
    create_button(r"C:\Users\alexs\OneDrive\Рабочий стол\pic\calendar.png", lambda: show_frame(schedule_frame), "Расписание", row=0, column=2)
    create_button(r"C:\Users\alexs\OneDrive\Рабочий стол\pic\men.png", lambda: show_frame(profile_frame), "Профиль", row=0, column=3)

# Создаем навигационные кнопки
create_navigation_buttons()

# Установим размеры для самой рамки, чтобы она заполнила всё пространство
root.grid_rowconfigure(1, weight=1)


# Страница "Клубы"
Label(club_frame, text="ALEX-FIT", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 20)).pack(anchor=N)
Label(club_frame, text="Г.Москва", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 16)).pack(anchor=NW)
Label(club_frame, text="Метро: Академическая", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 16)).pack(anchor=NW)
Label(club_frame, text="Адрес: Новочерёмушкинская 24", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 16)).pack(anchor=NW)
Label(club_frame, text="Номер телефона: +7 926 312 72 74", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 16)).pack(anchor=NW)
Label(club_frame, text="Электронная почта: Alexs050956@mail.ru", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 16)).pack(anchor=NW)
Label(club_frame, text="График работы: ежедневно с 7:00 - 24:00", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 16)).pack(anchor=NW)
club_frame.configure(bg="#232D3F")

# Страница "Тренировки"
Label(workout_frame, text="Список занятий", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 20)).grid(row=0, column=0, padx=10, pady=(10, 5), sticky=N + S + E + W)

# Информация о тренировках
Label(workout_frame, text="Силовая тренировка", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 15)).grid(row=1, column=0, padx=10, pady=5, sticky=N + W)
info1_button = Button(workout_frame, text="Что входит", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info1)
info1_button.grid(row=2, column=0, padx=10, pady=5, sticky=N + W)
info11_button = Button(workout_frame, text="Тренер", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info11)
info11_button.grid(row=3, column=0, padx=10, pady=5, sticky=N + W)

# Кардио тренировка
Label(workout_frame, text="Кардио тренировка", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 15)).grid(row=1, column=1, padx=10, pady=5, sticky=N + E)
info2_button = Button(workout_frame, text="Что входит", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info2)
info2_button.grid(row=2, column=1, padx=10, pady=5, sticky=N + E)
info22_button = Button(workout_frame, text="Тренер", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info22)
info22_button.grid(row=3, column=1, padx=10, pady=5, sticky=N + E)

# Йога
Label(workout_frame, text="Йога", foreground="#CDC3BD", background="#232D3F", width=15, font=("Britannic Bold", 15)).grid(row=4, column=0, padx=10, pady=5, sticky=N + W)
info3_button = Button(workout_frame, text="Что входит", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info3)
info3_button.grid(row=5, column=0, padx=10, pady=5, sticky=N + W)
info33_button = Button(workout_frame, text="Тренер", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info33)
info33_button.grid(row=6, column=0, padx=10, pady=5, sticky=N + W)

# Спортивные танцы
Label(workout_frame, text="Спортивные танцы", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 15)).grid(row=4, column=1, padx=10, pady=5, sticky=N + E)
info4_button = Button(workout_frame, text="Что входит", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info4)
info4_button.grid(row=5, column=1, padx=10, pady=5, sticky=N + E)
info44_button = Button(workout_frame, text="Тренер", background="#E5E0D6", font=("Britannic Bold", 12), width=20, command=show_workout_info44)
info44_button.grid(row=6, column=1, padx=10, pady=5, sticky=N + E)

workout_frame.configure(bg="#232D3F")


def show_subscription(subscription=None):
    if subscription is None:
        messagebox.showinfo("Информация об абонементе", "Абонемент активен.")
        return
    # Получаем сегодняшнюю дату
    today_date = datetime.now().strftime("%Y-%m-%d")
    # Отображаем информацию об абонементе
    subscription_info = (
        f"Тип абонемента: {subscription[2]}\n"
        f"Цена: {subscription[3]} руб.\n"
        f"Дата покупки: {today_date}\n"  # Используем сегодняшнюю дату
        f"Дата окончания: {subscription[5]}"
    )
    messagebox.showinfo("Информация об абонементе", subscription_info)

# Страница "Профиль"
Label(profile_frame, text="ALEX-FIT", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 20)).pack(anchor=N)

# Предварительно создадим место для информации о профиля
info_frame = Frame(profile_frame, width=50, height=50, background="#232D3F")
info_frame.pack(pady=5)  # Добавляем фрейм с отступом


# Функция обновления информации о профиле
def update_profile_info(username, phone):
    # Устаревшую метку логина удаляем, если она есть
    for widget in info_frame.winfo_children():
        widget.destroy()

    if username:  # Если пользователь авторизован
        # Создаём метку для логина
        username_label = Label(info_frame, text=f"Добро пожаловать, {username}!", foreground="#CDC3BD",
                               background="#232D3F",
                               font=("Britannic Bold", 15))
        username_label.pack(pady=2)  # Устанавливаем отступ между метками
    else:  # Если пользователь не авторизован
        welcome_label = Label(info_frame, text="Пожалуйста, войдите в свой аккаунт.", foreground="#CDC3BD",
                              background="#232D3F",
                              font=("Britannic Bold", 15))
        welcome_label.pack(pady=2)


def logout():
    global logged_in_user, is_admin
    logged_in_user = None
    is_admin = False
    update_profile_info("", "")  # Убираем информацию о профиле
    toggle_auth_buttons()  # Обновляем состояние кнопок

def toggle_auth_buttons():
    if logged_in_user:
        logout_button.pack(pady=10, fill=X)
        reg_button.pack_forget()
        login_button.pack_forget()
    else:
        logout_button.pack_forget()
        reg_button.pack(pady=10, fill=X)
        login_button.pack(pady=10, fill=X)

def login(username, password):
    global logged_in_user, is_admin
    if username == 'admin' and password == '123':
        is_admin = True
        messagebox.showinfo("Успех", "Добро пожаловать, администратор!")
        open_user_window()  # Открываем окно пользователей для администратора
    else:
        logged_in_user = find_user(username, password)
        if logged_in_user:
            messagebox.showinfo("Успех", f"Добро пожаловать, {logged_in_user[0]}!")
            update_profile_info(logged_in_user[0], logged_in_user[1])
            toggle_auth_buttons()  # Обновляем состояние кнопок
        else:
            messagebox.showerror("Ошибка", "Неверные логин или пароль.")

# Кнопка "Регистрация"
reg_button = Button(profile_frame, text="Регистрация", background="#E5E0D6", font=("Britannic Bold", 12), width=24, height=1, command=open_registration_window)

# Кнопка "Войти"
login_button = Button(profile_frame, text="Войти", background="#E5E0D6", font=("Britannic Bold", 12), width=24, height=1, command=open_login_window)

# Кнопка "Выйти"
logout_button = Button(profile_frame, text="Выйти", background="#E5E0D6", font=("Britannic Bold", 12), width=24, height=1, command=logout)
logout_button.pack_forget()  # Скрыть кнопку выхода на старте

# Обновляем состояние кнопок при запуске приложения
toggle_auth_buttons()

# Сначала показываем кнопки регистрации и входа
reg_button.pack(pady=10, fill=X)
login_button.pack(pady=10, fill=X)

# Кнопка "Абонементы"
Button(profile_frame, text="Абонементы", background="#E5E0D6", font=("Britannic Bold", 12), width=48, height=1, command=open_purchase_window).pack(pady=10, fill=X)

# Кнопка "Показать записи"
Button(profile_frame, text="Показать записи", background="#E5E0D6", font=("Britannic Bold", 12), width=48, height=1, command=show_records).pack(pady=10, fill=X)

# Кнопка "Очистить записи"
Button(profile_frame, text="Очистить записи", background="#E5E0D6", font=("Britannic Bold", 12), width=48, height=1, command=clear_records).pack(pady=10, fill=X)
profile_frame.configure(bg="#232D3F")


#Запись на тренировки
Label(schedule_frame, text="Запись на занятия",foreground="#CDC3BD",background="#232D3F", font=("Britannic Bold", 20)).grid(row=0, column=0, padx=5, pady=5, sticky=N)# Установка интерфейса

Label(schedule_frame, text="Силовая тренировка (11:30)", foreground="#CDC3BD", background="#232D3F", font=("Britannic Bold", 15)).grid(row=1, column=0, padx=5, pady=5, sticky=NW)
trening_date_entry1 = DateEntry(schedule_frame, width=20, background="#CDC3BD", foreground="#232D3F", borderwidth=2, date_pattern='dd-mm-yyyy')
trening_date_entry1.grid(row=2, column=0, padx=5, pady=5, sticky=NW)
reg5_button = Button(schedule_frame, text="Записаться",background="#E5E0D6",font=("Britannic Bold", 12), width=20,
                     command=lambda: add_registration(logged_in_user[0]if logged_in_user is not None else None, "Силовая тренировка (11:30)", trening_date_entry1.get()))
reg5_button.grid(row=3, column=0, padx=5, pady=5, sticky=NW)


Label(schedule_frame, text="Кардио (15:00)",foreground="#CDC3BD",background="#232D3F", font=("Britannic Bold", 15)).grid(row=1, column=1, padx=5, pady=5,sticky=NW)
trening_date_entry2 = DateEntry(schedule_frame, width=20, background="#CDC3BD", foreground="#232D3F", borderwidth=2,date_pattern='dd-mm-yyyy')
trening_date_entry2.grid(row=2, column=1, padx=5, pady=5, sticky=NW)
reg6_button = Button(schedule_frame, text="Записаться",background="#E5E0D6",font=("Britannic Bold", 12), width=20,
                     command=lambda: add_registration(logged_in_user[0]if logged_in_user is not None else None, "Кардио (15:00)", trening_date_entry2.get()))
reg6_button.grid(row=3, column=1, padx=5, pady=5, sticky=NW)

Label(schedule_frame, text="Йога (18:30)",foreground="#CDC3BD",background="#232D3F", font=("Britannic Bold", 15)).grid(row=4, column=0, padx=5, pady=5,sticky=NW)
trening_date_entry3 = DateEntry(schedule_frame, width=20, background="#CDC3BD", foreground="#232D3F", borderwidth=2,date_pattern='dd-mm-yyyy')
trening_date_entry3.grid(row=5, column=0, padx=5, pady=5, sticky=NW)
reg7_button = Button(schedule_frame, text="Записаться",background="#E5E0D6",font=("Britannic Bold", 12), width=20,
                     command=lambda: add_registration(logged_in_user[0]if logged_in_user is not None else None, "Йога (18:30)", trening_date_entry3.get()))
reg7_button.grid(row=6, column=0, padx=5, pady=5, sticky=NW)

Label(schedule_frame, text="Спорт танцы (20:30)",foreground="#CDC3BD",background="#232D3F", font=("Britannic Bold", 15)).grid(row=4, column=1, padx=5, pady=5,sticky=NW)
trening_date_entry4 = DateEntry(schedule_frame, width=20, background="#CDC3BD", foreground="#232D3F", borderwidth=2,date_pattern='dd-mm-yyyy')
trening_date_entry4.grid(row=5, column=1, padx=5, pady=5, sticky=NW)
reg8_button = Button(schedule_frame, text="Записаться", background="#E5E0D6", font=("Britannic Bold", 12), width=20,
                     command=lambda: add_registration(logged_in_user[0] if logged_in_user is not None else None, "Спорт танцы (20:30)", trening_date_entry4.get()))
reg8_button.grid(row=6, column=1, padx=5, pady=5, sticky=NW)

schedule_frame.configure(bg="#232D3F")

# Запуск основного цикла приложения
root.mainloop()

conn.close()