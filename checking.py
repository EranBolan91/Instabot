from bot_folder import main_bot
import time

if __name__ == "__main__":
    insta = main_bot.InstagramBot('eranbolan91@gmail.com', 'eranbolan91', False)
    insta._login()
    time.sleep(2)
    insta._nav_user('sina.sandtel')
    time.sleep(1.4)
    insta._has_profile_image()
    # insta._screen_shot('eranbolan')
    # insta._send_email('eranbolan', '20', '10/10/2020')
    # txt = 'https://instagram.fsub8-1.fna.fbcdn.net/v/t51.2885-19/44884218_345707102882519_2446069589734326272_n.jpg?_nc_ht=instagram.fsub8-1.fna.fbcdn.net&_nc_cat=1&_nc_ohc=hs698vsjrYIAX-9qRF0&oh=6705de6637e64a28c3b8372877a7f9ed&oe=5FB1E08F&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.2'
    # has_text = txt.find('44884218_345707102882519_2446069589734326272_n.jpg')
    # print(has_text)


# https://instagram.fmct2-1.fna.fbcdn.net/v/t51.2885-19/44884218_345707102882519_2446069589734326272_n.jpg?_nc_ht=instagram.fmct2-1.fna.fbcdn.net&_nc_ohc=hs698vsjrYIAX_bfJMG&oh=0a70e39f59c8a1a7b5c6c8c6dd7f697a&oe=5FB1E08F&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.2
# https://instagram.fdmb1-1.fna.fbcdn.net/v/t51.2885-19/44884218_345707102882519_2446069589734326272_n.jpg?_nc_ht=instagram.fdmb1-1.fna.fbcdn.net&_nc_ohc=hs698vsjrYIAX-15VCh&oh=6759a9b4227011c0c5f97c57348be9c2&oe=5FB1E08F&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.2
# https://instagram.fiev11-1.fna.fbcdn.net/v/t51.2885-19/44884218_345707102882519_2446069589734326272_n.jpg?_nc_ht=instagram.fiev11-1.fna.fbcdn.net&_nc_ohc=hs698vsjrYIAX8ZXvQp&oh=2f88e738af5d9d138a37238c40d76c7e&oe=5FB1E08F&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.2
# https://instagram.fsub8-1.fna.fbcdn.net/v/t51.2885-19/44884218_345707102882519_2446069589734326272_n.jpg?_nc_ht=instagram.fsub8-1.fna.fbcdn.net&_nc_cat=1&_nc_ohc=hs698vsjrYIAX-9qRF0&oh=6705de6637e64a28c3b8372877a7f9ed&oe=5FB1E08F&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.2

# https://instagram.fsdv3-1.fna.fbcdn.net/v/t51.2885-19/s150x150/121277095_2776083959333902_3585922063442444776_n.jpg?_nc_ht=instagram.fsdv3-1.fna.fbcdn.net&_nc_ohc=xilH7Zy2K30AX9FJ_Hz&oh=5ffd6da5e37cc2f4f1c4f8e2094032e2&oe=5FB2CCDD
# https://instagram.fsdv3-1.fna.fbcdn.net/v/t51.2885-19/s150x150/117288601_586326512061978_4548125519637624742_n.jpg?_nc_ht=instagram.fsdv3-1.fna.fbcdn.net&_nc_ohc=SixfEr7IbWkAX8LuJrl&oh=870257acbf58fc0cfdaa8d16ab5dd848&oe=5FB21AED

