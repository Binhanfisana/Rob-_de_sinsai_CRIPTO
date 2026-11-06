# Robô SOL/USDT — simulação

Esta primeira versão observa candles fechados de 15 minutos e simula compra quando a EMA 9 cruza acima da EMA 21 e venda no cruzamento inverso. Estima taxa de 0,1% em cada ponta, sem slippage. A estratégia é apenas um exemplo, sem garantia de lucro. Não há stop, backtest, execução real nem recuperação de sinais perdidos durante períodos desligado. O saldo e a posição simulados são salvos em estado.json ao lado do programa. Ao iniciar pela primeira vez, aguarda um novo candle antes de operar.

## Executar no Windows

Instale Python 3 e abra o PowerShell na pasta deste arquivo. Crie um bot pelo @BotFather no Telegram, mande /start para ele e obtenha seu chat ID pela API getUpdates. Não compartilhe o token. Em sua sessão do PowerShell, configure:

```powershell
$env:TELEGRAM_TOKEN = 'SEU_TOKEN'
$env:TELEGRAM_CHAT_ID = 'SEU_CHAT_ID'
$env:SALDO_INICIAL_USDT = '1000'
$env:VALOR_POR_OPERACAO_USDT = '100'
python .\robo_sol.py
```

Sem credenciais do Telegram, as mensagens aparecem no terminal. Mantenha o programa aberto. Os valores de saldo inicial só se aplicam quando não existe estado.json. Para reiniciar a simulação, pare o programa e renomeie ou remova esse arquivo. Uma falha do Telegram é mostrada no terminal e não é reenviada automaticamente. Antes de operar com dinheiro real, serão necessários testes, limites de risco, tratamento de ordens e conferência da conta.
