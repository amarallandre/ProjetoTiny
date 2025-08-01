import pandas as pd
import os


def salvar_log_alteracoes_excel(alteracoes, nome_arquivo="alteracoes_precos.xlsx"):
    """
    Salva um log das alterações de preços em um arquivo Excel.

    alteracoes: lista de dicts, exemplo:
      [
        {
          "codigo": "123",
          "nome": "Produto X",
          "preco_antigo": 10.0,
          "preco_novo": 11.0,
          "data": "2025-07-08 21:45:00"
        },
        ...
      ]
    """
    if not alteracoes:
        print("Nenhuma alteração detectada. Excel não será salvo.")
        return

    df = pd.DataFrame(alteracoes)

    caminho_completo = os.path.abspath(nome_arquivo)
    print(f"📁 Salvando Excel em: {caminho_completo}")

    try:
        if os.path.exists(nome_arquivo):
            # Junta com as alterações anteriores
            df_existente = pd.read_excel(nome_arquivo)
            df = pd.concat([df_existente, df], ignore_index=True)

        df.to_excel(nome_arquivo, index=False)
        print("✅ Excel salvo com sucesso.")

    except Exception as e:
        print(f"❌ Erro ao salvar Excel: {e}")