from math import *
import numpy as np
import time
import random


class Easing:
    def __init__(self, x_start=1.0, x_end=1.5, duration_list=[5.0], fps=30, custom_filename="", custom_y_list=[]) -> None:
        """顔の拡大縮小・移動などの時間変化を管理するEasingクラス。xは拡大率・移動の大きさなどの変位を表す。

        Args:
            x_start (float, optional): 最初の状態でのxの値。 Defaults to 1.0.
            x_end (float, optional): 最後の状態でのxの値。 Defaults to 1.5.
            duration (list, optional): 何秒間でx_startからx_endまで変化させたいか。 Defaults to [5.0].
            fps (int, optional): 1秒に何フレームか。 Defaults to 30.
            custom_filename (str, optional): 自分で記録した時間変化のファイルへのパス。 Defaults to "".
            custom_y_list (list, optional): 自分で記録した時間変化のリストを直接渡すのに使う。 Defaults to [].
        """
        self.x_start = x_start
        self.x_end = x_end
        self.duration_list = duration_list
        self.fps = fps
        self.elapsed = 0
        self.x = x_start

        # easing を開始した時点。`time.time() - self.start_time` で経過時間(s)が求まる
        self.start_time = time.time()

        # easing が進行中かどうかを管理する。
        self.is_easing = False

        # ファイル名が指定された場合は、そのファイルに記録された時間変化を用いる。
        if custom_filename != "":
            self.y = np.load(custom_filename)
        elif custom_y_list != []:
            # config.yml で指定された path_to_df のエフェクトからランダムに1つ選ぶ。
            self.custom_y_list = custom_y_list
            
            # randint(a, b) は a <= n <= b のランダムな整数 n を返す。
            random_index = random.randint(0, len(self.custom_y_list) - 1)    
            self.y = self.custom_y_list[random_index]
            self.duration = self.duration_list[random_index]
        else:
            self.y = None

    def restart(self):
        """開始時間 `start_time` を現在の時刻に設定して、y を設定（ランダムに選ぶ）。
        """
        # randint(a, b) は a <= n <= b のランダムな整数 n を返す。
        random_index = random.randint(0, len(self.custom_y_list) - 1)
        print(random_index)
        self.y = self.custom_y_list[random_index]
        self.duration = self.duration_list[random_index]
        
        self.start_time = time.time()

    def stop(self):
        """現在の変位 `x` を、変化し始める最初の状態 `x_start` に設定する。
        """
        self.x = self.x_start
    
    def customized_easing(self):
        if not self.is_easing:
            return self.x_start
        if self.y is None:
            print("Easing クラスの引数 `custom_filename` と `custom_y` のどちらかが指定されていません。\n`custom_filename` または `custom_y` を指定するか、`customized_easing()` の代わりに別のイージング関数（例：`ease_in_linear()`）を呼び出してください。")
            self.y = [1 for _ in range(int(self.fps * self.duration))]
        self.elapsed = time.time() - self.start_time
        if self.elapsed >= self.duration:
            self.is_easing = False
        #     self.restart() if self.enable_loop else self.stop()
        #     return self.x
        return self.y[min(len(self.y) - 1, int(self.elapsed * self.fps))]

    def deco_easing(func):
        def wrapper(self):
            self.elapsed = time.time() - self.start_time
            if self.elapsed >= self.duration:
                self.stop()
                # self.restart() if self.enable_loop else self.stop()
                return self.x
            self.x = self.elapsed / self.duration
            return self.x_start + func(self) * self.x_end
        return wrapper

    @deco_easing
    def ease_in_linear(self):
        return self.x

    @deco_easing
    def ease_in_sine(self):
        return 1 - cos((self.x * pi) / 2)

    @deco_easing
    def ease_out_sine(self):
        return sin((self.x * pi) / 2)

    @deco_easing
    def ease_in_out_sine(self):
        return -(cos(pi * self.x) - 1) / 2

    @deco_easing
    def ease_in_quad(self):
        return self.x * self.x

    @deco_easing
    def ease_out_quad(self):
        return 1 - (1 - self.x) * (1 - self.x)

    @deco_easing
    def ease_in_out_quad(self):
        return 2 * self.x * self.x if self.x < 0.5 else 1 - (-2 * self.x + 2) ** 2 / 2

    @deco_easing
    def ease_in_cubic(self):
        return self.x ** 3

    @deco_easing
    def ease_out_cubic(self):
        return 1 - (1 - self.x) ** 3

    @deco_easing
    def ease_in_out_cubic(self):
        return 4 * (self.x ** 3) if self.x < 0.5 else 1 - (-2 * self.x + 2) ** 3 / 2

    @deco_easing
    def ease_in_quart(self):
        return self.x ** 4

    @deco_easing
    def ease_out_quart(self):
        return 1 - (1 - self.x) ** 4

    @deco_easing
    def ease_in_out_quart(self):
        return 8 * (self.x ** 4) if self.x < 0.5 else 1 - (-2 * self.x + 2) ** 4 / 2

    @deco_easing
    def ease_in_quint(self):
        return self.x ** 5

    @deco_easing
    def ease_out_quint(self):
        return 1 - (1 - self.x) ** 5

    @deco_easing
    def ease_in_out_quint(self):
        return 16 * (self.x ** 5) if self.x < 0.5 else 1 - (-2 * self.x + 2) ** 5 / 2

    @deco_easing
    def ease_in_expo(self):
        return 0 if self.x == 0 else (2 ** (10 * self.x - 10))

    @deco_easing
    def ease_out_expo(self):
        return 1 if self.x == 1 else 1 - (2 ** (-10 * self.x))

    @deco_easing
    def ease_in_out_expo(self):
        if self.x == 0:
            return 0
        elif self.x == 1:
            return 1
        elif self.x < 0.5:
            return 2 ** (20 * self.x - 10) / 2
        else:
            return (2 - (2 ** (-20 * self.x + 10))) / 2

    @deco_easing
    def ease_in_circ(self):
        return 1 - sqrt(1 - self.x ** 2)

    @deco_easing
    def ease_out_circ(self):
        return sqrt(1 - (self.x - 1) ** 2)

    @deco_easing
    def ease_in_out_circ(self):
        if self.x < 0.5:
            return (1 - sqrt(1 - (2 * self.x) ** 2)) / 2
        else:
            return (sqrt(1 - (-2 * self.x + 2) ** 2) + 1) / 2

    @deco_easing
    def ease_in_back(self):
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * self.x ** 3 - c1 * self.x ** 2

    @deco_easing
    def ease_out_back(self):
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (self.x - 1) ** 3 + c1 * (self.x - 1) ** 2

    @deco_easing
    def ease_in_out_back(self):
        c1 = 1.70158
        c2 = c1 * 1.525
        if self.x < 0.5:
            return ((2 * self.x) ** 2 * ((c2 + 1) * 2 * self.x - c2)) / 2
        else:
            return ((2 * self.x - 2) ** 2 * ((c2 + 1) * (self.x * 2 - 2) + c2) + 2) / 2

    @deco_easing
    def ease_in_elastic(self):
        c4 = (2 * pi) / 3
        if self.x == 0:
            return 0
        elif self.x == 1:
            return 1
        else:
            return -(2 ** (10 * self.x - 10)) * sin((self.x * 10 - 10.75) * c4)

    @deco_easing
    def ease_out_elastic(self):
        c4 = (2 * pi) / 3
        if self.x == 0:
            return 0
        elif self.x == 1:
            return 1
        else:
            return 2 ** (-10 * self.x) * sin((self.x * 10 - 0.75) * c4) + 1

    @deco_easing
    def ease_in_out_elastic(self):
        c5 = (2 * pi) / 4.5
        if self.x == 0:
            return 0
        elif self.x == 1:
            return 1
        elif self.x < 0.5:
            return -(2 ** (20 * self.x - 10) * sin((20 * self.x - 11.125) * c5)) / 2
        else:
            return (2 ** (-20 * self.x + 10) * sin((20 * self.x - 11.125) * c5)) / 2 + 1

    @deco_easing
    def ease_in_bounce(self):
        return 1 - self.ease_out_bounce(1 - self.x)

    @deco_easing
    def ease_out_bounce(self):
        n1 = 7.5625
        d1 = 2.75
        if self.x < 1 / d1:
            return n1 * self.x * self.x
        elif self.x < 2 / d1:
            return n1 * (self.x - (1.5 / d1)) ** 2 + 0.75
        elif self.x < 2.5 / d1:
            return n1 * (self.x - (2.25 / d1)) ** 2 + 0.9375
        else:
            return n1 * (self.x - (2.625 / d1)) * self.x + 0.984375

    @deco_easing
    def ease_in_out_bounce(self):
        if self.x < 0.5:
            return (1 - self.ease_out_bounce(1 - 2 * self.x)) / 2
        else:
            return (1 + self.ease_out_bounce(2 * self.x - 1)) / 2
