import tkinter as tk
from tkinter import messagebox
from estoque_app import EstoqueApp

class LoginApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Login com Token da Tiny")
        self.master.geometry("400x150")

        tk.Label(master, text="Digite seu Token da Tiny:").pack(pady=10)
        self.entry_token = tk.Entry(master, width=50)
        self.entry_token.pack(pady=5)

        btn_login = tk.Button(master, text="Entrar", command=self.abrir_app_principal)
        btn_login.pack(pady=15)

    def abrir_app_principal(self):
        token = self.entry_token.get().strip()

        if not token:
            messagebox.showerror("Erro", "Por favor, digite o token.")
            return

        self.master.destroy()
        root_app = tk.Tk()
        EstoqueApp(root_app, token)
        root_app.mainloop()

if __name__ == "__main__":
    root_login = tk.Tk()
    LoginApp(root_login)
    root_login.mainloop()
