import numpy as np
import pandas as pd
from keras.models import Sequential, load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

#予測結果のクラス
class Predictor:
    def __init__(self, model_path, time_steps=200, batch_size=20, feature_columns=None, output_index=0):
        self.model_path = model_path
        self.time_steps = time_steps
        self.batch_size = batch_size
        self.feature_columns = feature_columns if feature_columns is not None else ["open", "high", "low", "close", "Volume"]
        self.output_index = output_index

    def predict_next(self, input_csv):
        # モデルのロード
        model = load_model(self.model_path)

        # 入力データの読み込み
        df_input = pd.read_csv(input_csv, engine='python')
        df_predict = df_input[-self.time_steps:]

        # データの正規化
        min_max_scaler = MinMaxScaler()
        x_predict = min_max_scaler.fit_transform(df_predict.loc[:, self.feature_columns].values)

        # 予測
        y_pred = model.predict(np.tile(x_predict, (self.batch_size, 1, 1)), batch_size=None)
        y_pred = y_pred.flatten()

        # 正規化したデータを元に戻す
        y_pred_org = (y_pred * min_max_scaler.data_range_[self.output_index]) + min_max_scaler.data_min_[self.output_index]

        final_value = y_pred_org[0]
        print("PREDICTED VALUE: ", final_value)

        return final_value

    def predict(self, input_csv):
        return self.predict_next(input_csv)


# 別のコードでの使用例
if __name__ == "__main__":
    predictor = Predictor(model_path="best_model.h5")
    input_csv = "chartdata/data_175.csv"
    predictor.predict(input_csv)