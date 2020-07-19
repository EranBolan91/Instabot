class Utils:
    TIME_SLEEP = 5
    @staticmethod
    def _check_username_password(username, password):
        if username == '' or password == '':
            return False
        else:
            return True

    # Calculate how much time it will take to finish the action
    def arithmetic_progression(self, time_wait, total, rows):
        n = total/rows
        time = 1 + (((n-1)/2) * time_wait) * n
        print(time/60)


Utils().arithmetic_progression(25, 100, 5)

