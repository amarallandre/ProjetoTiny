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


def monitorar_estoque(token, parar_callback=None, log_func=None, chamar_obter_produtos=None):
    url = 'https://api.tiny.com.br/api2/lista.atualizacoes.estoque.php'
    caminho_arquivo = "estoque_atualizado.json"

    def _log(msg):
        if log_func:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_func(f"[{timestamp}] {msg}")
        else:
            print(msg)

    if parar_callback and parar_callback():
        _log("⏹ Monitoramento interrompido antes de iniciar a verificação.")
        return

    _log("🔄 Verificando atualizações de estoque...")

    data_alteracao = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y %H:%M:%S')
    payload = {
        'token': token,
        'formato': 'json',
        'dataAlteracao': data_alteracao
    }

    try:
        dados = enviar_post(url, data=payload)
    except Exception as e:
        _log(f"❌ Erro ao consultar API de estoque: {e}")
        return

    if dados:
        retorno = dados.get('retorno', {})
        produtos = retorno.get('produtos', [])

        if retorno.get('status') == 'OK' and produtos:
            salvar_em_arquivo(dados, caminho_arquivo)
            _log(f"📥 Produtos atualizados e salvos em '{caminho_arquivo}'.")
        else:
            _log("⚠️ Nenhum produto atualizado ou resposta da API vazia.")

        if chamar_obter_produtos:
            _log("📦 Atualizando produtos detalhados...")
            try:
                chamar_obter_produtos()
            except Exception as e:
                _log(f"❌ Erro ao chamar obter_produtos: {e}")
    else:
        _log("❌ Nenhuma resposta da API.")
