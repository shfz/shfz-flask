"""
shfztrace ©hi120ki

Flask用traceライブラリ
各エンドポイントへのリクエストに対してエラーとFrameを取得し、shfz serverへ送信する

- 導入方法

```
from flask import Flask
from shfzflask import shfztrace

app = Flask(__name__)
shfztrace(app, debug=True)
```
"""

import os, sys, json, traceback
from flask import request
import urllib.request


class shfztrace(object):
    def __init__(
        self,
        app,
        trace=True,
        debug=False,
        debugFrame=False,
        report=True,
        fuzzUrl="http://localhost:53653",
    ):
        # trace=Trueのときにトレースを実行する
        if trace:
            self.id = ""
            self.debug = debug
            self.debugFrame = debugFrame
            self.report = report
            self.fuzzUrl = fuzzUrl
            self.framelist = []

            @app.before_request
            def before():
                self.id = request.headers.get("x-shfzlib-id")
                # x-shfzlib-idが設定されていないリクエストに対してはトレースは実行しない
                if self.id != None:
                    sys.settrace(self.profile)

            # 今後responseに変更を加えるときのために残している。現状では不要
            @app.after_request
            def after(response):
                return response

    def profile(self, frame, event, arg):
        if self.debugFrame:
            print(
                ">>> frame:",
                frame.f_code.co_name.ljust(32),
                "event:",
                str(event).ljust(8),
                "arg:",
                str(arg).ljust(8),
                "file:",
                frame.f_code.co_filename,
            )

        # ユーザー定義関数内で例外が発生したときに出てくるframe
        # このとき@app.after_requestは呼ばれないのでここでtracerを止めてデータを送信する
        # handle_user_exceptionは例外が発生したユーザー定義関数の次に呼ばれる
        if frame.f_code.co_name == "handle_user_exception":
            # tracebackの取得
            tb = traceback.extract_tb(sys.exc_info()[2])
            # トレース終了
            sys.settrace(None)
            self.fin(True, str(frame.f_locals["e"]), tb[len(tb) - 1])
            self.framelist.clear()

        # 正常に終了するときに出てくるframe
        # finalize_requestは最後に実行したユーザー定義関数の次に呼ばれる
        if frame.f_code.co_name == "finalize_request":
            # トレース終了
            sys.settrace(None)
            self.fin()
            self.framelist.clear()

        # フレーム名をリストに追加
        # 処理が記述されているファイルがライブラリに該当しないときに追加する
        # ライブラリの例
        # - /Users/username/.pyenv/versions/3.8.12/lib/python3.8/json/encoder.py
        # - /Users/username/.pyenv/versions/3.8.12/lib/python3.8/site-packages/werkzeug/local.py
        # - /Users/username/src/github.com/shfz/testfbapp/venv/lib/python3.8/site-packages/werkzeug/local.py
        # - <frozen importlib._bootstrap_external>
        if (
            "lib/python" not in frame.f_code.co_filename
            and "importlib" not in frame.f_code.co_filename
        ):
            self.framelist.append(
                {
                    "name": frame.f_code.co_name,
                    "file": frame.f_code.co_filename.replace(os.getcwd(), ""),
                }
            )

    def fin(self, is_error=False, error="", tb=""):
        if is_error:
            data = {
                "isServerError": is_error,
                "serverError": error,
                "serverErrorFile": tb.filename.replace(os.getcwd(), ""),
                "serverErrorLineNo": tb.lineno,
                "serverErrorFunc": tb.name,
                "frames": self.framelist,
                "framelen": len(self.framelist),
            }
        else:
            data = {
                "isServerError": is_error,
                "serverError": error,
                "frames": self.framelist,
                "framelen": len(self.framelist),
            }

        if self.debug:
            print("Data:", self.id, data)
            if tb != "":
                print(
                    "Traceback:",
                    tb.filename.replace(os.getcwd(), ""),
                    tb.lineno,
                    tb.name,
                    tb.line,
                )

        if self.report:
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(
                self.fuzzUrl + "/server/" + self.id,
                data=json.dumps(data).encode(),
                method="POST",
                headers=headers,
            )
            with urllib.request.urlopen(req) as res:
                body = res.read().decode()
                if self.debug:
                    print("Report response:", body)
