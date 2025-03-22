import cv2
import pyvirtualcam
import numpy as np
import sys
import pandas as pd
import threading
import socket
import time
import yaml
import pyaudio
import csv

import onnx
import onnxruntime as ort
from google.protobuf.json_format import MessageToDict

from scaling import Scaling
from get_device_number_and_name import get_camera_devices_using_ffmpeg


def monitor_audio_level(audio_threshold: float) -> None:
    """喋っているかどうかを、リアルタイムに音量をモニタリングしながら調べる。喋っている間はエフェクトがかからないようにするため。

    Args:
        audio_threshold (float): この値以上のdBだったら、喋っているとみなす。
    """
    chunk = 1024 * 5
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    # この時間以上の沈黙が現れたら、話し終わったことにする
    silence_interval = 3
    
    # 話し終わった時刻を記録する
    end_of_speaking_time = time.time()
    
    # 話している途中の短い沈黙であるかどうかを記録する
    is_interval = False

    # 音の取込開始
    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT,
        channels = CHANNELS,
        rate = RATE,
        input = True,
        frames_per_buffer = chunk
    )
    
    while True:
        # continue
        # 音データを取得して ndarray に変換
        data = stream.read(chunk)
        x = np.frombuffer(data, dtype="int16")

        if x.max() > audio_threshold:
            scaling.is_speaking = True
            is_interval = False
        else:
            if scaling.is_speaking == True:
                if not is_interval:
                    # 音アリから沈黙に切り替わった瞬間に、時刻を記録する。
                    end_of_speaking_time = time.time()
                    is_interval = True
                elif time.time() - end_of_speaking_time > silence_interval:
                    # 沈黙中、ただし沈黙し始めてから silence_interval 秒経った。
                    is_interval = False
                    scaling.is_speaking = False

    stream.close()
    p.terminate()


def socket_listen(IP: str, port: int, model_path: str, threshold: float, enable_visualization: bool) -> None:
    """ソケット通信で OpenFace の FeatureExtraction から Action Unit を受け取り、その値から推論した結果を元にエフェクトを加える。

    Args:
        IP (str): ソケット通信の IP アドレス
        port (int): ソケット通信のポート
        model_path (str): AU から発話意図を推定する onnx モデルへのパス
        threshold (float): モデルの閾値
        enable_visualization (bool): コンソールで発話意図の推定結果を可視化するかどうか
    """
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((IP, port))  # IPとポート番号を指定する
    except OSError as e:
        print("しばらく時間を空けてから試すか、プロセスをキルしてから再度実行してください。")
        print(e)

    s.listen(5)

    clientsocket, address = s.accept()
    print(f"Connection from {address} has been established!")

    # ONNX モデルをロードする
    model = onnx.load(model_path)

    # ONNX モデルが正しい形式になっているかチェックしてからセッション開始
    onnx.checker.check_model(model)
    ort_session = ort.InferenceSession(model_path)
    
    # model.graph.input が RepeatedCompositeContainer なので、最初の要素の shape を見る。
    # 参考：https://stackoverflow.com/a/68617172
    input_shapes = [d.dim_value for d in model.graph.input[0].type.tensor_type.shape.dim]
    lstm_length = input_shapes[1]
    num_of_aus = input_shapes[2]

    # 過去 `lstm_length`` (例：25) フレーム分の AU `num_of_aus`（例：17）種類を入れる配列。最初は全てゼロで初期化。
    previous_aus = np.zeros((lstm_length, num_of_aus), dtype=np.float32)

    # 前回のフレームを記録した時刻
    prev_frame_time = time.time()

    # start_recording = time.time()

    while True:
        rcvmsg = clientsocket.recv(10000)
        aus_string = rcvmsg.decode().split(",")
        aus_string.pop()
        aus = np.array([float(s) for s in aus_string])

        # 推論を 6 FPS にするため、1/6 秒ごとに値を読み取る。前回から 1/6 秒経ってないならスルーする。
        if time.time() - prev_frame_time < 1/6:
            continue
        else:
            prev_frame_time = time.time()
        
        # 説明：numpy.delete(入力配列, 削除する行番号や列番号, 削除対象となる軸=None)
        # 参考：https://note.nkmk.me/python-numpy-delete/
        dequeued_aus = np.delete(previous_aus, 0, 0)

        # 説明：numpy.insert(元のNumPy配列, 挿入する位置, 挿入する要素・行・列の値, 挿入する軸)
        # 参考：https://note.nkmk.me/python-numpy-insert/
        try:
            previous_aus = np.insert(dequeued_aus, lstm_length-1, aus, axis=0)
        except ValueError as ve:
            print(ve)
            print("OpenFace にエラーが出ている可能性があります。もう一度実行しなおしてください。")
            break

        # モデルに適した形に整えてから推論へ
        previous_aus_reshaped = previous_aus.reshape(1, lstm_length, num_of_aus)
        try:
            outputs = ort_session.run(
                None,
                {"input": previous_aus_reshaped},
            )
        except Exception as e:
            print(f"モデルに入力する配列のサイズが合っていない可能性があります。")
            print(f"lstm_length (現在{lstm_length}) と num_of_aus (現在{num_of_aus})を見直してください。\n{e}")

        # 発話意図の推論結果をコンソールで可視化する
        if enable_visualization:
            results_black_char = ""
            for _ in range(max(1, int(outputs[0][0][0]))):
                results_black_char += "█"
            print(str(int(outputs[0][0][0])).rjust(4) + results_black_char)
        
        if outputs[0][0][0] > threshold and not scaling.is_scaling and not scaling.is_speaking:
            scaling.restart()

        if rcvmsg == '':
            break

    clientsocket.close()


