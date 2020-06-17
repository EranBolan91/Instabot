class ScheduleCalc:
    def __init__(self):
        self._MINUTE = 60
        self._HOUR = self._MINUTE * 60
        self._DAY = self._HOUR * 24
        self.MINUTES = 0
        self.HOURS = 1
        self.DAYS = 2

    def _calc_minutes(self, time):
        return time * self._MINUTE

    def _calc_hours(self, time):
        return time * self._HOUR

    def _calc_days(self, time):
        return time * self._DAY

    def calc_schedule_time(self, action, minutes, hours, days):
        if action == self.MINUTES:
            time = self._calc_minutes(minutes)
        elif action == self.HOURS:
            time = self._calc_hours(hours)
        else:
            time = self._calc_days(days)

        return time
