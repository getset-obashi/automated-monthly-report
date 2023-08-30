from datetime import datetime, timedelta
import os
import sys
from typing import List, Tuple

# ダウンロードのパス
DOWNLOAD_PATH = os.path.join(os.path.expanduser('~') , 'Downloads')


def get_nth_weekday_of_month(months_ago: int, week_number: int, weekday: int) -> datetime:
    """
    指定した月数・週数・曜日に応じて、任意の月の第n週目の曜日を取得する関数。

    Parameters:
        months_ago (int): 今日から何ヶ月前の日付を対象とするかを指定します。
        week_number (int): 第n週目を指定します。
        weekday (int): 曜日を指定します。（0: 月曜日, 1: 火曜日, ..., 6: 日曜日）

    Returns:
        datetime: 第n週目の指定した曜日の日付を返します。
    """
    # 今日の日付を取得
    today = datetime.today()

    # 何ヶ月前の日付を計算
    target_date = today - timedelta(days=months_ago * 30)

    # その月の最初の日を取得
    first_day_of_month = target_date.replace(day=1)

    # その月の第1週の指定曜日の日付を計算
    diff = (weekday - first_day_of_month.weekday()) % 7
    first_weekday = first_day_of_month + timedelta(days=diff)

    # 第n週の指定曜日の日付を計算
    nth_weekday = first_weekday + timedelta(weeks=week_number - 1)

    return nth_weekday

def get_last_weekday_of_month(months_ago: int, weekday: int) -> datetime:
    """
    指定した月数と曜日に応じて、任意の月の最終週の指定した曜日の日付を取得する関数。

    Parameters:
        months_ago (int): 今日から何ヶ月前の日付を対象とするかを指定します。
        weekday (int): 曜日を指定します。（0: 月曜日, 1: 火曜日, ..., 6: 日曜日）

    Returns:
        datetime: 最終週の指定した曜日の日付を返します。
    """
    # 今日の日付を取得
    today = datetime.today()

    # 何ヶ月前の日付を計算
    target_date = today - timedelta(days=months_ago * 30)

    # 指定した月の次の月の初日を取得
    next_month_first_day = target_date.replace(day=1) + timedelta(days=32)
    next_month_first_day = next_month_first_day.replace(day=1)

    # 指定した月の最終週の指定曜日を計算
    last_weekday = next_month_first_day - timedelta(days=next_month_first_day.weekday() + 1)
    diff = (weekday - last_weekday.weekday()) % 7
    last_weekday = last_weekday + timedelta(days=diff)

    return last_weekday

def get_aggregation_period() -> Tuple[datetime, datetime]:
    """
    集計期間を取得します。

    Returns:
        Tuple[datetime, datetime]: 開始日と終了日のタプルを返します。
    """
    return get_nth_weekday_of_month(1, 2, 1), get_nth_weekday_of_month(0, 2, 0)

def get_sys_arg(idx: int, default):
    return sys.argv[idx] if len(sys.argv) > idx else default

def get_sys_arg_date(idx: int, default: datetime) -> datetime:
    return datetime.strptime(sys.argv[idx], "%Y/%m/%d") if len(sys.argv) > idx else default