def create_y_from_df(df: pd.DataFrame, duration: float=5, fps: float=60, reversed_end_effect: bool=True, zoom_out_duration: float=5.0) -> pd.DataFrame:
    """dataframe を入力として、仮想カメラのfpsに合わせた変位のリストを返す。

    Args:
        df (pd.DataFrame): 録画データから記録した値が入った dataframe。
        duration (float, optional): エフェクト全体の長さを秒で指定。 Defaults to 5.
        fps (float, optional): 仮想カメラのfps。 Defaults to 60.
        reversed_end_effect (bool, optional): 拡大エフェクトの後、それを逆再生することで元の倍率に戻るようにするかどうか。 Defaults to True.
        zoom_out_duration (float, optional): エフェクトが終わった後、元の倍率に戻るまでの秒数。Defaults to 5.
    """

    # デバッグのために dataframe を print するとき、行を省略せずに出力する。
    # 参考：https://it-ojisan.tokyo/pandas-display-max_rows/
    pd.set_option('display.max_rows', None)
    
    # 空の dataframe を作成して、値のある場所だけ入れていく。
    new_df = pd.DataFrame(index=range(int(duration * fps)), columns=df.columns, dtype='float64')
    for i in range(len(df)):
        new_df.loc[int(i * fps / df.attrs['fps'])] = df.loc[i]
    
    if reversed_end_effect:
        # 補間の参考：https://note.nkmk.me/python-pandas-interpolate/
        new_df = new_df.interpolate()
        
        # 拡大エフェクトの逆再生。new_df の列を逆順にした zoom_out_df を作成して、new_df の末尾に追加する。
        # dataframe の結合の参考：https://note.nkmk.me/python-pandas-concat/
        zoom_out_df = new_df.iloc[::-1]
        new_df = pd.concat([new_df, zoom_out_df])
        
    else:
        # reversed_end_effect が False のときは、zoom_out_duration 秒かけて、ゆっくり元の倍率に戻るようにする。
        # 空の dataframe を作成して、値のある場所だけ入れていく。
        new_df = pd.DataFrame(index=range(int(duration * fps + zoom_out_duration * fps)), columns=df.columns, dtype='float64')
        for i in range(len(df)):
            new_df.loc[int(i * fps / df.attrs['fps'])] = df.loc[i]
        
        # 末尾に初期状態を設定する。次の補間で滑らかに繋いでくれる。
        new_df.at[-1, 'x_33'] = 0.0
        new_df.at[-1, 'y_33'] = 0.0
        new_df.at[-1, 'Z_33'] = 1.0
        
        # 補間の参考：https://note.nkmk.me/python-pandas-interpolate/
        new_df = new_df.interpolate()

    return new_df


