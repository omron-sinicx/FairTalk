import time

class Timer(object):
    """
    時間計測のクラス
    example:
    t = Timer(label="タイマーのラベル", is_print=True)
    # チェックポイントを追加
    t.check("ラベル") # 短縮版 ->　t.c("ラベル")
    """

    class TimerObject(object):
        """
        時間計測のオブジェクト
        """

        def __init__(self, time_data: float, label: str, index: int) -> None:
            """
            :param time_data: その時間のtime秒、float型
            :param label:
            """
            self.time = time_data
            self.label = label
            self.pause_from = None
            self.pause_to = None
            self.pause_seconds = .0
            self.index = index

    def __init__(self, label: str = "T", is_print: bool = True) -> None:
        # チェックポイントのリスト。TimerObjectを格納
        self.__checkpoint = []
        # インスタンスのラベル
        self.__label = label
        # チェックポイント毎にprintするかどうか
        self.__is_print = is_print
        # 前回の処理を表示するかどうか
        self.__is_print_before = True
        # 通常のprint以外のprint関数の登録
        self.__print_func = None
        # 削除済みのオブジェクトに登録されていた秒数の合計（削除処理用）
        self.__removed_pause_time_seconds = .0
        # 最大オブジェクト数(マイナスの場合は上限なし）
        self.__max_object = 10
        # TimerObjectに割り当てるインデックス
        self.__abs_index = 0
        self.__checkpoint.append(self.TimerObject(time.time(), "start", self.__abs_index))
        self.__abs_index = 1

    def as_print(self, as_print: bool) -> None:
        """
        チェックポイント毎にprintするかどうか
        :param as_print:
        :return:
        """
        self.__is_print = as_print

    def as_print_before(self, as_print_before: bool) -> None:
        """
         前回の処理を表示するかどうか
        :param as_print_before:
        :return:
        """
        self.__is_print_before = as_print_before

    def set_print_func(self, func) -> None:
        """
        通常のprint以外のprint関数の登録
        登録オブジェクトが関数でない場合は何もしない
        :param func:
        :return:
        """
        if not hasattr(func, '__call__'):
            return
        self.__print_func = func

    def set_max(self, max_count: int):
        """
        最大オブジェクト数(マイナスの場合は上限なし）。
        ただし、0 もしくは 1 は除く
        :param max_count:
        :return:
        """
        if max_count > 1 or max_count < 0:
            self.__max_object = max_count

    def check(self, label: str = "") -> None:
        """
        チェックポイントを追加。
        :param label:
        :return:
        """
        # もしポーズ中なら、ポーズ継続の状態にする。
        pause_time = .0
        if self.__checkpoint[-1].pause_from is not None and self.__checkpoint[-1].pause_to is None:
            pause_time = self.__checkpoint[-1].pause_from
            self.__checkpoint[-1].pause_to = pause_time
        self.__checkpoint.append(self.TimerObject(time.time(), label, self.__abs_index))
        if pause_time != .0:
            self.__checkpoint[-1].pause_from = pause_time
        if self.__is_print:
            self.print(-1)
        # オブジェクトの限界数を超えた場合は最初のオブジェクトを削除
        if len(self.__checkpoint) > self.__max_object > 1:
            self.remove(1)
        # 全体のインデックスをインクリメント
        self.__abs_index = self.__abs_index + 1

    def c(self, label: str) -> None:
        self.check(label)

    def print(self, index: int) -> None:
        """
        チェックポイントの表示
        :param index:
        :return:
        """
        index_number = self.normalize_index(self.__checkpoint, index)

        before = ""
        if self.__checkpoint[index].index > 99999:
            check_point = "?"
        else:
            check_point = str(self.__checkpoint[index].index)
        check_point = check_point.rjust(5)[:5]

        # 桁数が限界値を超えると表示されなくなるので加工
        def get_sec_str(sec: float, digits: int):
            if len(str(int(sec))) > 10:
                digits = len(str(int(sec)))
            # ここで必ず小数点は丸めておかないと 3.5w465e-10という感じになるのでformatで整形
            return '{:f}'.format(sec).rjust(digits)[:digits] + "[sec]"

        # 起点からの時間(削除済みのポーズ秒数を足す)
        abs_time = self.get_seconds(index=index_number, base_index=0) + self.__removed_pause_time_seconds
        abs_time_str = get_sec_str(abs_time, 10)
        # 前回のチェックポイントからの相対時間
        before_time = .0
        if index_number != 0:
            before_time = self.get_seconds(index=index_number, base_index=index_number - 1)
        time_str = get_sec_str(before_time, 5)
        label_str = self.__checkpoint[index_number].label
        # チェックポイントが２以上ある場合で、かつis print beforeがTrueの場合。
        if self.__is_print_before and index != 0 and len(self.__checkpoint) > 1:
            before = self.__checkpoint[index_number - 1].label + " -> "
        text = "{0}{1} : {2} (+{3}) : {4}{5}".format(self.__label, check_point, abs_time_str, time_str, before,
                                                     label_str)
        if self.__print_func is not None:
            self.__print_func(text)
            return
        print(text)

    @staticmethod
    def normalize_index(lists: list, index: int) -> int:
        """
        入力のリストのインデックスを正規化する。
        つまり、-1だと、末尾のindexが帰ってくる。
        :param lists:
        :param index:
        :return:
        """
        if index < 0:
            if len(lists) + index <= 0:
                # マイナス値で指定したとき、個数よりも小さい場合
                return 0
            else:
                # indexを設定
                return len(lists) + index
        elif index >= len(lists):
            # チェックポイントより大きい場合は末尾のindexに設定
            return len(lists) - 1
        return index

    def get_seconds(self, index: int, base_index: int = 0) -> float:
        """
        indexまでにかかった時間を計算して表示する。
        第２引数がある場合は、第一引数間の双胎時間を返す
        :param index:
        :param base_index:
        :return:
        """
        result = .0
        for i in range(base_index, index):
            if i != 0 and self.__checkpoint[i].pause_to is not None and self.__checkpoint[i].pause_from is not None:
                result = result - self.__checkpoint[i].pause_seconds
            if i >= index - 1:
                break
        result = result + self.__checkpoint[index].time - self.__checkpoint[base_index].time
        # ポーズ中は末尾のparse_fromの時間分をへらす。
        if self.is_pause():
            result = result - (time.time() - self.__checkpoint[-1].pause_from)
        return result

    def get_time(self, index: int) -> float:
        """
        チェックポイントの時間を取得。
        1970年1月1日0時0分0秒からの秒数を浮動小数点数で返します。
        :param index:
        :return:
        """
        return self.__checkpoint[index].time

    def get_times_by_label(self, label: str) -> [float, ]:
        """
        チェックポイントの時間をラベルをもとに取得。配列を返すのでtimeではなくtimes
        :param label:
        :return:
        """
        return [i.time for i in self.__checkpoint if i.label == label]

    def pause(self, is_pause: bool) -> None:
        """
        一時停止
        Trueで一時停止開始、Falseで再実行。
        :param is_pause:
        :return:
        """
        if is_pause:
            self.__checkpoint[-1].pause_from = time.time()
            self.__checkpoint[-1].pause_to = None
        elif not is_pause and self.__checkpoint[-1].pause_from is not None:
            self.__checkpoint[-1].pause_to = time.time()
            self.__checkpoint[-1].pause_seconds = self.__checkpoint[-1].pause_to - self.__checkpoint[-1].pause_from

    def is_pause(self) -> bool:
        """ポーズ中かどうか"""
        return self.__checkpoint[-1].pause_from is not None and self.__checkpoint[-1].pause_to is None

    def pause_cancel(self) -> None:
        self.__checkpoint[-1].pause_from = None
        self.__checkpoint[-1].pause_to = None

    def remove(self, index: int) -> None:
        """
        オブジェクトの削除。ただし、index0は起点なので消してはいけない。
        :param index:
        :return:
        """
        if index == 0:
            print("Timer index 0 cannot be removed.")
            return
        removed_sec = .0
        try:
            removed_sec = self.__checkpoint[index].pause_seconds
            del self.__checkpoint[index]
        except IndexError:
            print("Timer [ {0} ] delete object error".format(self.__label))
            return
        # 削除したデータにポーズの秒数があればその値を保存
        self.__removed_pause_time_seconds = self.__removed_pause_time_seconds + removed_sec

    def remove_abs(self, index: int):
        """
        TimerObjectに割り当てられたインデックスを参照して削除する。
        :param index:
        :return:
        """
        result = [item.index for item in self.__checkpoint]
        if index in result:
            self.remove(result.index(index))