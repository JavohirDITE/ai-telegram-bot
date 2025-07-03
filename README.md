# 🤖 AI Telegram Bot v3.0

**Мощный Telegram бот с искусственным интеллектом на базе Ollama LLaMA 3**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-LLaMA%203-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04+-orange.svg)](https://ubuntu.com)

## 🚀 Особенности

- 🧠 **Искусственный интеллект** на базе LLaMA 3
- 🎭 **Система ролей** - Программист, Учитель, Токсик, Актер и другие
- 📊 **База данных SQLite** с полной статистикой
- 👑 **Админ-панель** с мониторингом
- ⚡ **Оптимизированные ответы** - быстро и качественно
- 🔄 **Автоматическое разбиение** длинных сообщений
- 🛡️ **Systemd сервис** для автозапуска
- 📝 **Подробное логирование**
- 🔧 **Удобное управление** через команду `tgai`

## 📋 Минимальные требования

### Система
- **ОС:** Ubuntu 22.04+ (рекомендуется)
- **RAM:** 8GB+ (рекомендуется 12GB+)
- **CPU:** 4+ ядра (рекомендуется 8+)
- **Диск:** 20GB+ свободного места
- **Интернет:** Стабильное подключение

### Программное обеспечение
- Python 3.10+
- Git
- Curl/Wget
- Systemd (для автозапуска)

## 🛠️ Быстрая установка

### 1. Подготовка системы

\`\`\`bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых пакетов
sudo apt install -y curl wget git python3 python3-pip python3-venv build-essential
\`\`\`

### 2. Установка Ollama

\`\`\`bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск сервиса
sudo systemctl enable ollama
sudo systemctl start ollama

# Загрузка модели LLaMA 3 (это займет время!)
ollama pull llama3
\`\`\`

### 3. Клонирование и настройка бота

\`\`\`bash
# Клонирование репозитория
git clone https://github.com/ВАШ_USERNAME/ai-telegram-bot.git
cd ai-telegram-bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
\`\`\`

### 4. Настройка бота

Отредактируйте файл `bot.py` и укажите ваши данные:

```python
# ВАШИ НАСТРОЙКИ
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"
ADMIN_ID = ВАШ_TELEGRAM_ID
