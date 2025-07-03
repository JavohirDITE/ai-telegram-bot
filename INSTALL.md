# 🚀 Подробная инструкция по установке

## 📋 Пошаговая установка на Ubuntu 22.04

### Шаг 1: Подготовка сервера

\`\`\`bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y curl wget git htop nano vim python3 python3-pip python3-venv build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release unzip jq tree
\`\`\`

### Шаг 2: Установка Ollama

\`\`\`bash
# Скачивание и установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Настройка автозапуска
sudo systemctl enable ollama
sudo systemctl start ollama

# Проверка статуса
systemctl status ollama

# Загрузка модели LLaMA 3 (займет 10-15 минут)
ollama pull llama3

# Проверка установленных моделей
ollama list
\`\`\`

### Шаг 3: Клонирование проекта

\`\`\`bash
# Клонирование репозитория
git clone https://github.com/ВАШ_USERNAME/ai-telegram-bot.git
cd ai-telegram-bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
\`\`\`

### Шаг 4: Настройка Telegram бота

1. **Создание бота:**
   - Найдите [@BotFather](https://t.me/BotFather) в Telegram
   - Отправьте `/newbot`
   - Введите имя бота (например: "My AI Bot")
   - Введите username бота (например: "my_ai_bot")
   - Скопируйте токен

2. **Получение вашего ID:**
   - Найдите [@userinfobot](https://t.me/userinfobot)
   - Отправьте `/start`
   - Скопируйте ваш ID

3. **Настройка bot.py:**
   \`\`\`bash
   nano bot.py
   \`\`\`
   
   Найдите и измените:
   ```python
   BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
   ADMIN_ID = ВАШ_ID_ЗДЕСЬ
   \`\`\`

### Шаг 5: Создание systemd сервиса

\`\`\`bash
# Замените USERNAME на ваше имя пользователя
sudo sed -i "s/cs2serverss/$USER/g" ai-telegram-bot.service

# Копирование сервиса
sudo cp ai-telegram-bot.service /etc/systemd/system/

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable ai-telegram-bot
\`\`\`

### Шаг 6: Установка команды управления

\`\`\`bash
# Копирование скрипта управления
sudo cp tgai /usr/local/bin/
sudo chmod +x /usr/local/bin/tgai
\`\`\`

### Шаг 7: Первый запуск

\`\`\`bash
# Запуск бота
tgai start

# Проверка статуса
tgai status

# Просмотр логов
tgai logs
\`\`\`

## 🔧 Проверка установки

### 1. Проверка Ollama
\`\`\`bash
# Статус сервиса
systemctl status ollama

# Список моделей
ollama list

# Тест модели
ollama run llama3 "Привет, как дела?"
\`\`\`

### 2. Проверка бота
\`\`\`bash
# Статус бота
tgai status

# Логи в реальном времени
tgai logs
\`\`\`

### 3. Тест в Telegram
- Найдите вашего бота по username
- Отправьте `/start`
- Задайте любой вопрос

## 🐛 Решение проблем

### Ollama не запускается
\`\`\`bash
# Проверка логов
journalctl -u ollama -f

# Перезапуск
sudo systemctl restart ollama
\`\`\`

### Бот не отвечает
\`\`\`bash
# Проверка токена в bot.py
nano bot.py

# Перезапуск бота
tgai restart
\`\`\`

### Ошибки Python
\`\`\`bash
# Переустановка зависимостей
source venv/bin/activate
pip install --upgrade -r requirements.txt
\`\`\`

## 📊 Мониторинг

### Использование ресурсов
\`\`\`bash
# Общая информация
htop

# Использование диска
df -h

# Память
free -h
\`\`\`

### Логи
\`\`\`bash
# Логи бота
tgai logs

# Системные логи
journalctl -u ai-telegram-bot -f
\`\`\`

## 🔄 Обновление

\`\`\`bash
# Остановка бота
tgai stop

# Получение обновлений
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Запуск
tgai start
\`\`\`

---

**🎉 Поздравляем! Ваш AI Telegram бот готов к работе!**
