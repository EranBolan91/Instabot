class Utils:
    TIME_SLEEP = 5
    ROUNDS = 5
    PROFILE_IMAGE = '44884218_345707102882519_2446069589734326272_n.jpg'
    NOT_FOUND_USER_TITLE = "Sorry, this page isn't available."
    NOT_FOUND_USER_PARA = "The link you followed may be broken, or the page may have been removed. Go back to Instagram."
    BLOCK_RESTRICTION = "https://www.instagram.com/restriction/"
    BLOCK_CHANGE_PASSWORD = "https://www.instagram.com/challenge/?next=/"
    SCROLL_BOX = "/html/body/div[7]/div/div/div[2]/div"
    LIKES_BUTTON = "/html/body/div[5]/div[2]/div/article/div[3]/section[2]/div/div/a"
    SECOND_LIKES_BUTTON = "/html/body/div[6]/div[2]/div/article/div/div[2]/div[2]/section[2]/div/div[2]/a"
    CLOSE_BUTTON_SCROLL_BOX = "/html/body/div[7]/div/div/div[1]/div/div[2]/button"
    UNSUCCESSFUL_LOG_IN_TEXT = "Sorry, your password was incorrect. Please double-check your password."

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
        # check if the number is thousands example: 1,454 , 2,888 , 9,999
        thousands = number.find(',')
        # check if the number is more then ten thousands example: 10k , 20.8k , 90.9k
        ten_thousands = number.find('k')
        # check if the number is millions example: 10.1m , 20m , 90.9m
        millions = number.find('m')
        if thousands != -1:
            clean_num = int(number.replace(',', ''))
            return clean_num
        elif ten_thousands != -1:
            if number.find('.') != -1:
                num_no_dot = number.replace('.', '')
                clean_num = int(num_no_dot.replace('k', ''))
                return clean_num * 100
            else:
                clean_num = int(number.replace('k', ''))
                return clean_num * 1000
        elif millions != -1:
            if number.find('.') != -1:
                num_no_dot = number.replace('.', '')
                clean_num = int(num_no_dot.replace('m', ''))
                return clean_num * 100000
            else:
                clean_num = int(number.replace('m', ''))
                return clean_num * 100000
        else:
            return int(number)

    def clean_post_number(self, number):
        thousands = number.find(',')
        if thousands != -1:
            clean_num = int(number.replace(',', ''))
            return int(clean_num)
        else:
            return int(number)


# Utils().arithmetic_progression(25, 100, 5)
# Utils().clean_number('29k')