import tkinter as tk
from tkinter import messagebox
from estoque_app import EstoqueApp  # nome do seu arquivo acima (sem .py)

class LoginApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")

        tk.Label(master, text="Usuário:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_usuario = tk.Entry(master)
        self.entry_usuario.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(master, text="Senha:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_senha = tk.Entry(master, show="*")
        self.entry_senha.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(master, text="Token Tiny:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_token = tk.Entry(master)
        self.entry_token.grid(row=2, column=1, padx=10, pady=5)

        btn_login = tk.Button(master, text="Entrar", command=self.verificar_login)
        btn_login.grid(row=3, column=0, columnspan=2, pady=10)

    def verificar_login(self):
        usuario = self.entry_usuario.get()
        senha = self.entry_senha.get()
        token = self.entry_token.get()

        if usuario == "admin" and senha == "123":
            self.abrir_app_principal(token)
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos")

    def abrir_app_principal(self, token):
        self.master.destroy()  # fecha a janela de login
        root_app = tk.Tk()
        EstoqueApp(root_app, token)
        root_app.mainloop()


if __name__ == "__main__":
    root_login = tk.Tk()
    LoginApp(root_login)
    root_login.mainloop()
