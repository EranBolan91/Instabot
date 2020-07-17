class Utils:
    TIME_SLEEP = 5
    @staticmethod
    def _check_username_password(username, password):
        if username == '' or password == '':
            return False
        else:
            return True