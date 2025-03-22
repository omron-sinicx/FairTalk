import cv2


def check_camera_connection():
    """ffmpeg を使わずに、カメラの番号とサイズを取得する。
    """
    true_camera_is = []  # 空の配列を用意
    for camera_number in range(0, 5):
        cap = cv2.VideoCapture(camera_number)
        ret, frame = cap.read()

        if ret is True:
            true_camera_is.append(camera_number)
            print(f"camera number {camera_number} of size {frame.shape} found. ")


def get_camera_devices_using_ffmpeg():
    """ffmpeg を使って、カメラの名前（Friendly Name）を取得する。
    参考: https://zenn.dev/4050sktrmt/articles/6f0998c6ba5436

    下記の形式で出力される：
     [0] FaceTime HD Camera
     [1] OBS Virtual Camera
     [2] Snap Camera
    """
    import ffmpeg
    import re

    # エラー内容を ffmpeg_output に代入。ffmpeg.input() の実行結果は常にエラー。
    try:
        ffmpeg_output = ffmpeg.input('dummy', format='avfoundation', list_devices='true').output('dummy').run(capture_stderr=True).decode('utf8')
    except ffmpeg.Error as e: 
        ffmpeg_output = e.stderr.decode('utf8')

    # ffmpegのエラー内容から、カメラデバイス名を抽出。
    regex_specified_range = "AVFoundation video devices:.*?Capture screen 0"
    regex_target_to_remove = "\[AVFoundation indev @.*?\]"
    extracted_lists = re.findall(regex_specified_range, re.sub(regex_target_to_remove, "", ffmpeg_output), flags=re.DOTALL)
    camera_list = [s for s in extracted_lists[0].split('\n') if ("AVFoundation video devices:" not in s) and ("Capture screen 0" not in s)]

    # カメラデバイスの一覧を出力。
    for camera in camera_list:
        print(camera)
    
    return camera_list


def get_audio_devices_using_ffmpeg():
    """ffmpeg を使って、オーディオデバイスの名前（Friendly Name）を取得する。
    参考: https://zenn.dev/4050sktrmt/articles/6f0998c6ba5436

    下記の形式で出力される：
      [0] BlackHole 2ch
      [1] MacBook Proのマイク
      [2] HD Pro Webcam C920
      [3] Microsoft Teams Audio
      [4] ZoomAudioDevice
    """
    import ffmpeg
    import re

    # エラー内容を ffmpeg_output に代入。ffmpeg.input() の実行結果は常にエラー。
    try:
        ffmpeg_output = ffmpeg.input('dummy', format='avfoundation', list_devices='true').output('dummy').run(capture_stderr=True).decode('utf8')
    except ffmpeg.Error as e: 
        ffmpeg_output = e.stderr.decode('utf8')

    # ffmpegのエラー内容から、カメラデバイス名を抽出。
    regex_specified_range = "AVFoundation audio devices:.*?error"
    regex_target_to_remove = "\[AVFoundation indev @.*?\]"
    extracted_lists = re.findall(regex_specified_range, re.sub(regex_target_to_remove, "", ffmpeg_output), flags=re.DOTALL)
    audio_list = [s for s in extracted_lists[0].split('\n') if ("AVFoundation audio devices:" not in s) and ("error" not in s)]

    # カメラデバイスの一覧を出力。
    for audio in audio_list:
        print(audio)
    
    return audio_list


if __name__ == '__main__':    
    print("Camera Devices:")
    get_camera_devices_using_ffmpeg()
    
    print("Audio Devices:")
    get_audio_devices_using_ffmpeg()
    
    # OpenCV で使う時の、カメラの画像サイズを知りたいときは、次の 1 行をコメントアウトする。
    # check_camera_connection()
    