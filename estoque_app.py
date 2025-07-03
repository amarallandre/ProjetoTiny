import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime
import json
import requests
from pathlib import Path
import os

from src.mapeamento import monitorar_estoque
from src.obter_produto import obter_produtos

ARQUIVO_PRECOS = "precos_e_saldo.json"



class EstoqueApp:



    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Monitor Tiny - Estoque & Preço")

        self.is_running = False
        self.thread = None
        self.produtos = []

        # Frame monitoramento
        monitor_frame = tk.LabelFrame(root, text="Monitorar Estoque", padx=10, pady=10)
        monitor_frame.pack(fill="x", padx=10, pady=5)

        self.btn_start = tk.Button(monitor_frame, text="Iniciar Monitoramento", command=self.start_monitor)
        self.btn_start.pack(side="left", padx=5, pady=5)

        self.btn_stop = tk.Button(monitor_frame, text="Parar Monitoramento", command=self.stop_monitor, state=tk.DISABLED)
        self.btn_stop.pack(side="left", padx=5, pady=5)

        self.status_label = tk.Label(monitor_frame, text="Status: Parado")
        self.status_label.pack(side="left", padx=20)

        # Área de log
        self.log_area = scrolledtext.ScrolledText(root, width=80, height=12, state='disabled', wrap='word')
        self.log_area.pack(padx=10, pady=5)

        # Seção preços automáticos
        self.criar_secao_precos()

        # Seção edição manual de preço
        self.criar_secao_edicao_manual()

        # Carregar produtos inicialmente
        self.carregar_produtos()

    def log(self, message):
        def append():
            self.log_area['state'] = 'normal'
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_area.see(tk.END)
            self.log_area['state'] = 'disabled'
        self.root.after(0, append)

    # --- Monitoramento ---
    def start_monitor(self):
        if not self.is_running:
            self.is_running = True
            self.status_label.config(text="Status: Monitorando...")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.log("Monitoramento iniciado.")

            def tarefa():
                monitorar_estoque(
                    token=self.token,
                    parar_callback=self.should_stop,
                    log_func=self.log,
                    intervalo=20,
                    chamar_obter_produtos=lambda: obter_produtos(
                        token=self.token,
                        parar_callback=self.should_stop,
                        log_func=self.log
                    )
                )
                self.is_running = False
                self.root.after(0, self.finalizar_monitoramento_e_carregar)

            self.thread = threading.Thread(target=tarefa, daemon=True)
            self.thread.start()

    def stop_monitor(self):
        if self.is_running:
            self.is_running = False
            self.status_label.config(text="Status: Parando...")
            self.log("Solicitada parada do monitoramento...")

    def should_stop(self):
        return not self.is_running

    def finalizar_monitoramento(self):
        self.status_label.config(text="Status: Parado")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.log("Monitoramento parado.")

    def finalizar_monitoramento_e_carregar(self):
        self.finalizar_monitoramento()
        self.carregar_produtos()

    # --- Seção de preços automáticos ---
    def criar_secao_precos(self):
        preco_frame = tk.LabelFrame(self.root, text="Controle Automático de Preço", padx=10, pady=10)
        preco_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(preco_frame, text="Aumentar preço (%) se saldo > 10:").pack(side="left")
        self.entry_aumento = tk.Entry(preco_frame, width=5)
        self.entry_aumento.insert(0, "5")
        self.entry_aumento.pack(side="left", padx=5)

        tk.Label(preco_frame, text="Reduzir preço (%) se saldo ≤ 10:").pack(side="left")
        self.entry_reducao = tk.Entry(preco_frame, width=5)
        self.entry_reducao.insert(0, "-10")
        self.entry_reducao.pack(side="left", padx=5)

        btn_ajustar = tk.Button(preco_frame, text="Atualizar Preços Automaticamente", command=self.ajustar_precos)
        btn_ajustar.pack(side="left", padx=10)

    def ajustar_precos(self):
        try:
            aumento = float(self.entry_aumento.get())
            reducao = float(self.entry_reducao.get())
        except ValueError:
            self.log("⚠️ Insira valores válidos para percentuais.")
            return

        self.log("Iniciando ajuste automático de preços...")
        threading.Thread(target=self._ajustar_precos_thread, args=(aumento, reducao), daemon=True).start()

    def _ajustar_precos_thread(self, aumento, reducao):
        self._ajustar_precos_automatico(
            caminho_arquivo=ARQUIVO_PRECOS,
            token=self.token,
            percentual_aumento=aumento,
            percentual_reducao=reducao,
            log_func=self.log
        )
        self.log("Ajuste de preços finalizado.")
        self.carregar_produtos()

    def _ajustar_precos_automatico(self, caminho_arquivo, token, percentual_aumento, percentual_reducao, log_func=None):
        URL_API = f"https://api.tiny.com.br/api2/produto.atualizar.precos.php?token={token}"

        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                produtos = json.load(f)
        except Exception as e:
            if log_func:
                log_func(f"Erro ao ler arquivo {caminho_arquivo}: {e}")
            return

        if not produtos:
            if log_func:
                log_func("Arquivo de preços vazio ou inválido.")
            return

        for prod in produtos:
            saldo = prod.get("saldo", 0)
            preco_antigo = prod.get("preco", 0)
            preco_promocional_antigo = prod.get("preco_promocional", 0)

            if saldo <= 10:
                fator = 1 + (percentual_reducao / 100)
            else:
                fator = 1 + (percentual_aumento / 100)

            preco_novo = round(preco_antigo * fator, 2)
            preco_promo_novo = round(preco_promocional_antigo * fator, 2) if preco_promocional_antigo else 0

            prod["preco"] = preco_novo
            if preco_promocional_antigo:
                prod["preco_promocional"] = preco_promo_novo

            if log_func:
                log_func(f"Produto {prod['codigo']} (Saldo: {saldo}): preço {preco_antigo} -> {preco_novo}")

            payload = {"precos": [{
                "id": prod["id"],
                "preco": preco_novo,
                **({"preco_promocional": preco_promo_novo} if preco_promocional_antigo else {})
            }]}

            try:
                r = requests.post(URL_API, json=payload,
                                  headers={"Content-Type": "application/json; charset=utf-8"},
                                  timeout=30)
                r.raise_for_status()
                if log_func:
                    log_func(f"✔️ Preço atualizado na API para produto {prod['codigo']}")
            except Exception as e:
                if log_func:
                    log_func(f"❌ Erro ao atualizar preço produto {prod['codigo']}: {e}")

        # Salva localmente o arquivo com os preços atualizados
        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(produtos, f, indent=2, ensure_ascii=False)
            if log_func:
                log_func(f"Arquivo '{caminho_arquivo}' atualizado localmente.")
        except Exception as e:
            if log_func:
                log_func(f"Erro ao salvar arquivo local: {e}")

    # --- Seção de edição manual ---
    def criar_secao_edicao_manual(self):
        manual_frame = tk.LabelFrame(self.root, text="Edição Manual de Preço", padx=10, pady=10)
        manual_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Lista de produtos
        self.lista_produtos = tk.Listbox(manual_frame, height=10, width=50)
        self.lista_produtos.pack(side="left", fill="y")
        self.lista_produtos.bind("<<ListboxSelect>>", self.produto_selecionado)

        # Scroll para lista
        scrollbar = tk.Scrollbar(manual_frame)
        scrollbar.pack(side="left", fill="y")
        self.lista_produtos.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lista_produtos.yview)

        # Frame para campos de edição
        editar_frame = tk.Frame(manual_frame)
        editar_frame.pack(side="left", fill="both", expand=True, padx=10)

        tk.Label(editar_frame, text="Nome:").grid(row=0, column=0, sticky="e")
        self.entry_nome = tk.Entry(editar_frame, state="readonly")
        self.entry_nome.grid(row=0, column=1, sticky="w")

        tk.Label(editar_frame, text="Preço:").grid(row=1, column=0, sticky="e")
        self.entry_preco = tk.Entry(editar_frame)
        self.entry_preco.grid(row=1, column=1, sticky="w")

        tk.Label(editar_frame, text="Preço Promocional:").grid(row=2, column=0, sticky="e")
        self.entry_preco_promo = tk.Entry(editar_frame)
        self.entry_preco_promo.grid(row=2, column=1, sticky="w")

        self.btn_salvar_preco = tk.Button(editar_frame, text="Salvar Alterações", command=self.salvar_preco_manual)
        self.btn_salvar_preco.grid(row=3, column=0, columnspan=2, pady=10)

    def carregar_produtos(self):
        self.produtos = []
        self.lista_produtos.delete(0, tk.END)
        if not os.path.exists(ARQUIVO_PRECOS):
            self.log(f"Arquivo {ARQUIVO_PRECOS} não encontrado.")
            return

        try:
            with open(ARQUIVO_PRECOS, "r", encoding="utf-8") as f:
                self.produtos = json.load(f)
        except Exception as e:
            self.log(f"Erro ao carregar produtos: {e}")
            return

        for p in self.produtos:
            self.lista_produtos.insert(tk.END, f"{p.get('nome', '---')} (Saldo: {p.get('saldo', 0)})")

    def produto_selecionado(self, event):
        self.log("🔍 Produto foi clicado.")
        if not self.lista_produtos.curselection():
            self.log("⚠️ Nenhum item selecionado.")
            return
        if not self.lista_produtos.curselection():
            return
        index = self.lista_produtos.curselection()[0]
        prod = self.produtos[index]
        self.entry_nome.config(state="normal")
        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, prod.get("nome", ""))
        self.entry_nome.config(state="readonly")

        self.entry_preco.delete(0, tk.END)
        self.entry_preco.insert(0, f"{prod.get('preco', 0):.2f}")

        self.entry_preco_promo.delete(0, tk.END)
        self.entry_preco_promo.insert(0, f"{prod.get('preco_promocional', 0):.2f}")

    def salvar_preco_manual(self):
        if not self.lista_produtos.curselection():
            self.log("Selecione um produto para salvar.")
            return

        index = self.lista_produtos.curselection()[0]
        prod = self.produtos[index]

        try:
            novo_preco = float(self.entry_preco.get().replace(",", "."))
            novo_promo = float(self.entry_preco_promo.get().replace(",", "."))
        except ValueError:
            self.log("Valores de preço inválidos.")
            return

        prod["preco"] = round(novo_preco, 2)
        prod["preco_promocional"] = round(novo_promo, 2)

        # Enviar para API numa thread
        threading.Thread(target=self._enviar_preco_api, args=(prod,), daemon=True).start()

    def _enviar_preco_api(self, produto):
        URL_API = f"https://api.tiny.com.br/api2/produto.atualizar.precos.php?token={self.token}"
        payload = {"precos": [{
            "id": produto["id"],
            "preco": produto["preco"],
            **({"preco_promocional": produto["preco_promocional"]} if produto.get("preco_promocional") else {})
        }]}

        try:
            r = requests.post(URL_API, json=payload,
                              headers={"Content-Type": "application/json; charset=utf-8"},
                              timeout=30)
            r.raise_for_status()
            self.log(f"✔️ Preço manual atualizado na API para produto {produto['codigo']}")
            self._atualizar_arquivo_local(produto)
        except Exception as e:
            self.log(f"❌ Erro ao atualizar preço manual produto {produto['codigo']}: {e}")

    def _atualizar_arquivo_local(self, produto_atualizado):
        # Atualiza o arquivo local com os dados alterados manualmente
        try:
            for p in self.produtos:
                if p["id"] == produto_atualizado["id"]:
                    p.update(produto_atualizado)
                    break
            with open(ARQUIVO_PRECOS, "w", encoding="utf-8") as f:
                json.dump(self.produtos, f, indent=2, ensure_ascii=False)
            self.log(f"Arquivo local '{ARQUIVO_PRECOS}' atualizado com a alteração manual.")
        except Exception as e:
            self.log(f"Erro ao salvar arquivo local: {e}")

def iniciar_aplicacao():
    TOKEN = 'faae0168b12e99a07d0f7b58c81830baec7e6682'
    root = tk.Tk()
    EstoqueApp(root, TOKEN)
    root.mainloop()

if __name__ == "__main__":
    iniciar_aplicacao()