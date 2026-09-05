import unittest
from decimal import Decimal
from game import roulette_double_zero as r
class T(unittest.TestCase):
 def ret(self,w,n):return r.payout(w,Decimal("100"),{"number":n})
 def test_pockets(self):self.assertEqual(len(r.POCKETS),38)
 def test_zeroes(self):self.assertEqual(self.ret("straight_0",0),Decimal("3600"));self.assertEqual(self.ret("straight_00","00"),Decimal("3600"))
 def test_zero_split(self):self.assertEqual(self.ret("split_0_00",0),Decimal("1800"));self.assertEqual(self.ret("split_0_00","00"),Decimal("1800"))
 def test_invalid(self):self.assertFalse(r.validate_wager("split_00_36"))
if __name__=="__main__":unittest.main()
