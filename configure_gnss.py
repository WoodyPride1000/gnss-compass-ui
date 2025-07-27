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

    print("\n送信するコマンドを選択してください:")
    print("1. NMEA GPGGAメッセージを1秒ごとに出力 (推奨初期設定)")
    print("2. カスタムコマンドを入力")
    
    choice = input("選択 (1または2): ").strip()

    command_to_send = ""
    if choice == '1':
        # UnicoreモジュールでNMEA GGAメッセージを1秒ごとに出力する一般的なコマンド
        # マニュアル (Unicore Reference Commands Manual) を参照し、正確なコマンドを確認してください。
        # 例: LOG GPGGA ONTIME 1.0
        command_to_send = "LOG GPGGA ONTIME 1.0" 
        print(f"選択されたコマンド: '{command_to_send}'")
    elif choice == '2':
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
            for res in responses:
                if "$GPGGA" in res or "$GPRMC" in res:
                    print(f"NMEAメッセージを検出しました: {res[:50]}...") # 最初の50文字を表示
                    print("NMEA出力が正常に有効になった可能性があります。")
                    break
            else:
                print("NMEAメッセージは検出されませんでした。")
                print("モジュールがNMEA出力を開始するには、追加のコマンドが必要な場合があります。")
                print("Unicore Communicationsのユーザーマニュアルを参照してください。")
        else:
            print("\nモジュールからの応答がありませんでした。コマンドが正しく送信されていないか、モジュールが応答していません。")
            print("シリアルポートの設定、ケーブル接続、モジュールの電源を確認してください。")

    print("\nスクリプトの実行が完了しました。")
    print("NMEAデータが継続的に出力されているか、GNSSコンパスWeb UIで確認してください。")

