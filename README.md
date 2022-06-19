# Instabot
A program that can like/follow/comment posts and also send direct messages automatically.

## How to start:

1) Clone this project: git@github.com:EranBolan91/Instabot.git
2) CD Instabot
3) Install packages: `pip install requirements.txt` 
4) Run main.py

4.a) If it doesn't work, you might need to download `chromedriver.exe` from https://chromedriver.chromium.org/downloads 
and save it in the same folder with the bot.py file.


## What the program can do?
1) Like/comment/follow posts and user by searching hash tag keyword.
2) Display to you which accounts you are following them, not following you back.
3) Follow the 'followers' and 'following' of a specific user.
4) Like/comment/follow posts by giving a specific url.
5) Write random comments on posts.
6) Follow after users who liked post
7) Automatically unfollowing users who we followed them 


### Settings:
In the "settings" section you can set the amount of likes. If a post has more then X likes like/comment/follow.
If the post has less likes then you set then it will just skip the post.

### Accounts:
In the "accounts" section you can add accounts with the username and password. It will save it on the database (using SQLITE database).
Instead write everytime the username and password, just create an account and you can easily log in into that account without typing every time his username and password.
* Create distribution lists
* Save Proxies
* Websites list (Navigating to random website before navigate to Instagram)

