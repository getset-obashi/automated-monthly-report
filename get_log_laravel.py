import sys
from typing import List
import re
import os
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from log_entry import LogEntry
from utils import get_aggregation_period, get_nth_weekday_of_month, get_sys_arg_date

DIVISONS = {
    'web':'nfs',
    'admin':'admin'
}

class LatavelLogEntry:
    def __init__(self, time: str, division: str, level: str, message: str):
        """
        LatavelLogEntryクラスのコンストラクタ

        Parameters:
            time (str): ログの時刻を表す文字列
            division (str): ログの部署または分類を表す文字列
            level (str): ログのレベルを表す文字列 (ERROR, INFO, DEBUGなど)
            message (str): ログのメッセージを表す文字列
        """
        self.time = time
        self.division = division
        self.level = level
        self.message = message.strip()

    def __str__(self) -> str:
        """
        LatavelLogEntryオブジェクトを文字列として返す

        Returns:
            str: ログの内容を文字列として表現したもの
        """
        return f"time:{self.time}, division:{self.division}, level:{self.level}, message:{self.message}"
    
    def original_log_format(self) -> str:
        """
        オリジナルのログ形式を文字列として返す

        Returns:
            str: オリジナルのログ形式の文字列
        """
        return f"[{self.time}] {self.division}.{self.level}: {self.message}\n"

class LogParser:
    def __init__(self, log_data: str):
        """
        LogParserクラスのコンストラクタ

        Parameters:
            log_data (str): 解析対象のログデータ
        """
        self.log_data = log_data
        self.pattern = r'\[(?P<time>[\d-]+\s[\d:.]+)\]\s+(?P<division>\w+)\.(?P<level>\w+):\s+(?P<message>[\s\S]*?)(?=\n\[|$)'

    def parse_logs(self) -> List[LatavelLogEntry]:
        """
        ログデータを解析し、LatavelLogEntryオブジェクトのリストとして返す

        Returns:
            List[LatavelLogEntry]: 解析されたログデータをLatavelLogEntryオブジェクトのリストとして返す
        """
        logs: List[LatavelLogEntry] = []
        for match in re.finditer(self.pattern, self.log_data, re.DOTALL):
            log = LatavelLogEntry(match.group("time"), match.group("division"), match.group("level"), match.group("message"))
            logs.append(log)
        return logs

def download_log_file(s3_bucket: str, s3_key: str, local_file_path: str) -> None:
    """
    S3バケットからログファイルをダウンロードします。

    Parameters:
        s3_bucket (str): S3バケット名
        s3_key (str): ダウンロードするオブジェクトのキー（ファイルパス）
        local_file_path (str): ローカルに保存するファイルパス

    Raises:
        ClientError: ダウンロード時にS3でエラーが発生した場合

    Returns:
        None: 正常にダウンロードされた場合は戻り値はありません
    """
    s3 = boto3.client('s3')
    try:
        # オブジェクトの存在を確認
        s3.head_object(Bucket=s3_bucket, Key=s3_key)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f'ログが存在しません。: {s3_key}')
            return
        else:
            raise

    # ログが存在する場合のみダウンロードを行う
    s3.download_file(s3_bucket, s3_key, local_file_path)

def read_log_file(file_path: str) -> str:
    """
    ログファイルを読み込んで文字列として返す

    Parameters:
        file_path (str): ログファイルのパス

    Returns:
        str: 読み込んだログファイルの内容を文字列として返す
    """
    with open(file_path, 'r') as file:
        log_data = file.read()
    return log_data

def write_logs_to_file(logs: List[LatavelLogEntry], output_file_path: str) -> None:
    """
    LatavelLogEntryオブジェクトのリストをファイルに書き込む

    Parameters:
        logs (List[LatavelLogEntry]): 書き込むLatavelLogEntryオブジェクトのリスト
        output_file_path (str): 出力ファイルのパス
    """
    with open(output_file_path, 'w') as file:
        for log in logs:
            file.write(str(log) + '\n')

def create_directory(directory: str) -> None:
    """
    ディレクトリを作成する

    Parameters:
        directory (str): 作成するディレクトリのパス
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def main() -> List[LogEntry]:
    output_directory = f'/Users/h.obashi/PwC/plat4/document/{datetime.now().strftime("%Y%m%d%H%M%S")}'
    start_date, end_date = get_aggregation_period()
    start_date = get_sys_arg_date(1, start_date)
    end_date = get_sys_arg_date(2, end_date)
    return main(output_directory, start_date, end_date)

def main(output_directory:str, start_date:datetime, end_date:datetime) -> List[LogEntry]:
    """
    メイン関数。指定された日付範囲のログファイルをダウンロードして解析し、エラーログを出力します。

    Parameters:
        start_date (datetime): ダウンロード対象の開始日付
        end_date (datetime): ダウンロード対象の終了日付
        output_directory (str): ログファイルの出力ディレクトリ
    """

    result:List[LogEntry] = []
    # 日付範囲のリストを作成
    formatted_dates = []
    current_date = start_date
    while current_date <= end_date:
        formatted_dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)        
    

    for server, division in DIVISONS.items():
        # すべてのログを格納するリスト
        all_logs: List[LatavelLogEntry] = []

        # ローカルに保存するディレクトリ
        directory_path = os.path.join(output_directory, server)
        create_directory(directory_path)

        for formatted_date in formatted_dates:
            # ローカルに保存するファイルパス
            local_file_path = os.path.join(directory_path, f'laravel-{formatted_date}.log')

            # S3のバケット名とキー
            s3_bucket = 'production-app-auditlog'
            s3_key = f'{division}/laravel-{formatted_date}.log'

            # ファイルのダウンロード
            download_log_file(s3_bucket, s3_key, local_file_path)

            # ファイルが存在しない場合(範囲外の日付を指定された場合など)は処理しない
            if not os.path.exists(local_file_path):
                continue

            # ファイルの読み込みとログの解析
            log_data = read_log_file(local_file_path)
            log_parser = LogParser(log_data)
            parsed_logs = log_parser.parse_logs()

            # デバッグ用に最初の一件目のmessageを出力
            if parsed_logs:
                first_message = parsed_logs[0].message
                print(f'First Message ({formatted_date}):', first_message)

            # 解析結果をすべてのログリストに追加
            all_logs.extend(parsed_logs)

        error_logs = [log for log in all_logs if log.level == "ERROR"]

        for log in error_logs:
            result.append(LogEntry(log.time, server, 'アプリケーションログ', log.message))

        # ファイルにログを書き込み
        output_file_path = f'{directory_path}/laravel.error.log'
        write_logs_to_file(error_logs, output_file_path)
    
    return result


if __name__ == "__main__":
    # LogParserのインスタンスを作成してmainメソッドを実行
    main()
