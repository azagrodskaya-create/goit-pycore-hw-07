from collections import UserDict
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


# --- КЛАСИ ТИПІВ ДАНИХ  ---


class Field:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field): # Ім'я — обов'язкове поле. Логіка успадковується від Field
    pass


class Phone(Field):
    def __init__(self, value: str) -> None: # Перевіряємо, чи номер містить рівно 10 цифр
        if not (len(value) == 10 and value.isdigit()):
            raise ValueError("Номер телефону має складатися з 10 цифр.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str) -> None:
        try: # Перевіряємо, чи дата відповідає формату "DD.MM.YYYY" і конвертуємо її в об'єкт datetime.date
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        
    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y") # Повертаємо дату у форматі "DD.MM.YYYY"    


class Record:
    def __init__(self, name: str) -> None:
        self.name: Name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone_number: str) -> None: # Створюємо об'єкт Phone і додаємо до списку
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number: str) -> None: # Шукаємо телефон за значенням і видаляємо об'єкт з списку
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_number: str, new_number: str) -> None: # Знаходимо старий номер, перевіряємо валідність нового і замінюємо
        phone_obj = self.find_phone(old_number)
        if not phone_obj:
            raise ValueError(f"Телефон {old_number} не знайдено.")
        
        new_phone = Phone(new_number) # Створення нового об'єкта Phone автоматично запустить валідацію 10 цифр
        index = self.phones.index(phone_obj) # Знаходимо індекс старого об'єкта і замінюємо його на новий
        self.phones[index] = new_phone

    def find_phone(self, phone_number: str) -> Optional[Phone]: # Пошук об'єкта Phone у списку за строковим значенням
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None
    
    def add_birthday(self, birthday_str: str) -> None: # Створюємо об'єкт Birthday і присвоюємо його атрибуту birthday
        self.birthday = Birthday(birthday_str)

    def __str__(self) -> str: # Формуємо строкове представлення контакту, включаючи ім'я, телефони та дату народження (якщо вона є)
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        phones_str = "; ".join(p.value for p in self.phones)
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"
        

class AddressBook(UserDict):
    def add_record(self, record: Record) -> None: # Додаємо запис до словника self.data (успадковано від UserDict)
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:  # Пошук запису за ключем (ім'ям)
        return self.data.get(name)

    def delete(self, name: str) -> None: # Видалення запису за ім'ям
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> List[dict]: # Повертає список словників з інформацією про контакти, у яких день народження наступає протягом наступних 7 днів
        upcoming_birthdays = []
        today = datetime.today().date()

        for record in self.data.values(): # Проходимо по всіх записах у адресній книзі
            if record.birthday:
                bday = record.birthday.value

                try:
                    birthday_this_year = bday.replace(year=today.year) # Створюємо дату для поточного року, використовуючи день і місяць з дати народження
                except ValueError:
                    birthday_this_year = bday.replace(year=today.year, month=3, day=1) # Якщо 29.02 не існує в цьому році, переносимо на 01.03 

                if birthday_this_year < today:
                    try:
                        birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                    except ValueError:
                        birthday_this_year = birthday_this_year.replace(year=today.year + 1, month=3, day=1)

                if 0 <= (birthday_this_year - today).days <= 7:
                    congrats_date = birthday_this_year # Якщо день народження наступає протягом наступних 7 днів, визначаємо дату для привітання (сам день народження або наступний робочий день, якщо він припадає на вихідні)
                    if congrats_date.weekday() == 5:  # Субота
                        congrats_date += timedelta(days=2)
                    elif congrats_date.weekday() == 6:  # Неділя
                        congrats_date += timedelta(days=1)

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": str(record.birthday),
                        "congrats_date": congrats_date.strftime("%d.%m.%Y")
                    })
        return upcoming_birthdays  


    # --- ФУНКЦІЇ-ОБРОБНИКИ ---


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter user name and and the required data (phone or birthday), please."
        except KeyError:
            return "Contact not found. Please check the name."
    return inner


def parse_input(user_input: str) -> Tuple[str, List[str]]:
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args


@input_error
def add_contact(args: List[str], book: AddressBook) -> str:
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: List[str], book: AddressBook) -> str:
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Phone updated."
    raise KeyError


@input_error
def show_phones(args: List[str], book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}: {', '.join(p.value for p in record.phones)}"
    raise KeyError


@input_error
def add_birthday(args: List[str], book: AddressBook) -> str:
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    raise KeyError


@input_error
def show_birthday(args: List[str], book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday}"
    elif record:
        return f"{name} doesn't have a birthday set."
    raise KeyError


@input_error
def birthdays(args, book: AddressBook) -> str:
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    
    result = "Upcoming birthdays:\n"
    for entry in upcoming:
        result += f"{entry['name']}: {entry['congrats_date']}\n"
    return result.strip()


# --- ГОЛОВНА ФУНКЦІЯ  ---


def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        if not user_input:
            continue
            
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phones(args, book))

        elif command == "all":
            for name, record in book.data.items():
                print(record)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()          
