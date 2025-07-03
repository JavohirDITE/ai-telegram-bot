#!/bin/bash

# Проверка системы перед установкой
echo "🔍 Проверка системы Ubuntu..."

# Проверяем Ubuntu
if grep -q "Ubuntu" /etc/os-release; then
    echo "✅ Ubuntu обнаружена"
    lsb_release -a
else
    echo "❌ Это не Ubuntu!"
    exit 1
fi

# Проверяем ресурсы
echo ""
echo "💻 Ресурсы системы:"
echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Диск: $(df -h / | awk 'NR==2 {print $4 " свободно"}')"
echo "CPU: $(nproc) ядер"

# Проверяем интернет
echo ""
echo "🌐 Проверка интернета:"
if ping -c 1 google.com &> /dev/null; then
    echo "✅ Интернет работает"
else
    echo "❌ Нет интернета!"
    exit 1
fi

echo ""
echo "🚀 Система готова к установке!"
