import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from paper_bot import risk, execution
from paper_bot.database import Store
import crypto_paper_bot as bot

class PaperTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(':memory:')
        self.addCleanup(self.store.db.close)
        self.state={'cash':100.0,'initial':100.0,'positions':{},'last_candles':{},'day':bot.today(),'day_start':100.0,'halted':False}
    def test_buy_sell_and_persistence(self):
        trade=execution.buy(self.state,'SOLUSDT',10,50); self.store.save(self.state,trade)
        self.assertAlmostEqual(self.state['cash'],50)
        self.assertAlmostEqual(self.state['positions']['SOLUSDT']['quantity'],4.995)
        trade=execution.sell(self.state,'SOLUSDT',11,'take-profit'); self.store.save(self.state,trade)
        self.assertAlmostEqual(trade[6],4.890055)
        self.assertEqual(self.store.summary()[0],1)
        self.assertAlmostEqual(self.store.load()['cash'],104.890055)
    def test_risk_controls(self):
        self.assertFalse(risk.entry_allowed(97,100,{},'SOLUSDT'))
        self.assertFalse(risk.entry_allowed(100,100,{'BTC':{},'ETH':{}},'SOLUSDT'))
        self.assertFalse(risk.entry_allowed(100,100,{'SOLUSDT':{}},'SOLUSDT'))
        self.assertEqual(risk.exit_reason(100,98.5,None),'stop-loss')
        self.assertEqual(risk.exit_reason(100,103,None),'take-profit')
    def test_stop_and_halt_persist(self):
        execution.buy(self.state,'SOLUSDT',100,50)
        with patch.object(bot.market,'price',return_value=(90,90.1)), patch.object(bot.market,'candles',side_effect=ValueError), patch.object(bot,'notify'):
            bot.cycle(self.store,self.state,[],True)
        self.assertTrue(self.state['halted'])
        self.assertFalse(self.state['positions'])
        self.assertTrue(self.store.load()['halted'])
        self.assertEqual(self.store.summary()[0],1)
    def test_missing_held_price_blocks_entry(self):
        execution.buy(self.state,'SOLUSDT',100,50)
        with patch.object(bot.market,'price',side_effect=OSError), patch.object(bot.market,'candles',side_effect=ValueError):
            bot.cycle(self.store,self.state,[],True)
        self.assertIn('SOLUSDT',self.state['positions'])

if __name__=='__main__': unittest.main()

