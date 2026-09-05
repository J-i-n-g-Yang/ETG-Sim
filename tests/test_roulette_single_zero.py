import unittest
from decimal import Decimal
from game import roulette_single_zero as r
class T(unittest.TestCase):
 def ret(self,w,n):return r.payout(w,Decimal("100"),{"number":n})
 def test_pockets(self):self.assertEqual(len(r.POCKETS),37)
 def test_payouts(self):
  for w,n,x in [("straight_17",17,"3600"),("split_17_20",20,"1800"),("street_1_2_3",2,"1200"),("corner_1_2_4_5",4,"900"),("sixline_1_2_3_4_5_6",6,"600"),("dozen_1",12,"300"),("column_1",34,"300"),("red",1,"200")]:self.assertEqual(self.ret(w,n),Decimal(x))
 def test_validation(self):self.assertTrue(r.validate_wager("split_0_1"));self.assertFalse(r.validate_wager("split_1_36"));self.assertFalse(r.validate_wager("straight_00"))
if __name__=="__main__":unittest.main()
