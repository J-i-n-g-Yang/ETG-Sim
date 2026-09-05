import unittest
from decimal import Decimal
from game import roulette_sands_roulette as r
class T(unittest.TestCase):
 def ret(self,w,n):return r.payout(w,Decimal("100"),{"number":n})
 def test_pockets(self):self.assertEqual(len(r.POCKETS),39)
 def test_top_line(self):
  for n in ("S","00",0,1,2,3):self.assertEqual(self.ret("top_line",n),Decimal("600"))
 def test_green(self):
  for n in ("S","00",0):self.assertEqual(self.ret("green",n),Decimal("1200"))
 def test_special_splits(self):
  for w,n in [("split_S_0","S"),("split_S_00","00"),("split_00_0",0),("split_0_1",0),("split_00_3","00")]:self.assertEqual(self.ret(w,n),Decimal("1800"))
 def test_invalid(self):self.assertFalse(r.validate_wager("split_S_36"))
if __name__=="__main__":unittest.main()
