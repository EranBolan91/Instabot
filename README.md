# Instabot
A program that can like/follow/comment posts and also send direct messages automatically.

## How to start:

1) Clone this project: git@github.com:EranBolan91/Instabot.git
2) CD Instabot
3) Install these packages: 

 a. `pip install selenium`

 b. `pip install ttkthemes`

 c. `pip install schedule`
 
4) Run main.py

4.a) If it doesn't work, you might need to download `chromedriver.exe` from https://chromedriver.chromium.org/downloads 
and save it in the same folder with the bot.py file.


## What the program can do?
1) You can like/comment/follow posts and user by searching hash tag keyword.
2) It can display to you which accounts you are following them, not following you back.
3) You can follow the followers of a specific user also follow the users the spasific user is following them
4) You can like/comment/follow posts by giving a spasific url.
5) You can write random comments on posts. In the input form just separate the words with `,`.
For example: hello,hey,Nice picture ....


### Settings:
In the settings you can set the amount of likes. If a post has more then X likes like/comment/follow.
If the post has less likes then you set then it will just skip the post.

### Accounts:
In the accounts you can add accounts with the username and password. It will save it on the database (using SQLITE database).
Instead write everytime the username and password, just create an account and you can easily log in into that account without typing every time his username and password.

# Still in progress
I'm still working on it, try to make it better and smarter.
I'm working now on new features so so stay tuned and follow me.

####### You guys can also add some functionality and push it to me. I might add your code to this repo.
