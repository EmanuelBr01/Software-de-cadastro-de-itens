import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import programa1


class Programa1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)
        self.base = Path(self.diretorio.name)
        self.patch_estoque = patch.object(
            programa1, "ARQUIVO_ESTOQUE", self.base / "estoque.json"
        )
        self.patch_historico = patch.object(
            programa1, "ARQUIVO_HISTORICO", self.base / "historico.json"
        )
        self.patch_estoque.start()
        self.patch_historico.start()
        self.addCleanup(self.patch_estoque.stop)
        self.addCleanup(self.patch_historico.stop)

    def test_saving_creates_a_backup_of_previous_inventory(self) -> None:
        primeiro = {"A1": {"nome": "Mouse", "quantidade": 2, "preco": 20.0}}
        segundo = {"A1": {"nome": "Mouse", "quantidade": 3, "preco": 20.0}}

        programa1.salvar_estoque(primeiro)
        programa1.salvar_estoque(segundo)

        backup = json.loads((self.base / "estoque.json.bak").read_text("utf-8"))
        self.assertEqual(backup, primeiro)
        self.assertEqual(programa1.carregar_estoque(), segundo)

    def test_loading_rejects_invalid_product_data(self) -> None:
        (self.base / "estoque.json").write_text(
            '{"A1": {"nome": "Mouse", "quantidade": -1, "preco": 20}}',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "quantidade"):
            programa1.carregar_estoque()

    def test_movement_is_saved_and_loaded_from_history(self) -> None:
        programa1.registrar_movimentacao("A1", "Mouse", "Entrada", 4)

        historico = programa1.carregar_historico()
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["codigo"], "A1")
        self.assertEqual(historico[0]["operacao"], "Entrada")
        self.assertEqual(historico[0]["quantidade"], 4)

    def test_programa1_entry_point_starts_the_gui(self) -> None:
        with patch("interface.main") as iniciar_interface:
            programa1.main()

        iniciar_interface.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
