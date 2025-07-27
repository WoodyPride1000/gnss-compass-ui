import serial
import time
import sys

# WTRTK-982モジュールにNMEA出力を設定するPythonスクリプト
# このスクリプトは、指定されたシリアルポートとボーレートを使用してモジュールにコマンドを送信します。
# コマンド送信後、モジュールからの応答をリアルタイムで表示し、NMEAデータが出力されているか確認できます。

def send_command_and_read_response(port, baudrate, command, timeout=5, read_duration=10):
    """
    シリアルポート経由でコマンドを送信し、応答を読み取ります。

    Args:
        port (str): シリアルポートのパス (例: '/dev/ttyUSB0', 'COM3')
        baudrate (int): ボーレート (例: 115200)
        command (str): モジュールに送信するコマンド文字列
        timeout (int): シリアルポートの読み取りタイムアウト時間 (秒)
        read_duration (int): コマンド送信後にデータを読み取る時間 (秒)
    """
    print(f"\n--- シリアルポート '{port}' ({baudrate}bps) に接続中 ---")
    try:
        # シリアルポートを開く
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(0.1) # ポートが開くのを少し待つ

        # コマンドを送信 (改行コードを追加)
        # Unicoreモジュールは、コマンドの終端にCR+LF (\\r\\n) を必要とすることが多いです。
        full_command = command.strip() + '\r\n'
        print(f"コマンド送信: '{full_command.strip()}'")
        ser.write(full_command.encode('ascii')) # ASCIIエンコーディングで送信

        print(f"--- {read_duration}秒間、モジュールからの応答を読み取り中 ---")
        start_time = time.time()
        response_lines = []
        while (time.time() - start_time) < read_duration:
            if ser.in_waiting > 0:
                try:
                    # バイナリメッセージの場合、ASCIIデコードでエラーになる可能性があるため、無視する
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        print(f"受信: {line}")
                        response_lines.append(line)
                except UnicodeDecodeError:
                    print("受信データがASCIIでデコードできませんでした。バイナリデータかもしれません。")
                except Exception as e:
                    print(f"データ読み取り中にエラーが発生しました: {e}")
            time.sleep(0.01) # 短い遅延でCPU使用率を抑える

        print("--- 読み取り終了 ---")
        ser.close()
        print(f"シリアルポート '{port}' を閉じました。")
        return response_lines

    except serial.SerialException as e:
        print(f"エラー: シリアルポート '{port}' に接続できませんでした。")
        print(f"詳細: {e}")
        print("以下の点を確認してください:")
        print("  1. ポート名が正しいか (例: /dev/ttyUSB0, COMx)")
        print("  2. ラズベリーパイのユーザーが 'dialout' グループに属しているか (sudo usermod -a -G dialout your_username)")
        print("  3. モジュールが正しく接続され、電源が入っているか")
        print("  4. 別のプログラムがポートを使用していないか")
        return None
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    print("GNSSコンパス (WTRTK-982) NMEA設定スクリプト")
    print("---------------------------------------")

    # ユーザーからの入力取得
    serial_port = input("シリアルポート名を入力してください (例: /dev/ttyUSB0, COM3): ").strip()
    
    try:
        baud_rate = int(input("ボーレートを入力してください (例: 115200): ").strip())
    except ValueError:
        print("エラー: 無効なボーレートです。数値を入力してください。")
        sys.exit(1)

    print("\n更新レートを選択してください:")
    print("1. 1 Hz (1秒ごと)")
    print("2. 10 Hz (0.1秒ごと)")
    
    rate_choice = input("選択 (1または2): ").strip()
    
    update_interval = 1.0 # デフォルトは1Hz
    if rate_choice == '2':
        update_interval = 0.1
        print("更新レート: 10 Hz が選択されました。")
    elif rate_choice == '1':
        print("更新レート: 1 Hz が選択されました。")
    else:
        print("エラー: 無効な選択です。デフォルトの1 Hzを使用します。")

    print("\n送信するコマンドを選択してください:")
    print(f"1. NMEA GPGGAメッセージを出力 (更新レート: {update_interval}秒ごと)")
    print(f"2. Unicoreバイナリ PVTSLNメッセージを出力 (推奨: 方位角、ピッチ、ロールを含む) (更新レート: {update_interval}秒ごと)")
    print(f"3. NMEA GPHDTメッセージを出力 (真方位角のみ) (更新レート: {update_interval}秒ごと)")
    print("4. カスタムコマンドを入力")
    
    choice = input("選択 (1, 2, 3, または 4): ").strip()

    command_to_send = ""
    if choice == '1':
        command_to_send = f"LOG GPGGA ONTIME {update_interval}" 
        print(f"選択されたコマンド: '{command_to_send}'")
    elif choice == '2':
        # UnicoreバイナリPVTSLNメッセージを1秒ごとに出力するコマンド
        # マニュアル (Unicore Reference Commands Manual) の "LOG Command" と "PVTSLN" セクションを参照してください。
        command_to_send = f"LOG PVTSLN ONTIME {update_interval}"
        print(f"選択されたコマンド: '{command_to_send}'")
        print("注意: PVTSLNはバイナリメッセージのため、ターミナルでの表示は読みにくい場合がありますが、コマンドがOK応答を返せば成功です。")
    elif choice == '3':
        # NMEA GPHDTメッセージを1秒ごとに出力するコマンド
        # マニュアル (Unicore Reference Commands Manual) の "LOG Command" と "GPHDT" セクションを参照してください。
        command_to_send = f"LOG GPHDT ONTIME {update_interval}"
        print(f"選択されたコマンド: '{command_to_send}'")
    elif choice == '4':
        command_to_send = input("送信するカスタムコマンドを入力してください: ").strip()
        if not command_to_send:
            print("エラー: コマンドが入力されていません。")
            sys.exit(1)
    else:
        print("エラー: 無効な選択です。")
        sys.exit(1)

    # コマンドを送信し、応答を読み取る
    if command_to_send:
        responses = send_command_and_read_response(serial_port, baud_rate, command_to_send)
        if responses:
            print("\n--- コマンド送信後のモジュール応答サマリー ---")
            nmea_detected = False
            pvt_detected = False
            for res in responses:
                if "$GNGGA" in res or "$GPGGA" in res or "$GNRMC" in res or "$GPRMC" in res or "$GPHDT" in res:
                    print(f"NMEAメッセージを検出しました: {res[:50]}...") # 最初の50文字を表示
                    nmea_detected = True
                # PVTSLNはバイナリなので、ASCIIデコードでは直接文字列として検出できない可能性が高い
                # コマンドのOK応答があれば成功とみなす
                if "response: OK" in res and ("LOG PVTSLN" in command_to_send or "LOG GPHDT" in command_to_send):
                    pvt_detected = True
            
            if nmea_detected or pvt_detected:
                print("出力が正常に有効になった可能性があります。")
                if pvt_detected and "LOG PVTSLN" in command_to_send:
                    print("PVTSLNはバイナリメッセージのため、ターミナルで読みにくいですが、モジュールは出力しています。")
            else:
                print("目的のメッセージは検出されませんでした。")
                print("モジュールがNMEA/バイナリ出力を開始するには、追加のコマンドが必要な場合があります。")
                print("Unicore Communicationsのユーザーマニュアルを参照してください。")
        else:
            print("\nモジュールからの応答がありませんでした。コマンドが正しく送信されていないか、モジュールが応答していません。")
            print("シリアルポートの設定、ケーブル接続、モジュールの電源を確認してください。")

    print("\nスクリプトの実行が完了しました。")
    print("データが継続的に出力されているか、GNSSコンパスWeb UIで確認してください。")

