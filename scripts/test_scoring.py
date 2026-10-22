"""Hand-checked tests for the independent scoring used in the report."""
import unittest
from analyze_results import independent_scores

def board(rows):
    return 'Current Board:\n'+'\n'.join(rows)+'\n\nUnfilled:\n'

class ScoringTests(unittest.TestCase):
    def test_perfect_board(self):
        self.assertEqual(independent_scores(board(['ABCDE','FGHIJ','KLMNO','PQRST','UVWXY']),list('ABCDEFGHIJKLMNOPQRSTUVWXY')),(1.0,1.0,1))

    def test_one_wrong_letter_breaks_two_words(self):
        self.assertEqual(independent_scores(board(['ZBCDE','FGHIJ','KLMNO','PQRST','UVWXY']),list('ABCDEFGHIJKLMNOPQRSTUVWXY')),(0.8,0.96,0))

    def test_blank_board(self):
        self.assertEqual(independent_scores(board(['_____']*5),list('ABCDEFGHIJKLMNOPQRSTUVWXY')),(0.0,0.0,0))

    def test_malformed_grid_fails(self):
        with self.assertRaises(ValueError):
            independent_scores('Current Board:\nABC\n',list('ABCDEFGHIJKLMNOPQRSTUVWXY'))

if __name__=='__main__':
    unittest.main()
