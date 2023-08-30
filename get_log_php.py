import boto3
import sys
import os
from datetime import datetime
from typing import List
from log_entry import LogEntry
from utils import get_aggregation_period, get_sys_arg

LOG_GROUP_NAME = 'log'
LOG_STREAM_ADMIN = '/var/log/httpd/admin.cisocyber.jp.pwc.com.error.log'
LOG_STREAM_WEB = '/var/log/httpd/cisocyber.jp.pwc.com.error.log'

LOG_STREAMS = {
    'admin': LOG_STREAM_ADMIN,
    'web': LOG_STREAM_WEB
}

def get_log_entries(log_group_name, log_stream_name, start_time, end_time, server, region_name=None) -> List[LogEntry]:
    """
    CloudWatch Logs からログエントリを取得してパースする

    :param log_group_name: ロググループ名
    :param log_stream_name: ログストリーム名
    :param start_time: 取得開始時間 (UNIX タイムスタンプ)
    :param end_time: 取得終了時間 (UNIX タイムスタンプ)
    :param server: サーバ名
    :param region_name: リージョン名
    :return: LogEntry オブジェクトのリスト
    """
    client = boto3.client('logs', region_name=region_name)
    log_entries = []

    # Retrieve log entries
    def retrieve_log_entries():
        response = client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            startTime=start_time,
            endTime=end_time,
            startFromHead=True)
        for event in response['events']:
            log_entries.append(parse_log_entry(event, server))
        while True:
            prev_token = response['nextForwardToken']
            if 'ResponseMetadata' in response:
                response_metadata = response['ResponseMetadata']
                if 'HTTPHeaders' in response_metadata:
                    http_headers = response_metadata['HTTPHeaders']
                    if 'date' in http_headers:
                        date_value = http_headers['date']
                        parsed_date = datetime.strptime(date_value, '%a, %d %b %Y %H:%M:%S %Z')
                        formatted_date = parsed_date.strftime('%Y/%m/%d %H:%M:%S')
                        print(f"Formatted Date: {formatted_date}")
            response = client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                startTime=start_time,
                endTime=end_time,
                nextToken=prev_token)
            for event in response['events']:
                log_entries.append(parse_log_entry(event, server))

            if response['nextForwardToken'] == prev_token:
                print("break")
                break

    print(f"get_log_event:{log_stream_name}")

    retrieve_log_entries()

    return log_entries


def parse_log_entry(event, server) -> LogEntry:
    """
    CloudWatch Logs のイベントを LogEntry オブジェクトにパースする

    :param event: CloudWatch Logs のイベント
    :param server: サーバ名
    :return: パースされた LogEntry オブジェクト
    """
    timestamp = datetime.fromtimestamp(int(event['timestamp']) / 1000)
    message = event['message']
    
    return LogEntry(timestamp, server, 'PHP', message)


def main() -> List[LogEntry]:
    """
    メイン関数。指定された日付範囲のログファイルをダウンロードして解析し、エラーログを出力します。
    """
    start_date, end_date = get_aggregation_period()
    output_directory = get_sys_arg(1, os.path.join(os.getcwd(),datetime.today().strftime('%Y%m')))
    return main(output_directory, start_date, end_date)

def main(output_directory:str, start_date:datetime, end_date:datetime) -> List[LogEntry]:
    """
    メイン関数。指定された日付範囲のログファイルをダウンロードして解析し、エラーログを出力します。

    Parameters:
        start_date (datetime): ダウンロード対象の開始日付
        end_date (datetime): ダウンロード対象の終了日付
        output_directory (str): ログファイルの出力ディレクトリ
    """
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    log_entries: List[LogEntry] = []
    for server, log_stream_name in LOG_STREAMS.items():
        disp_start = start_date.strftime('%Y%m%d')
        disp_end = end_date.strftime('%Y%m%d')
        dir = os.path.join(output_directory, server)
        file_name = os.path.join(dir, f'{disp_start}_{disp_end}.error.log')
        if not os.path.exists(dir):
            os.makedirs(dir)
        unix_start = int(start_date.timestamp() * 1000)
        unix_end = int(end_date.timestamp() * 1000)

        server_log_entries = get_log_entries(LOG_GROUP_NAME, log_stream_name, unix_start, unix_end, server)
        log_entries.extend(server_log_entries)

        with open(file_name, 'w+') as f:
            for entry in server_log_entries:
                f.write(str(entry.to_dict()) + '\n')

    # Processed log entries
    for entry in log_entries:
        print(entry.to_dict())
    return log_entries


if __name__ == "__main__":
    main()
