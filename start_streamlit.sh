#!/bin/bash

# Script para iniciar o Streamlit automaticamente com restart automático
# Salve este arquivo e execute: chmod +x start_streamlit.sh

APP_NAME="Google Ads Creative Automation"
LOG_FILE="streamlit.log"
PID_FILE="streamlit.pid"
MAX_RESTARTS=10
RESTART_DELAY=5

echo "🚀 Iniciando $APP_NAME..."

# Função para parar processo existente
stop_existing() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 Parando processo existente (PID: $PID)..."
            kill $PID
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
}

# Função para iniciar Streamlit
start_streamlit() {
    echo "🔄 Tentativa $1 de iniciar Streamlit..."
    
    # Ativar ambiente virtual
    source venv/bin/activate
    
    # Configurar variáveis de ambiente
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Verificar se a porta está livre
    PORT=8501
    while lsof -i :$PORT > /dev/null 2>&1; do
        echo "⚠️ Porta $PORT em uso, tentando próxima..."
        PORT=$((PORT + 1))
        if [ $PORT -gt 8510 ]; then
            echo "❌ Nenhuma porta disponível entre 8501-8510"
            return 1
        fi
    done
    
    echo "✅ Usando porta $PORT"
    
    # Iniciar Streamlit em background
    nohup streamlit run streamlit_app_final_limpo.py \
        --server.port $PORT \
        --server.address 0.0.0.0 \
        --server.headless true \
        --browser.gatherUsageStats false \
        --server.runOnSave false \
        > "$LOG_FILE" 2>&1 &
    
    # Salvar PID
    echo $! > "$PID_FILE"
    
    # Aguardar um pouco para ver se iniciou
    sleep 3
    
    # Verificar se está rodando
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ Streamlit iniciado com sucesso! PID: $(cat $PID_FILE)"
        return 0
    else
        echo "❌ Falha ao iniciar Streamlit"
        return 1
    fi
}

# Parar processo existente
stop_existing

# Loop de restart automático
restart_count=0
while [ $restart_count -lt $MAX_RESTARTS ]; do
    restart_count=$((restart_count + 1))
    
    if start_streamlit $restart_count; then
        echo "🎉 $APP_NAME está rodando!"
        echo "📊 Acesse: http://localhost:$PORT"
        echo "📝 Logs: tail -f $LOG_FILE"
        echo "🛑 Para parar: ./stop_streamlit.sh"
        
        # Monitorar o processo
        while ps -p $(cat "$PID_FILE") > /dev/null 2>&1; do
            sleep 10
        done
        
        echo "⚠️ Processo parou inesperadamente. Reiniciando em $RESTART_DELAY segundos..."
        sleep $RESTART_DELAY
    else
        echo "❌ Falha na tentativa $restart_count. Tentando novamente em $RESTART_DELAY segundos..."
        sleep $RESTART_DELAY
    fi
done

echo "💥 Máximo de tentativas atingido. Verifique os logs em $LOG_FILE" 