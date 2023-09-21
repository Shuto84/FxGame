from flask import Flask, render_template, request, redirect, url_for, session
import os
import random
import math
import numpy as np
import pandas as pd
from keras.models import Sequential, load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from predict import Predictor
from calculation import calculate_ai_action, calculate_profit_or_loss
from flask_sqlalchemy import SQLAlchemy
from model import db, Game, PlayerRanking, AIRanking
app = Flask(__name__)

app.secret_key = 'your_secret_key'  # セッション調整
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'  # SQLiteを使用
db.init_app(app)
with app.app_context():
    db.create_all()  # 例として、ここでデータベースを初期化します

predictor = Predictor(model_path="best_model.h5")#Aiによる値段予測
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
GAME_COUNT_KEY = "game_count"
@app.route('/')
def home():
    session.clear()
    # データベースのGameテーブルの内容を全て削除
    Game.query.delete()
    db.session.commit()
    return render_template('home.html')  # ホーム画面を表示

@app.route('/play', methods=['GET', 'POST'])
def play(): 
    if request.method == 'GET':

        # 初回のプレイ時のみ、playerとaiの資金を初期化
        latest_game = Game.query.order_by(Game.id.desc()).first()
        session['player_money'] = latest_game.player_money if latest_game else 1000
        session['ai_money'] = latest_game.ai_money if latest_game else 1000
        chart_name = random.choice([name for name in os.listdir("./static/chartdata") if "correct" not in name and name.endswith(".png")])
        session['chart_name'] = chart_name.replace(".png", "")
        session['data_name'] = chart_name.replace("chart", "data").replace(".png", "")
        data = pd.read_csv(f"./static/chartdata/{session['data_name']}.csv")
        last_open_value = data.iloc[-1]['open']
        session['max_lot'] = session['player_money'] * 500 // last_open_value  # レバレッジ500倍値段（単位1万）
        session['max_lot_AI'] = session['ai_money'] * 500 // last_open_value
        return render_template('play.html', player_money=session['player_money'], ai_money=session['ai_money'], chart_name=session['chart_name'],data_name=session['data_name'], max_lot=session['max_lot'])

    elif request.method == 'POST':
        # プレイヤーのアクション
        session['player_action'] = request.form.get('action')
        session['player_lot'] = float(request.form.get('bet_amount'))
        data = pd.read_csv(f"./static/chartdata/{session['data_name']}.csv")
        correct_data = pd.read_csv(f"./static/chartdata/{session['data_name']}_correct.csv")
        #ゲーム回数をカウント
        if GAME_COUNT_KEY not in session:
            session[GAME_COUNT_KEY] = 1
        else:
         session[GAME_COUNT_KEY] += 1
        # AIの予測ロジックの実行
        predicted_rate = predictor.predict(f"./static/chartdata/{session['data_name']}.csv")
        ai_action = calculate_ai_action(predicted_rate, f"./static/chartdata/{session['data_name']}.csv")
        session['ai_action'] = ai_action
        session['ai_lot'] = math.floor(session['max_lot_AI'] * 0.1)
        #計算結果を保持
        session['last_open_value'] = data.iloc[-1]['open']
        session['correct_open_value']= correct_data.iloc[-1]['open']
        session['before_player_money'] = session['player_money']
        session['before_ai_money'] = session['ai_money']   
        session['player_money'] += calculate_profit_or_loss(session.get('player_action'), session['last_open_value'], session['correct_open_value'], session.get('player_lot', 1))
        session['ai_money'] += calculate_profit_or_loss(session.get('ai_action'), session['last_open_value'], session['correct_open_value'], session.get('ai_lot', 0.2))
        game = Game(player_money=session['player_money'], ai_money=session['ai_money'])
        db.session.add(game)
        db.session.commit()
        if (session['player_money'] <6) or (session['ai_money']) <6:
            return redirect(url_for('final_results'))
        elif session[GAME_COUNT_KEY] >= 5:
            return redirect(url_for('final_results'))
        else:   
            return redirect(url_for('results'))

   
@app.route('/results')
def results():
    #結果を表示
    return render_template('results.html', 
                        player_money=session['player_money'], 
                        ai_money=session['ai_money'], 
                        count = session[GAME_COUNT_KEY],
                        last_open_value=session['last_open_value'],
                        correct_open_value=session['correct_open_value'],
                        before_player_money=session['before_player_money'],
                        before_ai_money=session['before_ai_money'],
                        chart_name_correct=f"{session['chart_name']}_correct",
                        data_name_correct=f"{session['data_name']}_correct")

@app.route('/final_results', methods=['GET', 'POST'])
def final_results():
    #最終結果を表示
    if request.method == 'GET':
        if session['player_money'] > session['ai_money']:
            result = "WIN!!!"
        elif session['player_money'] < session['ai_money']:
            result = "LOSE..."
        else:
            result = "DRAW"
        
        return render_template('final_results.html', 
                            player_money=session['player_money'], 
                            ai_money=session['ai_money'], 
                            result=result, 
                            last_open_value=session['last_open_value'],
                            correct_open_value=session['correct_open_value'],
                            before_player_money=session['before_player_money'],
                            before_ai_money=session['before_ai_money'],
                            chart_name_correct=f"{session['chart_name']}_correct",
                            data_name_correct=f"{session['data_name']}_correct")
    
    if request.method == 'POST':
        name = request.form.get('player_name')
        if session['player_money'] > session['ai_money']:
            result = "WIN!!!"
        elif session['player_money'] < session['ai_money']:
            result = "LOSE..."
        else:
            result = "DRAW"
        # 重複の確認: PlayerRanking
        existing_player = PlayerRanking.query.filter_by(name=name, money=session['player_money']).first()
        if not existing_player:
            player_ranking = PlayerRanking(name=name, money=session['player_money'])
            db.session.add(player_ranking)
            
        # 重複の確認: AIRanking
        existing_ai = AIRanking.query.filter_by(money=session['ai_money']).first()
        if not existing_ai:
            ai_ranking = AIRanking(money=session['ai_money'])
            db.session.add(ai_ranking)
        db.session.commit()
        return render_template('final_results.html', 
                            player_money=session['player_money'], 
                            ai_money=session['ai_money'], 
                            result=result, 
                            last_open_value=session['last_open_value'],
                            correct_open_value=session['correct_open_value'],
                            before_player_money=session['before_player_money'],
                            before_ai_money=session['before_ai_money'],
                            chart_name_correct=f"{session['chart_name']}_correct",
                            data_name_correct=f"{session['data_name']}_correct")
            


    
@app.route('/rankings')
def rankings():
    player_rankings = PlayerRanking.query.order_by(PlayerRanking.money.desc()).all()
    ai_rankings = AIRanking.query.order_by(AIRanking.money.desc()).all()
    return render_template('rankings.html', player_rankings=player_rankings, ai_rankings=ai_rankings)

if __name__ == "__main__":

    app.run(debug=True)