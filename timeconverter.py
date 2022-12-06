import datetime as datetime

b=datetime.datetime.fromisoformat('2022-11-30T13:30:00-08:00')
print(b.hour)
b.replace(hour=10)
print(b.hour)
