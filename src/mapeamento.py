import requests
import json
import time
from datetime import datetime, timedelta


def enviar_post(url, data):
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[{datetime.now()}] Erro HTTP: {response.status_code}")
            return None
    except Exception as e:
        print(f"[{datetime.now()}] Erro na requisição: {e}")
        return None


def salvar_em_arquivo(dados, nome_arquivo):
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
        print(f"[{datetime.now()}] Dados salvos no arquivo: {nome_arquivo}")


def monitorar_estoque(token, parar_callback=None, intervalo=20, log_func=None, chamar_obter_produtos=None):
    """
    Monitora o estoque periodicamente.
    Sempre que houver atualização, salva arquivo e chama 'chamar_obter_produtos' para atualizar os detalhes.

    - parar_callback(): função que retorna True para parar o monitoramento.
    - log_func(msg): função para logar mensagens.
    - chamar_obter_produtos(): função para chamar obter_produtos.
    """

    url = 'https://api.tiny.com.br/api2/lista.atualizacoes.estoque.php'
    caminho_arquivo = "estoque_atualizado.json"

    while True:
        if parar_callback and parar_callback():
            msg = "Monitoramento parado pelo callback."
            if log_func:
                log_func(msg)
            else:
                print(f"[{datetime.now()}] {msg}")
            break

        data_alteracao = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y %H:%M:%S')
        payload = {
            'token': token,
            'formato': 'json',
            'dataAlteracao': data_alteracao
        }

        dados = enviar_post(url, data=payload)

        if dados:
            retorno = dados.get('retorno', {})
            if retorno.get('status') == 'OK' and 'produtos' in retorno and len(retorno['produtos']) > 0:
                salvar_em_arquivo(dados, caminho_arquivo)
                if log_func:
                    log_func(f"Produtos atualizados e arquivo salvo: {caminho_arquivo}")
                else:
                    print(f"[{datetime.now()}] Produtos atualizados e arquivo salvo: {caminho_arquivo}")
                if chamar_obter_produtos:
                    chamar_obter_produtos()  # chama para atualizar os detalhes
            else:
                msg = "Nenhum produto atualizado ou erro na resposta."
                chamar_obter_produtos()
                if log_func:
                    log_func(msg)
                else:
                    print(f"[{datetime.now()}] {msg}")
        else:
            msg = "Nenhuma resposta da API."
            if log_func:
                log_func(msg)
            else:
                print(f"[{datetime.now()}] {msg}")

        # Espera intervalo segundos, verificando parar_callback a cada 1 segundo para responsividade
        for _ in range(intervalo):
            if parar_callback and parar_callback():
                msg = "Monitoramento parado pelo callback."
                if log_func:
                    log_func(msg)
                else:
                    print(f"[{datetime.now()}] {msg}")
                return
            time.sleep(1)