def camera_loop(cam_number: int, fps: float, enable_nodding: bool, nodding_path: str, enable_frame: bool, frame_effect_thickness: int, frame_effect_duration: float, default_magnification: float) -> None:
    """仮想カメラを開始する。OBSに配信される。

    Args:
        cam_number (int): カメラのデバイス番号。使用可能なデバイス番号は `python list_available_cameras.py` で調べられる。
        fps (float): 仮想カメラの FPS。デフォルトは 60。
        enable_nodding (bool): うなづきエフェクトにするかどうか。true にすると拡大エフェクトは無くなる。
        nodding_path (str): うなづき動画へのパス。
        enable_frame (bool): 閾値を超えたときにフレームをつけるかどうか。
        frame_effect_thickness (int): フレームエフェクトの、フレーム幅をピクセル単位で指定。
        frame_effect_duration (float): フレームエフェクトの持続時間を秒数で指定。
        default_magnification (float): 画角の拡大率のデフォルト値。基本は1。
    """
    
    # 取得するデータソース（Webカメラ）を選択
    cap = cv2.VideoCapture(cam_number)
    
    if enable_nodding:
        cap_nodding = cv2.VideoCapture(nodding_path)

    # webカメラの映像ではなく、事前に録画したものにエフェクトを加えたいときは、次の一行を使う。
    # cap = cv2.VideoCapture('path_to_vide_file.mp4')

    _, frame = cap.read()

    frame_effect_count_max = frame_effect_duration * fps
    frame_effect_count = frame_effect_count_max

    with pyvirtualcam.Camera(width=frame.shape[1], height=frame.shape[0], fps=fps) as cam:
        print(f"Virtual camera activated! (fps: {fps})")

        while True:
            _, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if enable_nodding:
                if scaling.is_scaling:
                    ret, nod_frame = cap_nodding.read()
                    if ret:
                        nod_frame = cv2.cvtColor(nod_frame, cv2.COLOR_BGR2RGB)
                        frame = nod_frame
                    else:
                        scaling.is_scaling = False
            
            if enable_frame:
                if scaling.is_scaling:
                    if frame_effect_count >= 0:
                        h, w, ch = frame.shape
                        cv2.rectangle(frame, (0, 0), (w, h), (255, 200, 0), thickness=frame_effect_thickness)
                        frame_effect_count -= 1
                    else:
                        frame_effect_count = frame_effect_count_max
                        scaling.is_scaling = False
            
            else:
                h, w, ch = frame.shape

                # 倍率と平行移動の値を計算
                (magnification, dx, dy) = scaling.update_effect()
                
                # デフォルトの拡大率をかける
                magnification *= default_magnification
                
                # 画面が普通より小さくならないようにする
                magnification = max(magnification, 1)

                # アフィン変換の拡大は、右上を固定して左下に伸ばす形で行われるので、中央に向かって拡大するように移動させる。
                x_move = w * (magnification - 1) / 2 + dx * magnification
                y_move = h * (magnification - 1) / 2 + dy * magnification
                
                # 余白ができないようにする
                y_move = min(y_move, h * (magnification - 1))
                y_move = max(y_move, 0)
                x_move = min(x_move, w * (magnification - 1))
                x_move = max(x_move, 0)

                # フレームに対して拡大・移動のアフィン変換
                m = np.float32([[magnification, 0, -x_move], [0, magnification, -y_move]])
                frame = cv2.warpAffine(frame, m, (w, h))

            # 画像を仮想カメラに流す
            cam.send(frame)
            cam.sleep_until_next_frame()

    # 終了処理
    cap.release()


