"""Mostra chats que iniciaram conversa com o bot, sem exibir o token."""
import os, sys
from robo_sol import request, notify

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        sys.exit('Defina TELEGRAM_TOKEN na sessão do PowerShell.')
    try:
        result = request('https://api.telegram.org/bot' + token + '/getUpdates')
        chats = {}
        for update in result.get('result', []):
            msg = update.get('message') or update.get('channel_post') or {}
            chat = msg.get('chat', {})
            if 'id' in chat: chats[chat['id']] = chat.get('title') or chat.get('first_name', 'chat')
        if not chats:
            print('Nenhuma conversa encontrada. Envie /start ao bot e tente novamente. Se houver webhook configurado, getUpdates não funciona.')
        for chat_id, name in chats.items(): print(f'{name}: {chat_id}')
        if os.getenv('TELEGRAM_CHAT_ID'): notify('Teste do robô SOL/USDT: Telegram conectado. Nenhuma ordem foi enviada.')
    except Exception:
        sys.exit('Falha ao consultar Telegram. Confira o token e a conexão.')

if __name__ == '__main__': main()
