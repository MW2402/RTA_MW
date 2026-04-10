from kafka import KafkaConsumer
import json
from datetime import datetime
import datetime as dt

consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers='broker:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)
delta = dt.timedelta(seconds=60)
user_stats = {}

for message in consumer:
    user = message.value["user_id"]
    time_now = datetime.fromisoformat(message.value["timestamp"])
    if user not in user_stats.keys():
        user_stats[user] = []
    user_stats[user].append(time_now)
    user_stats[user] = [t for t in user_stats[user] if time_now - t <= delta]
    if len(user_stats[user]) > 3:
        print(f"ALERT: User: {user} made more than 3 transactions in the last 60 seconds")
