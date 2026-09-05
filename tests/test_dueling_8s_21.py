import unittest
from decimal import Decimal
import game.dueling_8s_21 as d8

def C(r,s="H",permanent=False): return d8.card(r,s,permanent)
def P(): return d8.permanent_eight()

class TestDueling8s21(unittest.TestCase):
    def test_shoe(self):
        shoe=d8.make_shoe(3,False)
        self.assertEqual(len(shoe),144)
        self.assertFalse(any(c["rank"]=="10" for c in shoe))
        self.assertFalse(any(c.get("permanent") for c in shoe))

    def test_deck_range(self):
        with self.assertRaises(ValueError): d8.make_shoe(2)
        with self.assertRaises(ValueError): d8.make_shoe(9)

    def test_ace_and_soft(self):
        self.assertEqual(d8.hand_total([P(),C("A")]),19)
        self.assertTrue(d8.is_soft([P(),C("A")]))
        self.assertEqual(d8.hand_total([P(),C("A"),C("9")]),18)

    def test_dealer_rule(self):
        self.assertTrue(d8.dealer_should_hit([P(),C("8")]))
        self.assertFalse(d8.dealer_should_hit([P(),C("9")]))
        self.assertFalse(d8.dealer_should_hit([P(),C("A"),C("8")]))

    def test_surrender(self):
        h={"cards":[P(),C("6")],"stake":100,"acted":False}
        self.assertTrue(d8.can_surrender(h))
        self.assertEqual(d8.surrender_return(100),Decimal("50"))
        h["from_split"]=True
        self.assertFalse(d8.can_surrender(h))

    def test_split_only_eights_and_max_four(self):
        h={"cards":[P(),C("8")],"acted":False}
        self.assertTrue(d8.can_split(h,3))
        self.assertFalse(d8.can_split(h,4))
        self.assertFalse(d8.can_split({"cards":[P(),C("7")],"acted":False},1))

    def test_partial_double(self):
        self.assertTrue(d8.double_amount_valid(25,100,25))
        self.assertTrue(d8.double_amount_valid(100,100,25))
        self.assertFalse(d8.double_amount_valid(20,100,25))
        self.assertFalse(d8.double_amount_valid(101,100,25))

    def test_regular(self):
        dealer=[P(),C("9")]
        self.assertEqual(d8.regular_result([P(),C("K")],dealer),"win")
        self.assertEqual(d8.regular_result([P(),C("9")],dealer),"push")
        self.assertEqual(d8.regular_return(100,"win"),Decimal("200"))

    def test_678(self):
        mixed=[P(),C("6","H"),C("7","D")]
        spades=[P(),C("7","S"),C("6","S")]
        self.assertEqual(d8.six_seven_eight_bonus(100,mixed),Decimal("100"))
        self.assertEqual(d8.six_seven_eight_bonus(100,spades),Decimal("500"))
        self.assertEqual(d8.six_seven_eight_bonus(100,spades,True),Decimal("0"))

    def test_tie_18(self):
        p=[P(),C("K")]; d=[P(),C("K")]
        self.assertEqual(d8.tie_on_18_return(100,p,d),Decimal("900"))

    def test_superb_8s(self):
        self.assertEqual(d8.superb_eights_return(100,[P(),C("8")]),Decimal("400"))
        self.assertEqual(d8.superb_eights_return(100,[P(),C("8"),C("8")]),Decimal("900"))
        self.assertEqual(d8.superb_eights_return(100,[P(),C("8"),C("8"),C("8")]),Decimal("80100"))
        self.assertEqual(d8.superb_eights_return(100,[P(),C("8","S"),C("8","S"),C("8","S")]),Decimal("800100"))
        self.assertEqual(d8.superb_eights_result([P(),C("8"),C("7"),C("8")]),"two_eights")

    def test_21_plus_table(self):
        expected={3:2,4:3,5:8,6:35,7:80,8:800}
        for count,odds in expected.items():
            with self.subTest(count=count):
                dealer=[P()]+[C("K")]*(count-1)
                self.assertEqual(d8.twenty_one_plus_odds(dealer),Decimal(odds))
                self.assertEqual(d8.twenty_one_plus_return(100,dealer),Decimal(100)*(Decimal(1)+Decimal(odds)))

    def test_21_plus_loses_without_bust(self):
        self.assertEqual(d8.twenty_one_plus_return(100,[P(),C("9")]),Decimal("0"))

if __name__=="__main__":
    unittest.main()
