class Utils:
    TIME_SLEEP = 5
    ROUNDS = 5
    # Instagram selectors and texts live in utils/instagram_selectors.json

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

    def clean_number(self, number):
        """Instagram counter text -> int: "1,454" -> 1454, "20.8K" -> 20800, "686M" -> 686000000."""
        text = str(number).strip().replace(",", "").upper()
        multiplier = {"K": 1000, "M": 1000000, "B": 1000000000}.get(text[-1:], 1)
        if multiplier != 1:
            text = text[:-1]
        return int(round(float(text) * multiplier))

    def clean_post_number(self, number):
        return self.clean_number(number)


# Utils().arithmetic_progression(25, 100, 5)
# Utils().clean_number('29k')