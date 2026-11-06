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

## Teste histórico

Execute `python backtest.py --dias 90` para baixar candles públicos e calcular o resultado. O período inclui 150 candles de aquecimento; o capital inicial é 1.000 USDT e cada compra usa até 100 USDT. A simulação executa na abertura do candle seguinte ao sinal, cobra 0,1% por ordem e estima o valor da posição aberta incluindo taxa de venda. Não considera slippage, latência, falhas, impostos ou alterações de taxa. Resultados passados não garantem resultados futuros. O simulador ao vivo usa o fechamento como referência, portanto os resultados não são idênticos.

## Configurar e testar o Telegram

1. Crie um bot usando @BotFather e envie /start ao bot criado.
2. No PowerShell, defina `$env:TELEGRAM_TOKEN = 'TOKEN_DO_BOT'` e execute `python telegram_config.py` para listar os IDs das conversas recentes. Não envie seu token a outras pessoas nem o inclua no repositório. O comando depende de getUpdates e não funciona se um webhook estiver ativo.
3. Defina `$env:TELEGRAM_CHAT_ID = 'ID_DA_CONVERSA'` e execute novamente `python telegram_config.py`. O bot enviará uma mensagem de teste.
4. Na mesma janela, execute `python robo_sol.py`. As variáveis de ambiente duram apenas enquanto a janela estiver aberta.

## Relatório Spot → P2P

Instale a biblioteca Pillow com `python -m pip install Pillow`. Com o Telegram configurado, rode `python arbitragem.py --valor 500 --telegram`. O comando envia uma mensagem a cada 3 minutos (use `--intervalo 0` para enviar uma única vez) com preços e uma imagem com gráfico de barras e o relatório formatado na legenda; sem `--telegram`, mostra apenas no terminal. O valor é aplicado separadamente em cada moeda fiduciária. O relatório compara o melhor preço Spot para adquirir USDT e anúncios P2P de compra de USDT que aceitam o valor informado; consulta até 20 anúncios. A resposta P2P usa um endpoint público não documentado oficialmente, sujeito a mudanças, bloqueios e ofertas diferentes conforme região. USD é indicado como indisponível até haver um par Spot adequado. A diferença é bruta, não garante operação nem considera taxas, pagamento, slippage, volume completo, risco da contraparte ou impostos. Confira os detalhes na Binance. Não envia ordens. Mantenha a janela aberta e use Ctrl+C para parar. Para mudar o intervalo, use `--intervalo` em segundos (mínimo 60).


## Simulador multimoeda (experimental)

`crypto_paper_bot.py` usa somente dados públicos: não possui chave de corretora e não envia ordens reais. Na primeira execução converte R$ 100 em USDT ao melhor preço de venda público USDT/BRL. Para fixar um saldo virtual, use `--capital-usdt 20`. O valor inicial fica salvo no banco e não é recalculado ao reiniciar.

Seleciona até 20 pares Spot USDT negociáveis por volume de 24 horas, atualizados aproximadamente a cada hora. Para cada candle fechado de 5 minutos, a estratégia ilustrativa compra no cruzamento de alta da EMA 9/21, quando RSI está entre 50 e 70, MACD está acima de sua linha de sinal e o volume supera a média dos 20 candles anteriores. Vende no cruzamento de baixa. As operações usam o melhor preço ask/bid consultado e taxa estimada de 0,1% por ponta. O sinal no primeiro ciclo e candles perdidos não geram ordens retroativas.

Risco: até duas posições, cada nova compra usa no máximo 50% do patrimônio; saída simulada quando o preço observado atinge -1,5% ou +3% da entrada. Ao detectar queda de 3% do patrimônio em relação ao valor no primeiro ciclo do dia UTC, bloqueia novas compras até o próximo dia UTC; posições continuam abertas e sujeitas a saídas. Isso não garante limite máximo de perdas. O stop depende do programa em execução e das consultas: pode ocorrer muito depois do nível, especialmente em caso de lentidão, falhas, gaps ou programa desligado. Faltam slippage, profundidade, regras de lote, e efeitos de liquidez. Se não conseguir avaliar uma posição, novas entradas são suspensas naquele ciclo. Não execute duas instâncias com o mesmo banco.

No PowerShell, com o Telegram configurado na mesma janela, execute:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\crypto_paper_bot.py
```

Mantenha a janela aberta e use Ctrl+C para parar. Se preferir, defina `--capital-usdt 20` na primeira execução. O banco `paper_trading.sqlite3` armazena posições e operações localmente e é ignorado pelo Git. Para ver saldo, posições e resultados acumulados, em outra janela execute:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\crypto_paper_bot.py --status
```

As mensagens de compra e venda serão enviadas ao Telegram se as variáveis estiverem configuradas; falhas de envio não são reenviadas. O resumo no terminal é básico; não há painel gráfico, backtest multimoeda, nem integração Testnet. Testes automatizados: `python -m unittest test_indicators test_paper_bot -v`. Simulação e resultados passados não comprovam que a estratégia seja lucrativa.
