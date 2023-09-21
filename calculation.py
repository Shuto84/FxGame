# calculation.py
import math
import pandas as pd
def calculate_ai_action(predicted_rate, last_file_path):
    last_data = pd.read_csv(last_file_path)
    last_open_value = last_data.iloc[-1]['open']

    if predicted_rate > last_open_value:
        return "buy"
    else:
        return "sell"

def calculate_profit_or_loss(action, last_open_value, correct_open_value, lot):
    profit_or_loss = correct_open_value - last_open_value  # 1円の変動で1万円の利益/損失

    if action == "buy":
        return math.floor(profit_or_loss * lot)
    elif action == "sell":
        return math.floor(-profit_or_loss * lot)
    else:
        return 0  # hold の場合