if __name__ == '__main__':

    with open('config.yml', 'r') as yml:
        config = yaml.safe_load(yml)

    try:
        cam_number = int(config['virtual_camera']['camera_num'])
    except ValueError as e:
        print(f"config.ymlのcamera_numは-1以上の整数で入力してください。\n{e}\n自動でカメラ番号の抽出を試みます。")
        cam_number = -1

    # config.yml の camera_num が -1 だった場合、または不正な値だった場合、FaceTime HD Camera を探す。
    if cam_number == -1:
        available_camera_list = get_camera_devices_using_ffmpeg()
        for available_camera in available_camera_list:
            # available_camera の例：" [0] FaceTime HD Camera"
            if "FaceTime" in available_camera:
                try:
                    cam_number = int(available_camera[2])
                except ValueError as e:
                    print(f"自動でカメラ番号を取得できませんでした。\nconfig.ymlでcamera_numを手動で設定してください。\n{e}")
                    cam_number = 0

    print(f"Camera device number is set to {cam_number}\n")

    # to_pickle() で保存した pickle ファイルを読み込む。
    # 参考：https://note.nkmk.me/python-pandas-to-pickle-read-pickle/
    df_read_list = [pd.read_pickle(df_pickle) for df_pickle in config['effect']['path_to_df']]
    
    # エフェクトの倍率の時間変化を格納した dataframe を作成する。
    enable_loop = config['effect']['enable_effect_loop']
    duration = config['effect']['effect_duration']
    fps = config['virtual_camera']['fps']
    zoom_out_duration = config['effect']['zoom_out_duration']
    reversed_end_effect = config['effect']['reversed_end_effect']
    threshold = config['model']['threshold'] if not enable_loop else -float('inf')
    
    df_list = []
    duration_list = []
    
    for df_read in df_read_list:
        duration = float(len(df_read) / df_read.attrs['fps'])
        df = create_y_from_df(
            df_read,
            duration = duration,
            fps = fps,
            reversed_end_effect = reversed_end_effect,
            zoom_out_duration = zoom_out_duration
            )

        df_list.append(df)
        
        if reversed_end_effect:
            duration *= 2
        else:
            duration += zoom_out_duration

        duration_list.append(duration)
    
    try:
        scaling = Scaling(df_list=df_list, duration_list=duration_list, fps=fps)
    except FileNotFoundError as e:
        print(f"config.yml に指定した `path_to_df` が見つかりませんでした。パスを確認してください。\n{e}")

    is_nod_starting = False
    
    # コマンドライン引数で、cオプションを与えられたら
    if '-c' in sys.argv:
        index = sys.argv.index('-c')
        try:
            condition_number = int(sys.argv[index + 1])
        except (ValueError, IndexError):
            print('Error: invalid argument for -c option')
        else:
            print(f'The value of -c option is {condition_number}')
    else:
        print('Error: -c option is not specified')

    enable_frame = config['effect']['enable_frame_effect']
    if condition_number == 1:
        threshold = float('inf')
    elif condition_number == 2:
        enable_frame = False
    elif condition_number == 3:
        enable_frame = True

    t1 = threading.Thread(target = socket_listen,
                          args = (
                              config['socket_connection']['IP'],              # IP
                              config['socket_connection']['port'],            # port
                              config['model']['path_to_onnx_model'],          # model_path
                              threshold,                                      # threshold
                              config['debug_tools']['console_visualization']  # enable_visualization
                              )
                          )
    t2 = threading.Thread(target = camera_loop,
                          args = (
                              cam_number,
                              fps,
                              config['effect']['enable_nodding_effect'],
                              config['effect']['path_to_nodding_video'],
                              enable_frame,
                              config['effect']['frame_effect_thickness'],
                              config['effect']['frame_effect_duration'],
                              config['virtual_camera']['default_magnification'],
                              )
                          )
    t3 = threading.Thread(target = monitor_audio_level,
                          args = (
                              config['audio']['audio_threshold'],
                          )
                          )
    t1.start()
    t2.start()
    t3.start()
