# вспомогательные функции безопасного пользовательского ввода

from datetime import date, datetime


# запрос целого числа в заданном диапазоне
def input_int(
    prompt: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    while True:
        try:
            value = int(input(prompt))
            if minimum is not None and value < minimum:
                raise ValueError
            if maximum is not None and value > maximum:
                raise ValueError
            return value
        except ValueError:
            if minimum is not None and maximum is not None:
                print(f"Введите число от {minimum} до {maximum}.")
            elif minimum is not None:
                print(f"Введите целое число не меньше {minimum}.")
            else:
                print("Введите корректное целое число.")


# запрос даты в формате ДД.ММ.ГГГГ
def input_date(prompt: str) -> date:
    while True:
        try:
            return datetime.strptime(input(prompt), "%d.%m.%Y").date()
        except ValueError:
            print("Введите корректную дату в формате ДД.ММ.ГГГГ.")
