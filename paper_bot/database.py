"""Persistência transacional; banco local dedicado à simulação."""
import json, sqlite3
from datetime import datetime, timezone

def timestamp(): return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=5)
        self.db.executescript('''CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY, time TEXT NOT NULL, symbol TEXT NOT NULL, side TEXT NOT NULL, price REAL NOT NULL, quantity REAL NOT NULL, fee REAL NOT NULL, pnl REAL, reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time TEXT NOT NULL, message TEXT NOT NULL);''')
    def load(self):
        row=self.db.execute('SELECT data FROM state WHERE id=1').fetchone()
        return json.loads(row[0]) if row else None
    def save(self,state,trade=None,event=None):
        with self.db:
            self.db.execute('INSERT INTO state(id,data) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',(json.dumps(state),))
            if trade: self.db.execute('INSERT INTO trades(time,symbol,side,price,quantity,fee,pnl,reason) VALUES(?,?,?,?,?,?,?,?)',trade)
            if event: self.db.execute('INSERT INTO events(time,message) VALUES(?,?)',(timestamp(),event))
    def summary(self):
        return self.db.execute("SELECT COUNT(*),COALESCE(SUM(pnl),0),COALESCE(SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END),0) FROM trades WHERE side='SELL'").fetchone()
