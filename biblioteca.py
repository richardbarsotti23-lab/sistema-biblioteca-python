"""
Sistema de Gerenciamento de Biblioteca
Autor: Richard Barsotti Silva

Aplicação desktop com interface gráfica (Tkinter) e banco de dados
SQLite para cadastro, empréstimo e devolução de livros.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

NOME_BANCO = "biblioteca.db"


def conectar():
    """Abre uma conexão com o banco de dados SQLite."""
    return sqlite3.connect(NOME_BANCO)


def criar_tabela():
    """Cria a tabela de livros caso ela ainda não exista."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            emprestado INTEGER NOT NULL DEFAULT 0,
            emprestado_para TEXT
        )
    """)
    conexao.commit()
    conexao.close()


class AplicativoBiblioteca:
    """Classe principal da interface gráfica do sistema de biblioteca."""

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Sistema de Biblioteca")
        self.raiz.geometry("700x500")

        self._montar_formulario()
        self._montar_tabela()
        self._montar_botoes()
        self.atualizar_lista()

    def _montar_formulario(self):
        """Cria os campos de entrada para título e autor."""
        quadro = tk.Frame(self.raiz, padx=10, pady=10)
        quadro.pack(fill="x")

        tk.Label(quadro, text="Título:").grid(row=0, column=0, sticky="w")
        self.entrada_titulo = tk.Entry(quadro, width=40)
        self.entrada_titulo.grid(row=0, column=1, padx=5)

        tk.Label(quadro, text="Autor:").grid(row=1, column=0, sticky="w")
        self.entrada_autor = tk.Entry(quadro, width=40)
        self.entrada_autor.grid(row=1, column=1, padx=5)

        tk.Button(
            quadro, text="Cadastrar Livro", command=self.cadastrar_livro
        ).grid(row=0, column=2, rowspan=2, padx=10)

    def _montar_tabela(self):
        """Cria a tabela (Treeview) que lista os livros cadastrados."""
        colunas = ("id", "titulo", "autor", "status")
        self.tabela = ttk.Treeview(self.raiz, columns=colunas, show="headings")

        self.tabela.heading("id", text="ID")
        self.tabela.heading("titulo", text="Título")
        self.tabela.heading("autor", text="Autor")
        self.tabela.heading("status", text="Status")

        self.tabela.column("id", width=40)
        self.tabela.column("titulo", width=250)
        self.tabela.column("autor", width=180)
        self.tabela.column("status", width=150)

        self.tabela.pack(fill="both", expand=True, padx=10, pady=10)

    def _montar_botoes(self):
        """Cria os botões de ação: emprestar, devolver e remover."""
        quadro = tk.Frame(self.raiz, padx=10, pady=10)
        quadro.pack(fill="x")

        tk.Button(
            quadro, text="Emprestar", command=self.emprestar_livro
        ).pack(side="left", padx=5)

        tk.Button(
            quadro, text="Devolver", command=self.devolver_livro
        ).pack(side="left", padx=5)

        tk.Button(
            quadro, text="Remover", command=self.remover_livro
        ).pack(side="left", padx=5)

    def atualizar_lista(self):
        """Recarrega a tabela com os dados atuais do banco."""
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, titulo, autor, emprestado, emprestado_para FROM livros")
        for livro_id, titulo, autor, emprestado, para in cursor.fetchall():
            status = f"Emprestado ({para})" if emprestado else "Disponível"
            self.tabela.insert("", "end", values=(livro_id, titulo, autor, status))
        conexao.close()

    def cadastrar_livro(self):
        """Cadastra um novo livro no banco de dados."""
        titulo = self.entrada_titulo.get().strip()
        autor = self.entrada_autor.get().strip()

        if not titulo or not autor:
            messagebox.showwarning("Aviso", "Preencha título e autor.")
            return

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO livros (titulo, autor, emprestado) VALUES (?, ?, 0)",
            (titulo, autor)
        )
        conexao.commit()
        conexao.close()

        self.entrada_titulo.delete(0, tk.END)
        self.entrada_autor.delete(0, tk.END)
        self.atualizar_lista()

    def _obter_selecionado(self):
        """Retorna o ID do livro selecionado na tabela, ou None."""
        selecionado = self.tabela.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro na lista.")
            return None
        return self.tabela.item(selecionado[0])["values"][0]

    def emprestar_livro(self):
        """Marca o livro selecionado como emprestado."""
        livro_id = self._obter_selecionado()
        if livro_id is None:
            return

        janela = tk.Toplevel(self.raiz)
        janela.title("Emprestar Livro")
        tk.Label(janela, text="Nome de quem vai levar o livro:").pack(padx=10, pady=5)
        entrada_nome = tk.Entry(janela, width=30)
        entrada_nome.pack(padx=10, pady=5)

        def confirmar():
            nome = entrada_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Digite um nome.")
                return
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE livros SET emprestado = 1, emprestado_para = ? WHERE id = ?",
                (nome, livro_id)
            )
            conexao.commit()
            conexao.close()
            janela.destroy()
            self.atualizar_lista()

        tk.Button(janela, text="Confirmar", command=confirmar).pack(pady=5)

    def devolver_livro(self):
        """Marca o livro selecionado como devolvido/disponível."""
        livro_id = self._obter_selecionado()
        if livro_id is None:
            return

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE livros SET emprestado = 0, emprestado_para = NULL WHERE id = ?",
            (livro_id,)
        )
        conexao.commit()
        conexao.close()
        self.atualizar_lista()

    def remover_livro(self):
        """Remove o livro selecionado do banco de dados."""
        livro_id = self._obter_selecionado()
        if livro_id is None:
            return

        confirmar = messagebox.askyesno("Confirmar", "Deseja remover este livro?")
        if not confirmar:
            return

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
        conexao.commit()
        conexao.close()
        self.atualizar_lista()


def main():
    criar_tabela()
    raiz = tk.Tk()
    AplicativoBiblioteca(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
