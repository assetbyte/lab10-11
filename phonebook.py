import psycopg2
import csv

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="phonebook",  
            user="postgres",
            password="8554",  
            host="localhost",
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        print("Ошибка при подключении к базе данных:", e)
        return None

def create_table():
    conn = connect_db()
    if conn is not None:
        cursor = conn.cursor()

        
        cursor.execute("DROP FUNCTION IF EXISTS search_pattern(text);")
        
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phonebook (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone_number VARCHAR(15)
            );
        """)

        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION search_pattern(pattern text)
            RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, phone_number VARCHAR) AS $$
            BEGIN
                RETURN QUERY 
                SELECT p.id, p.first_name, p.last_name, p.phone_number  
                FROM phonebook p 
                WHERE p.first_name LIKE '%' || pattern || '%'
                   OR p.last_name LIKE '%' || pattern || '%'
                   OR p.phone_number LIKE '%' || pattern || '%';
            END;
            $$ LANGUAGE plpgsql;
        """)

       
        cursor.execute("""
            CREATE OR REPLACE PROCEDURE insert_or_update_user(
                first_name VARCHAR, 
                last_name VARCHAR, 
                phone_number VARCHAR)
            LANGUAGE plpgsql
            AS $$
            BEGIN
               
                UPDATE phonebook
                SET phone_number = phone_number 
                WHERE first_name = first_name AND last_name = last_name;
                
            
                IF NOT FOUND THEN
                    INSERT INTO phonebook (first_name, last_name, phone_number)
                    VALUES (first_name, last_name, phone_number);
                END IF;
            END;
            $$;
        """)

        
        cursor.execute("""
            CREATE OR REPLACE PROCEDURE insert_multiple_users(users_list jsonb)
            LANGUAGE plpgsql
            AS $$
            DECLARE
                user RECORD;
            BEGIN
                
                FOR user IN
                    SELECT * FROM jsonb_array_elements(users_list)
                LOOP
                    
                    IF LENGTH(user->>'phone_number') = 10 THEN
                        
                        INSERT INTO phonebook (first_name, last_name, phone_number)
                        VALUES (user->>'first_name', user->>'last_name', user->>'phone_number');
                    ELSE
                        RAISE NOTICE 'Некорректный номер телефона: %', user->>'phone_number';
                    END IF;
                END LOOP;
            END;
            $$;
        """)

        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION query_with_pagination(limit_val INT, offset_val INT)
            RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, phone_number VARCHAR) AS $$
            BEGIN
                RETURN QUERY 
                SELECT p.id, p.first_name, p.last_name, p.phone_number  
                FROM phonebook p 
                LIMIT limit_val OFFSET offset_val;
            END;
            $$ LANGUAGE plpgsql;
        """)


        cursor.execute("""
            CREATE OR REPLACE PROCEDURE delete_user_by_value(value VARCHAR)
            LANGUAGE plpgsql
            AS $$
            BEGIN
                DELETE FROM phonebook WHERE first_name = value OR last_name = value OR phone_number = value;
            END;
            $$;
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Таблица и процедуры успешно созданы!")
    else:
        print("Не удалось подключиться к базе данных.")

def call_search_pattern():
    conn = connect_db()
    if conn:
        pattern = input("Введите шаблон для поиска: ")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM search_pattern(%s);", (pattern,))
        results = cursor.fetchall()
        for row in results:
            print(row)
        cursor.close()
        conn.close()

def call_insert_or_update():
    conn = connect_db()
    if conn:
        fname = input("Имя: ")
        lname = input("Фамилия: ")
        phone = input("Телефон: ")
        cursor = conn.cursor()
        cursor.execute("CALL insert_or_update_user(%s, %s, %s);", (fname, lname, phone))
        conn.commit()
        cursor.close()
        conn.close()
        print("Данные добавлены или обновлены.")
        
def call_insert_from_csv():
    conn = connect_db()
    if conn:
        path = input("Введите путь к CSV-файлу: ")
        cursor = conn.cursor()

        try:
            with open(path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) == 3:
                        fname, lname, phone = row
                        cursor.execute("CALL insert_or_update_user(%s, %s, %s);", (fname, lname, phone))
            conn.commit()
            print("Данные из CSV успешно добавлены.")
        except Exception as e:
            print("Ошибка при чтении CSV-файла:", e)
        
        cursor.close()
        conn.close()

def call_paginated_data():
    conn = connect_db()
    if conn:
        limit = int(input("Введите лимит: "))
        offset = int(input("Введите смещение (offset): "))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM query_with_pagination(%s, %s);", (limit, offset))  # Исправлено имя функции
        results = cursor.fetchall()
        for row in results:
            print(row)
        cursor.close()
        conn.close()

def call_delete_by_value():
    conn = connect_db()
    if conn:
        value = input("Введите имя, фамилию или номер телефона для удаления: ")
        cursor = conn.cursor()
        cursor.execute("CALL delete_user_by_value(%s);", (value,))  # Исправлено имя процедуры
        conn.commit()
        cursor.close()
        conn.close()
        print("Удаление завершено.")

def main():
    while True:
        print("1. Создать таблицу и процедуры")
        print("2. Поиск по шаблону")
        print("3. Вставить/обновить одного пользователя")
        print("4. Пагинация")
        print("5. Удалить по значению")
        print("6. Загрузить из CSV") 
        print("7. Выйти")

        choice = input("Введите номер действия: ")

        if choice == "1":
            create_table()
        elif choice == "2":
            call_search_pattern()
        elif choice == "3":
            call_insert_or_update()
        elif choice == "4":
            call_paginated_data()
        elif choice == "5":
            call_delete_by_value()
        elif choice == "6":
            call_insert_from_csv()
        elif choice == "7":
            break
            print("Неверный выбор, попробуйте снова.")

if __name__ == "__main__":
    main()
