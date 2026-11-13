import math
import tkinter as tk
from tkinter import messagebox, ttk

from programa1 import (
    carregar_estoque,
    carregar_historico,
    registrar_movimentacao,
    salvar_estoque,
)


class InterfaceEstoque:
    def __init__(self, janela: tk.Tk, estoque: dict) -> None:
        self.janela = janela
        self.estoque = estoque
        self.janela.title("Controle de Estoque")
        self.janela.geometry("1080x700")
        self.janela.minsize(820, 560)
        self.janela.configure(bg="#f4f6fb")

        estilo = ttk.Style()
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("TFrame", background="#f4f6fb")
        estilo.configure("TLabel", background="#f4f6fb", foreground="#172033")
        estilo.configure(
            "PageTitle.TLabel",
            font=("Segoe UI", 24, "bold"),
            foreground="#172033",
        )
        estilo.configure(
            "Subtitle.TLabel", font=("Segoe UI", 10), foreground="#68758a"
        )
        estilo.configure("Card.TFrame", background="#ffffff")
        estilo.configure(
            "CardTitle.TLabel",
            background="#ffffff",
            foreground="#68758a",
            font=("Segoe UI", 9),
        )
        estilo.configure(
            "CardValue.TLabel",
            background="#ffffff",
            foreground="#172033",
            font=("Segoe UI", 19, "bold"),
        )
        estilo.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#273449",
            rowheight=38,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        estilo.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", "#1d4ed8")],
        )
        estilo.configure(
            "Treeview.Heading",
            background="#f8fafc",
            foreground="#526078",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 12),
            relief="flat",
        )
        estilo.map("Treeview.Heading", background=[("active", "#eef2f7")])
        estilo.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(12, 9))
        estilo.configure(
            "Primary.TButton",
            background="#2563eb",
            foreground="#ffffff",
            borderwidth=0,
        )
        estilo.map(
            "Primary.TButton",
            background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
            foreground=[("active", "#ffffff")],
        )
        estilo.configure(
            "Toolbar.TFrame", background="#ffffff", padding=(10, 8)
        )
        estilo.configure(
            "Search.TEntry",
            fieldbackground="#ffffff",
            foreground="#172033",
            padding=(9, 8),
        )
        estilo.configure("Status.TLabel", foreground="#68758a", font=("Segoe UI", 9))

        self.busca = tk.StringVar()
        self.status = tk.StringVar(value="Estoque carregado.")
        self.resumos: dict[str, ttk.Label] = {}
        self._montar_tela()
        self.atualizar_lista()

    def _montar_tela(self) -> None:
        conteudo = ttk.Frame(self.janela, padding=(30, 26))
        conteudo.pack(fill="both", expand=True)

        cabecalho = ttk.Frame(conteudo)
        cabecalho.pack(fill="x", pady=(0, 22))
        ttk.Label(
            cabecalho, text="Controle de Estoque", style="PageTitle.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            cabecalho,
            text="Visão geral dos produtos e movimentações do seu estoque.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        cartoes = ttk.Frame(conteudo)
        cartoes.pack(fill="x", pady=(0, 20))
        for coluna, (titulo, chave) in enumerate(
            (
                ("PRODUTOS CADASTRADOS", "produtos"),
                ("UNIDADES EM ESTOQUE", "unidades"),
                ("VALOR TOTAL DO ESTOQUE", "valor"),
            )
        ):
            cartao = ttk.Frame(cartoes, style="Card.TFrame", padding=(18, 15))
            cartao.grid(row=0, column=coluna, sticky="nsew", padx=(0, 12))
            ttk.Label(cartao, text=titulo, style="CardTitle.TLabel").pack(
                anchor="w", pady=(0, 7)
            )
            valor = ttk.Label(cartao, text="0", style="CardValue.TLabel")
            valor.pack(anchor="w")
            self.resumos[chave] = valor
            cartoes.columnconfigure(coluna, weight=1)
        cartoes.columnconfigure(2, weight=1)

        barra = ttk.Frame(conteudo, style="Toolbar.TFrame")
        barra.pack(fill="x", pady=(0, 14))
        campo_busca = ttk.Entry(
            barra, textvariable=self.busca, style="Search.TEntry"
        )
        campo_busca.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.busca.trace_add("write", lambda *_: self.atualizar_lista())
        ttk.Button(
            barra,
            text="+  Cadastrar produto",
            command=self.cadastrar,
            style="Primary.TButton",
        ).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(barra, text="Entrada / saída", command=self.movimentar).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(barra, text="Histórico", command=self.ver_historico).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(barra, text="Remover", command=self.remover).pack(side="left")

        tabela_frame = ttk.Frame(conteudo)
        tabela_frame.pack(fill="both", expand=True)
        tabela_frame.configure(style="Card.TFrame", padding=1)
        colunas = ("codigo", "nome", "quantidade", "preco", "total")
        self.tabela = ttk.Treeview(
            tabela_frame, columns=colunas, show="headings", selectmode="browse"
        )
        for coluna, titulo, largura, ancora in (
            ("codigo", "Código", 110, "w"),
            ("nome", "Produto", 300, "w"),
            ("quantidade", "Quantidade", 130, "center"),
            ("preco", "Preço unitário", 150, "e"),
            ("total", "Valor em estoque", 170, "e"),
        ):
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=largura, anchor=ancora)
        rolagem = ttk.Scrollbar(
            tabela_frame, orient="vertical", command=self.tabela.yview
        )
        self.tabela.configure(yscrollcommand=rolagem.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")

        ttk.Label(
            conteudo, textvariable=self.status, style="Status.TLabel"
        ).pack(anchor="w", pady=(12, 0))

    @staticmethod
    def _moeda(valor: float) -> str:
        formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace(
            "X", "."
        )
        return f"R$ {formatado}"

    def atualizar_lista(self) -> None:
        termo = self.busca.get().strip().casefold()
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for indice, (codigo, produto) in enumerate(sorted(self.estoque.items())):
            nome = str(produto["nome"])
            if termo and termo not in codigo.casefold() and termo not in nome.casefold():
                continue
            quantidade = int(produto["quantidade"])
            preco = float(produto["preco"])
            self.tabela.insert(
                "",
                "end",
                values=(
                    codigo,
                    nome,
                    quantidade,
                    self._moeda(preco),
                    self._moeda(quantidade * preco),
                ),
                tags=("par",) if indice % 2 == 0 else ("impar",),
            )

        self.tabela.tag_configure("par", background="#ffffff")
        self.tabela.tag_configure("impar", background="#f8fafc")
        self.resumos["produtos"].configure(text=str(len(self.estoque)))
        self.resumos["unidades"].configure(
            text=str(sum(int(item["quantidade"]) for item in self.estoque.values()))
        )
        valor_total = sum(
            int(item["quantidade"]) * float(item["preco"])
            for item in self.estoque.values()
        )
        self.resumos["valor"].configure(text=self._moeda(valor_total))

    def _salvar(self) -> bool:
        try:
            salvar_estoque(self.estoque)
        except (OSError, ValueError) as erro:
            messagebox.showerror(
                "Erro ao salvar", f"Não foi possível salvar o estoque:\n{erro}"
            )
            return False
        return True

    def _produto_selecionado(self) -> str | None:
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showinfo(
                "Selecione um produto", "Selecione um produto na tabela primeiro."
            )
            return None
        return str(self.tabela.item(selecionados[0], "values")[0])

    def cadastrar(self) -> None:
        dialogo = tk.Toplevel(self.janela)
        dialogo.title("Cadastrar produto")
        dialogo.resizable(False, False)
        dialogo.transient(self.janela)
        dialogo.grab_set()

        campos: dict[str, ttk.Entry] = {}
        for linha, (chave, rotulo) in enumerate(
            (
                ("codigo", "Código"),
                ("nome", "Nome do produto"),
                ("quantidade", "Quantidade inicial"),
                ("preco", "Preço unitário (R$)"),
            )
        ):
            ttk.Label(dialogo, text=rotulo).grid(
                row=linha, column=0, sticky="w", padx=16, pady=(12, 0)
            )
            entrada = ttk.Entry(dialogo, width=34)
            entrada.grid(row=linha, column=1, padx=16, pady=(12, 0))
            campos[chave] = entrada

        def confirmar() -> None:
            codigo = campos["codigo"].get().strip().upper()
            nome = campos["nome"].get().strip()
            if not codigo or not nome:
                messagebox.showwarning(
                    "Dados obrigatórios", "Preencha o código e o nome do produto."
                )
                return
            if codigo in self.estoque:
                messagebox.showwarning(
                    "Código existente", "Já existe um produto com esse código."
                )
                return
            try:
                quantidade = int(campos["quantidade"].get().strip())
                preco = float(campos["preco"].get().strip().replace(",", "."))
                if quantidade < 0 or preco < 0 or not math.isfinite(preco):
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Dados inválidos",
                    "Informe uma quantidade inteira não negativa e um preço válido.",
                )
                return

            self.estoque[codigo] = {
                "nome": nome,
                "quantidade": quantidade,
                "preco": preco,
            }
            if not self._salvar():
                del self.estoque[codigo]
                return
            self.atualizar_lista()
            self.status.set(f"Produto {nome} cadastrado.")
            dialogo.destroy()

        botoes = ttk.Frame(dialogo)
        botoes.grid(row=4, column=0, columnspan=2, sticky="e", padx=16, pady=16)
        ttk.Button(botoes, text="Cancelar", command=dialogo.destroy).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(botoes, text="Salvar produto", command=confirmar).pack(side="left")
        campos["codigo"].focus_set()

    def movimentar(self) -> None:
        codigo = self._produto_selecionado()
        if codigo is None:
            return

        dialogo = tk.Toplevel(self.janela)
        dialogo.title("Movimentar estoque")
        dialogo.resizable(False, False)
        dialogo.transient(self.janela)
        dialogo.grab_set()
        ttk.Label(
            dialogo,
            text=f"{self.estoque[codigo]['nome']} — disponível: "
            f"{self.estoque[codigo]['quantidade']}",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))
        operacao = tk.StringVar(value="E")
        ttk.Radiobutton(
            dialogo, text="Entrada", variable=operacao, value="E"
        ).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        ttk.Radiobutton(
            dialogo, text="Saída", variable=operacao, value="S"
        ).grid(row=1, column=1, sticky="w", padx=16, pady=6)
        ttk.Label(dialogo, text="Quantidade").grid(
            row=2, column=0, sticky="w", padx=16, pady=(8, 0)
        )
        quantidade_campo = ttk.Entry(dialogo, width=20)
        quantidade_campo.grid(row=2, column=1, padx=16, pady=(8, 0))

        def confirmar() -> None:
            try:
                quantidade = int(quantidade_campo.get().strip())
                if quantidade <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Quantidade inválida",
                    "Informe uma quantidade inteira maior que zero.",
                )
                return

            atual = int(self.estoque[codigo]["quantidade"])
            if operacao.get() == "S" and quantidade > atual:
                messagebox.showwarning(
                    "Estoque insuficiente",
                    f"Há apenas {atual} unidade(s) disponíveis.",
                )
                return
            nova_quantidade = (
                atual + quantidade if operacao.get() == "E" else atual - quantidade
            )
            self.estoque[codigo]["quantidade"] = nova_quantidade
            if not self._salvar():
                self.estoque[codigo]["quantidade"] = atual
                return
            tipo = "Entrada" if operacao.get() == "E" else "Saída"
            try:
                registrar_movimentacao(
                    codigo,
                    str(self.estoque[codigo]["nome"]),
                    tipo,
                    quantidade,
                )
            except (OSError, ValueError) as erro:
                self.estoque[codigo]["quantidade"] = atual
                if not self._salvar():
                    messagebox.showerror(
                        "Erro ao reverter estoque",
                        "Não foi possível reverter a quantidade. Confira o arquivo "
                        "de estoque e o backup antes de continuar.",
                        parent=self.janela,
                    )
                messagebox.showerror(
                    "Erro ao registrar movimentação",
                    f"A movimentação não foi registrada:\n{erro}",
                    parent=self.janela,
                )
                return
            self.atualizar_lista()
            self.status.set(f"{tipo} de {quantidade} unidade(s) registrada.")
            dialogo.destroy()

        botoes = ttk.Frame(dialogo)
        botoes.grid(row=3, column=0, columnspan=2, sticky="e", padx=16, pady=16)
        ttk.Button(botoes, text="Cancelar", command=dialogo.destroy).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(botoes, text="Confirmar", command=confirmar).pack(side="left")
        quantidade_campo.focus_set()

    def ver_historico(self) -> None:
        try:
            historico = carregar_historico()
        except (OSError, ValueError) as erro:
            messagebox.showerror(
                "Erro ao carregar histórico",
                f"Não foi possível carregar o histórico:\n{erro}",
                parent=self.janela,
            )
            return

        dialogo = tk.Toplevel(self.janela)
        dialogo.title("Histórico de movimentações")
        dialogo.geometry("780x440")
        dialogo.minsize(620, 320)
        dialogo.transient(self.janela)

        conteudo = ttk.Frame(dialogo, padding=18)
        conteudo.pack(fill="both", expand=True)
        ttk.Label(
            conteudo, text="Movimentações", style="PageTitle.TLabel"
        ).pack(anchor="w", pady=(0, 14))

        colunas = ("data", "codigo", "nome", "operacao", "quantidade")
        tabela = ttk.Treeview(conteudo, columns=colunas, show="headings")
        for coluna, titulo, largura, ancora in (
            ("data", "Data e hora", 180, "w"),
            ("codigo", "Código", 90, "w"),
            ("nome", "Produto", 220, "w"),
            ("operacao", "Operação", 100, "center"),
            ("quantidade", "Quantidade", 100, "center"),
        ):
            tabela.heading(coluna, text=titulo)
            tabela.column(coluna, width=largura, anchor=ancora)

        rolagem = ttk.Scrollbar(conteudo, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=rolagem.set)
        tabela.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")
        for registro in reversed(historico):
            tabela.insert(
                "",
                "end",
                values=(
                    registro["data_hora"],
                    registro["codigo"],
                    registro["nome"],
                    registro["operacao"],
                    registro["quantidade"],
                ),
            )
        if not historico:
            ttk.Label(
                conteudo,
                text="Nenhuma movimentação foi registrada ainda.",
                style="Subtitle.TLabel",
            ).pack(anchor="w", pady=(10, 0))

    def remover(self) -> None:
        codigo = self._produto_selecionado()
        if codigo is None:
            return
        nome = str(self.estoque[codigo]["nome"])
        if not messagebox.askyesno(
            "Confirmar remoção", f"Deseja remover o produto {nome} ({codigo})?"
        ):
            return

        produto = self.estoque.pop(codigo)
        if not self._salvar():
            self.estoque[codigo] = produto
            return
        self.atualizar_lista()
        self.status.set(f"Produto {nome} removido.")


def main() -> None:
    janela = tk.Tk()
    janela.withdraw()
    try:
        estoque = carregar_estoque()
    except (OSError, ValueError) as erro:
        messagebox.showerror(
            "Erro ao carregar estoque",
            f"Não foi possível carregar o arquivo de estoque:\n{erro}",
            parent=janela,
        )
        janela.destroy()
        return

    janela.deiconify()
    InterfaceEstoque(janela, estoque)
    janela.mainloop()


if __name__ == "__main__":
    main()
