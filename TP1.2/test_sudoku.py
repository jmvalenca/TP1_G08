"""Cinco testes do Sudoku. Correr sem python -O."""

import unittest

from sudoku import box, make_sudoku, run_example, validate_solution


class SudokuTests(unittest.TestCase):
    def test_sudoku_4x4(self):
        pistas, solucao, _, _ = run_example(2, seed=2026)
        self.assertTrue(validate_solution(2, solucao, pistas))

    def test_sudoku_9x9(self):
        pistas, solucao, _, _ = run_example(3, seed=2027)
        self.assertTrue(validate_solution(3, solucao, pistas))

    def test_sudoku_16x16(self):
        pistas, solucao, _, _ = run_example(4, seed=2028)
        self.assertTrue(validate_solution(4, solucao, pistas))

    def test_sudoku_diagonal(self):
        principal = box(2)
        secundaria = box(2)
        for i in range(4):
            principal.add(i, i)
            secundaria.add(i, 3 - i)

        pistas = box(2)
        problema = make_sudoku(2, pistas, (principal, secundaria))
        solucao = problema.solve()
        self.assertTrue(validate_solution(2, solucao, pistas))
        self.assertEqual({solucao[i][i] for i in range(4)}, {1, 2, 3, 4})
        self.assertEqual({solucao[i][3-i] for i in range(4)}, {1, 2, 3, 4})

    def test_pistas_impossiveis(self):
        # duas pistas iguais na mesma linha
        pistas = box(2).add(0, 0, 1).add(0, 1, 1)
        problema = make_sudoku(2, pistas)
        self.assertIsNone(problema.solve())
        self.assertEqual(problema.status, "INFEASIBLE")


if __name__ == "__main__":
    unittest.main()
