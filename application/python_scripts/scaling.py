import pandas as pd
from easing import Easing

class Scaling:
    def __init__(self, df_list: list[pd.DataFrame], x_start=1.0, x_end=1.5, duration_list=[5.0], fps=30) -> None:
        """拡大・x 移動量・y 移動量の 3 つの Easing を初期化。

        Args:
            df_list (list[pd.DataFrame]): 拡大率とxy方向の移動量が含まれた dataframe を指定。
            x_start (float, optional): 最初の状態でのxの値。 Defaults to 1.0.
            x_end (float, optional): 最後の状態でのxの値。 Defaults to 1.5.
            duration_list (list, optional): エフェクトの長さ。 Defaults to [5.0].
            fps (int, optional): 1秒に何フレームか. Defaults to 30.
        """
        self.magnification_easing = Easing(duration_list = duration_list,
                                           fps = fps,
                                           custom_y_list = [df['Z_33'].values for df in df_list]
                                           )
        self.translation_x_easing = Easing(duration_list = duration_list,
                                           fps = fps,
                                           custom_y_list = [df['x_33'].values for df in df_list],
                                           )
        self.translation_y_easing = Easing(duration_list = duration_list,
                                           fps = fps,
                                           custom_y_list = [df['y_33'].values for df in df_list],
                                           )
        
        # easing が進行中かどうかを管理する。
        self.is_scaling = False
        
        # 話しているかどうかを管理する。
        self.is_speaking = False
    
    def update_effect(self):
        magnification = self.magnification_easing.customized_easing()
        dx = self.translation_x_easing.customized_easing()
        dy = self.translation_y_easing.customized_easing()
        self.is_scaling = self.magnification_easing.is_easing
        return (magnification, dx, dy)
    
    def restart(self):
        self.is_scaling = True
        self.magnification_easing.is_easing = True
        self.translation_x_easing.is_easing = True
        self.translation_y_easing.is_easing = True

        self.magnification_easing.restart()
        self.translation_x_easing.restart()
        self.translation_y_easing.restart()
