# 主要目的：此腳本用於初始化一個 PyQt5 應用程式，設置窗口圖標，創建自定義 View 類的實例，顯示該視圖，並啟動應用程式的事件循環。

import sys  # 導入 sys 模組，用於訪問系統特定的參數和功能，例如命令行參數和退出功能。
from PyQt5.QtWidgets import QApplication  # 從 PyQt5.QtWidgets 導入 QApplication，用於創建 GUI 的主應用程式對象。
from PyQt5.QtGui import QIcon  # 從 PyQt5.QtGui 導入 QIcon，用於設置應用程式窗口的圖標。
from View.view import View  # 從 View.view 模組導入自定義的 View 類，該類通常定義 GUI 的主窗口或界面。

if __name__ == '__main__':  # 檢查腳本是否直接運行（而非作為模組導入），確保以下代碼僅在此情況下執行。
    app = QApplication(sys.argv)  # 創建 QApplication 實例，傳遞命令行參數，用於管理應用程式的控制流程和設置。
    app.setWindowIcon(QIcon("logo.svg"))  # 使用名為 "logo.svg" 的 SVG 文件設置應用程式窗口的圖標。
    view = View()  # 創建自定義 View 類的實例，通常表示主窗口或用戶界面。
    view.show()  # 在螢幕上顯示 View 實例（主窗口）。
    sys.exit(app.exec_())  # 啟動應用程式的事件循環，並在事件循環終止時以應用程式的返回碼退出腳本。