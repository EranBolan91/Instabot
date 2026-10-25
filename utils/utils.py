class Utils:
    TIME_SLEEP = 5
    ROUNDS = 5
    PROFILE_IMAGE = '44884218_345707102882519_2446069589734326272_n.jpg'
    NOT_FOUND_USER_TITLE = "Sorry, this page isn't available."
    NOT_FOUND_USER_PARA = "The link you followed may be broken, or the page may have been removed. Go back to Instagram."
    BLOCK_RESTRICTION = "https://www.instagram.com/restriction/"
    BLOCK_CHANGE_PASSWORD = "https://www.instagram.com/challenge/?next=/"
    #SCROLL_BOX = "/html/body/div[7]/div/div/div[2]/div"
    SECOND_LIKES_BUTTON = "/html/body/div[6]/div[2]/div/article/div/div[2]/div[2]/section[2]/div/div[2]/a"
    #CLOSE_BUTTON_SCROLL_BOX = "/html/body/div[7]/div/div/div[1]/div/div[2]/button"
    #self.driver.find_element_by_xpath('//button[text()="Following"]').click()
    UNSUCCESSFUL_LOG_IN_TEXT = "Sorry, your password was incorrect. Please double-check your password."

    RIGHT_ARROW = "//*[name()='svg' and @aria-label='Next']"
    POST_USERNAME = "/html/body/div[2]/div/div/div[3]/div/div/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[1]/div/header/div[2]/div[1]/div[1]/div/div/span/div/div/a"
    FOLLOW_BTN = "//div[@class='_aacl _aaco _aacw _aad6 _aade']"
    PROFILE_IMAGE_XPATH = "/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/header/div/div/span/img"
    POSTS_FOLLOWERS_FOLLOWING = "_ac2a"
    LIKE_BUTTON = "_aamw"
    SCROLL_BOX = "/html/body/div[6]/div[2]/div/div[2]/div[1]/div/div[2]/div/div/div/div/div[2]/div/div[2]/div"
    FIRST_POST = "_aagw"
    CLOSE_BUTTON_SCROLL_BOX = "//*[name()='svg' and @aria-label='Close']"
    USERNAME_IN_SCROLL_BOX = "_aacl._aaco._aacw._aacx._aad7._aade"
    UNFOLLOW_BTN = "//span[text()='Unfollow']"
    #LIKES_TEXT = "//*[contains(text(),'likes')]"
    LIKES_TEXT = "/html/body/div[6]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div/span/a"
    OTHERS_TEXT = "/html/body/div[6]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/section[2]/div/div[2]/span/a"
    # OTHERS_TEXT = "//span[contains(text()='others')]"


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