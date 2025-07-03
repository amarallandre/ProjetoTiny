import json
from datetime import datetime
from time import sleep
from urllib.parse import urlencode
from pathlib import Path
import requests

def enviar_rest(url: str, data: dict | str, optional_headers: dict | None = None, timeout: int = 30) -> dict:
    if isinstance(data, dict):
        data = urlencode(data, doseq=True)

    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
    if optional_headers:
        headers.update(optional_headers)

    resp = requests.post(url, data=data, headers=headers, timeout=timeout)
    resp.raise_for_status()

    try:
        return resp.json()
    except ValueError as exc:
        raise RuntimeError("Resposta não é JSON válido") from exc

def salvar_em_arquivo(dados: list, nome_arquivo: str) -> None:
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def obter_produtos(token: str,
                   parar_callback=None,
                   log_func=None,
                   arquivo_estoque: str = "estoque_atualizado.json",
                   arquivo_saida: str = "precos_e_saldo.json"):
    """
    Lê 'estoque_atualizado.json', consulta detalhe de cada ID e
    salva saída em 'precos_e_saldo.json'.

    • parar_callback() → função que retorna True quando o usuário clicar em Parar
    • log_func(msg)   → função da interface para exibir logs
    """

    def _log(msg: str):
        if log_func:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_func(f"[{timestamp}] {msg}")
        else:
            print(msg)

    if not Path(arquivo_estoque).exists():
        _log(f"Arquivo '{arquivo_estoque}' não encontrado.")
        return

    try:
        with open(arquivo_estoque, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception as e:
        _log(f"Erro ao ler o arquivo '{arquivo_estoque}': {e}")
        return

    produtos_estoque = dados.get("retorno", {}).get("produtos", [])
    total = len(produtos_estoque)
    if not total:
        _log("Nenhum produto dentro do arquivo de estoque.")
        return

    _log(f"Iniciando obtenção de {total} produtos…")
    lista_precos_saldo = []

    URL = "https://api.tiny.com.br/api2/produto.obter.php"
    FORMATO = "JSON"

    for idx, item in enumerate(produtos_estoque, 1):
        if parar_callback and parar_callback():
            _log("❗ Execução interrompida pelo usuário.")
            break

        prod = item["produto"]
        prod_id = prod.get("id")
        prod_nome = prod.get("nome")
        saldo = prod.get("saldo", 0)

        payload = {
            "token": token,
            "id": prod_id,
            "nome": prod_nome,
            "formato": FORMATO
        }

        try:
            dados_api = enviar_rest(URL, payload)
        except Exception as err:
            _log(f"({idx}/{total}) ❌ Erro para ID {prod_id}: {err}")
            continue

        retorno = dados_api.get("retorno", {})
        if retorno.get("status") == "OK" and "produto" in retorno:
            produto_api = retorno["produto"]
            lista_precos_saldo.append({
                "id": produto_api.get("id"),
                "nome": produto_api.get("nome"),
                "codigo": produto_api.get("codigo"),
                "preco": float(produto_api.get("preco", 0)),
                "preco_promocional": float(produto_api.get("preco_promocional", 0)),
                "saldo": int(saldo)
            })
            _log(f"({idx}/{total}) ✔️ Produto {prod_id} processado.")
        else:
            _log(f"({idx}/{total}) ⚠️ Produto {prod_id} não encontrado.")

        sleep(1)

    if lista_precos_saldo:
        salvar_em_arquivo(lista_precos_saldo, arquivo_saida)
        _log(f"🏁 Concluído: {len(lista_precos_saldo)} registros salvos em '{arquivo_saida}'.")
    else:
        _log("Nenhum registro válido para salvar.")
