#データベース
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_money = db.Column(db.Float, nullable=False)
    ai_money = db.Column(db.Float, nullable=False)
    
class PlayerRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    money = db.Column(db.Float, nullable=False)

class AIRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    money = db.Column(db.Float, nullable=False)