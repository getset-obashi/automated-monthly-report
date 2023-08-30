class LogEntry:
    def __init__(self, date: str, server: str, location: str, content: str):
        self.date = date
        self.server = server
        self.location = location
        self.content = content

    def to_dict(self):
        return {
            "日付": self.date,
            "対象サーバ": self.server,
            "検知箇所": self.location,
            "ログの内容": self.content
        }