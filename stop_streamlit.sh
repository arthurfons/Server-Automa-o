#!/bin/bash

# Script para parar o Streamlit
# Salve este arquivo e execute: chmod +x stop_streamlit.sh

PID_FILE="streamlit.pid"
LOG_FILE="streamlit.log"

echo "🛑 Parando Google Ads Creative Automation..."

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "📋 Parando processo (PID: $PID)..."
        kill $PID
        sleep 2
        
        # Verificar se parou
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️ Processo não parou, forçando..."
            kill -9 $PID
        fi
        
        echo "✅ Processo parado com sucesso!"
    else
        echo "ℹ️ Processo já não estava rodando"
    fi
    rm -f "$PID_FILE"
else
    echo "ℹ️ Arquivo PID não encontrado"
fi

# Parar todos os processos streamlit (backup)
echo "🧹 Limpando processos streamlit restantes..."
pkill -f "streamlit run" 2>/dev/null || true

echo "🎉 Streamlit parado completamente!" 