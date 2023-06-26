class Utils:
    TIME_SLEEP = 5
    ROUNDS = 5
    PROFILE_IMAGE = '44884218_345707102882519_2446069589734326272_n.jpg'
    NOT_FOUND_USER_TITLE = "Sorry, this page isn't available."
    NOT_FOUND_USER_PARA = "The link you followed may be broken, or the page may have been removed. Go back to Instagram."
    BLOCK_RESTRICTION = "https://www.instagram.com/restriction/"
    BLOCK_CHANGE_PASSWORD = "https://www.instagram.com/challenge/?next=/"
    SCROLL_BOX = "/html/body/div[7]/div/div/div[2]/div"
    SECOND_LIKES_BUTTON = "/html/body/div[6]/div[2]/div/article/div/div[2]/div[2]/section[2]/div/div[2]/a"
    CLOSE_BUTTON_SCROLL_BOX = "/html/body/div[7]/div/div/div[1]/div/div[2]/button"
    UNSUCCESSFUL_LOG_IN_TEXT = "Sorry, your password was incorrect. Please double-check your password."

    RIGHT_ARROW = "//*[name()='svg' and @aria-label='Next']"
    POST_USERNAME = "/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[1]/div/header/div[2]/div[1]/div[1]/div/div/span/div/div/a"
    FOLLOW_BTN = "//div[@class='_aacl _aaco _aacw _aad6 _aade']"
    LIKE_BUTTON = "_aamw"
    PROFILE_IMAGE_XPATH = "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/header/div/div/span/img"
    POSTS_FOLLOWERS_FOLLOWING = "_ac2a"

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
        ten_thousands = number.find('K')
        # check if the number is millions example: 10.1m , 20m , 90.9m
        millions = number.find('M')
        if thousands != -1:
            clean_num = int(number.replace(',', ''))
            return clean_num
        elif ten_thousands != -1:
            if number.find('.') != -1:
                num_no_dot = number.replace('.', '')
                clean_num = int(num_no_dot.replace('K', ''))
                return clean_num * 100
            else:
                clean_num = int(number.replace('K', ''))
                return clean_num * 1000
        elif millions != -1:
            if number.find('.') != -1:
                num_no_dot = number.replace('.', '')
                clean_num = int(num_no_dot.replace('M', ''))
                return clean_num * 100000
            else:
                clean_num = int(number.replace('M', ''))
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