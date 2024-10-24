# Brushshe - програма для малювання

## Опис
**Брашше** - простий графічний редактор, написаний на Python 3 та CustomTkinter.

![Screenshot](https://raw.githubusercontent.com/limafresh/Brushshe/main/screenshot.png)

## Встановлення
1. Встановіть [Python 3](https://www.python.org/downloads/), якщо не встановлений;
2. Завантажте код та розпакуйте завантажений архів:

[![Download the code](https://img.shields.io/badge/Завантажити_код-ZIP-orange?style=for-the-badge&logo=Python&logoColor=white)](https://github.com/limafresh/Brushshe/archive/refs/heads/main.zip)  
3. Встановіть CustomTkinter, якщо не встановлений - відкрийте термінал чи командну строку та введіть:
```
pip install customtkinter
```
4. Запустіть Python IDLE, відкрийте файл `brushshe.py` та запустіть його.
### Можливі помилки
1. Якщо Python не зміг знайти бібліотеку `PIL`, встановіть `Pillow`, яка сумісна з `PIL`:
```
pip install Pillow
```

## Функціонал
### Малювання
Можна обирати колір, змінювати товщину пензля і малювати.
### Ластик
Видалення зайвого ластиком.
### Тло
Можна обирати колір тла.
### Наліпки
Можна ставити наліпки і змінювати їх розмір. Всі зображення наліпок намальовані мною або створені штучним інтелектом.
### Текст
Можна ставити текст і змінювати його розмір.
### Рамки
Можна прикрасити малюнок рамками.
### Фігури
Прямокутник, овал (з заповненням та без), лінія.
### Моя галерея
Місце, де зберігаються малюнки, намальовані в Brushshe, а також вікно, де можна їх переглянути. Якщо треба перенести малюнки на новий пристрій, скопіюйте вміст папки "gallery".
### Темна тема
Є світла і темна тема.
### Файл
Можна відкрити малюнок з файлу і зберегти не в галерею.

## Версії залежностей, використовувані під час розробки
+ Python 3.11.2
+ customtkinter 5.2.2

## Подяки
Дякую [Akascape](https://github.com/Akascape) за бібліотеки [CTkColorPicker](https://github.com/Akascape/CTkColorPicker), [CTkMenuBar](https://github.com/Akascape/CTkMenuBar) та [CTkMessagebox](https://github.com/Akascape/CTkMessagebox).

## Ліцензія
Ліцензія проекту - *GNU GPL v3*, ліцензія CTkColorPicker, CTkMenuBar та CTkMessagebox - *CC0*.

## Для розробників
### Лінтер
Для підтримки чистоти коду використовується [Ruff](https://github.com/astral-sh/ruff).

## 🎨🦅💪
