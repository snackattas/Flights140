import datetime
import pytz

now = datetime.datetime.now(tz=pytz.UTC) - datetime.timedelta(1)
later = now - datetime.timedelta(400)
ttd = Tweet.objects.filter(timestamp__range=[later, now])
print ttd.count()

# tweets_to_delete.delete()
