import json
import math
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


ARQUIVO_ESTOQUE = Path(__file__).with_name("estoque.json")
ARQUIVO_HISTORICO = Path(__file__).with_name("historico.json")


def _salvar_json_seguro(caminho: Path, dados: object) -> None:
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())

        if caminho.exists():
            shutil.copy2(caminho, caminho.with_suffix(caminho.suffix + ".bak"))
        os.replace(temporario, caminho)
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()


def _validar_estoque(estoque: object) -> dict[str, dict[str, str | int | float]]:
    if not isinstance(estoque, dict):
        raise ValueError("O arquivo de estoque precisa conter um objeto JSON.")

    for codigo, produto in estoque.items():
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError("O estoque contém um código de produto inválido.")
        if not isinstance(produto, dict):
            raise ValueError(f"O produto {codigo} precisa ser um objeto JSON.")

        nome = produto.get("nome")
        quantidade = produto.get("quantidade")
        preco = produto.get("preco")
        preco_valido = isinstance(preco, (int, float)) and not isinstance(
            preco, bool
        )
        if preco_valido:
            try:
                preco_valido = math.isfinite(float(preco))
            except OverflowError:
                preco_valido = False
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError(f"O produto {codigo} não possui um nome válido.")
        if (
            not isinstance(quantidade, int)
            or isinstance(quantidade, bool)
            or quantidade < 0
        ):
            raise ValueError(f"A quantidade do produto {codigo} é inválida.")
        if not preco_valido or preco < 0:
            raise ValueError(f"O preço do produto {codigo} é inválido.")

    return estoque


def carregar_estoque() -> dict[str, dict[str, str | int | float]]:
    if not ARQUIVO_ESTOQUE.exists():
        return {}

    with ARQUIVO_ESTOQUE.open("r", encoding="utf-8") as arquivo:
        estoque = json.load(arquivo)

    return _validar_estoque(estoque)


def salvar_estoque(estoque: dict[str, dict[str, str | int | float]]) -> None:
    _validar_estoque(estoque)
    _salvar_json_seguro(ARQUIVO_ESTOQUE, estoque)


def carregar_historico() -> list[dict[str, str | int]]:
    if not ARQUIVO_HISTORICO.exists():
        return []

    with ARQUIVO_HISTORICO.open("r", encoding="utf-8") as arquivo:
        historico = json.load(arquivo)

    if not isinstance(historico, list):
        raise ValueError("O arquivo de histórico precisa conter uma lista JSON.")
    for registro in historico:
        if (
            not isinstance(registro, dict)
            or not isinstance(registro.get("data_hora"), str)
            or not isinstance(registro.get("codigo"), str)
            or not isinstance(registro.get("nome"), str)
            or not isinstance(registro.get("operacao"), str)
            or registro["operacao"] not in {"Entrada", "Saída"}
            or not isinstance(registro.get("quantidade"), int)
            or isinstance(registro.get("quantidade"), bool)
            or registro["quantidade"] <= 0
        ):
            raise ValueError("O arquivo de histórico contém um registro inválido.")
    return historico


def registrar_movimentacao(
    codigo: str, nome: str, operacao: str, quantidade: int
) -> None:
    historico = carregar_historico()
    historico.append(
        {
            "data_hora": datetime.now().astimezone().isoformat(timespec="seconds"),
            "codigo": codigo,
            "nome": nome,
            "operacao": operacao,
            "quantidade": quantidade,
        }
    )
    _salvar_json_seguro(ARQUIVO_HISTORICO, historico)


def ler_inteiro_nao_negativo(mensagem: str) -> int:
    while True:
        try:
            valor = int(input(mensagem))
            if valor < 0:
                print("Digite um número igual ou maior que zero.")
                continue
            return valor
        except ValueError:
            print("Digite um número inteiro válido.")


def ler_preco(mensagem: str) -> float:
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
            if valor < 0:
                print("O preço não pode ser negativo.")
                continue
            return valor
        except ValueError:
            print("Digite um preço válido, por exemplo 12,50.")


def cadastrar_produto(estoque: dict[str, dict[str, str | int | float]]) -> bool:
    codigo = input("Código do produto: ").strip().upper()
    if not codigo:
        print("O código não pode ficar vazio.")
        return False
    if codigo in estoque:
        print("Já existe um produto com esse código.")
        return False

    nome = input("Nome do produto: ").strip()
    if not nome:
        print("O nome não pode ficar vazio.")
        return False

    quantidade = ler_inteiro_nao_negativo("Quantidade inicial: ")
    preco = ler_preco("Preço unitário: R$ ")
    estoque[codigo] = {"nome": nome, "quantidade": quantidade, "preco": preco}
    print("Produto cadastrado.")
    return True


def listar_produtos(estoque: dict[str, dict[str, str | int | float]]) -> None:
    if not estoque:
        print("O estoque está vazio.")
        return

    print("\n--- Estoque ---")
    for codigo, produto in sorted(estoque.items()):
        print(
            f"{codigo} | {produto['nome']} | "
            f"Quantidade: {produto['quantidade']} | "
            f"Preço: R$ {produto['preco']:.2f}"
        )


def buscar_produtos(estoque: dict[str, dict[str, str | int | float]]) -> None:
    termo = input("Digite o código ou nome do produto: ").strip().casefold()
    encontrados = [
        (codigo, produto)
        for codigo, produto in estoque.items()
        if termo in codigo.casefold() or termo in str(produto["nome"]).casefold()
    ]

    if not encontrados:
        print("Nenhum produto encontrado.")
        return

    for codigo, produto in encontrados:
        print(
            f"{codigo} | {produto['nome']} | "
            f"Quantidade: {produto['quantidade']} | "
            f"Preço: R$ {produto['preco']:.2f}"
        )


def movimentar_estoque(
    estoque: dict[str, dict[str, str | int | float]],
) -> bool:
    codigo = input("Código do produto: ").strip().upper()
    if codigo not in estoque:
        print("Produto não encontrado.")
        return False

    operacao = input("Digite E para entrada ou S para saída: ").strip().upper()
    if operacao not in {"E", "S"}:
        print("Operação inválida.")
        return False

    quantidade = ler_inteiro_nao_negativo("Quantidade a movimentar: ")
    if quantidade == 0:
        print("A quantidade deve ser maior que zero.")
        return False

    atual = int(estoque[codigo]["quantidade"])
    if operacao == "S" and quantidade > atual:
        print(f"Estoque insuficiente. Quantidade disponível: {atual}.")
        return False

    estoque[codigo]["quantidade"] = (
        atual + quantidade if operacao == "E" else atual - quantidade
    )
    print("Estoque atualizado.")
    return True


def remover_produto(estoque: dict[str, dict[str, str | int | float]]) -> bool:
    codigo = input("Código do produto a remover: ").strip().upper()
    if codigo not in estoque:
        print("Produto não encontrado.")
        return False

    confirmacao = input(f"Remover {estoque[codigo]['nome']}? (s/n): ").strip().lower()
    if confirmacao != "s":
        print("Remoção cancelada.")
        return False

    del estoque[codigo]
    print("Produto removido.")
    return True


def main() -> None:
    from interface import main as iniciar_interface

    iniciar_interface()


if __name__ == "__main__":
    main()