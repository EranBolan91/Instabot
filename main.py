from ttkthemes import ThemedTk
from view.layout import Layout
# TODO: need to change the logic in follow followers to scroll and the follow (like combination)
# TODO: need to fix when the account follow after a user he wants to access to his followers list. It returns -1 buttons
# TODO: need to change the logic of unfollow only users who are not following back.-**changed-still need to run tests **
#  need to get first the names, close it and again open new window and start unfollow
# TODO: need to add table for proxy and UI
# TODO: add check how many posts user has
# TODO: headless. change the logic to login
# TODO: display combination window on statistic tab
# TODO: add to DM text box that limit messages - **** added - just need to run few tests ****
# TODO: write error message function on 'main_bot' to use on all other classes - ** added **
# TODO: add limit box on unfollowers that limits how many users to unfollow - *** added - just need to run few tests **
# TODO: on the statistic page, create box details for every account that display his all actions
# TODO: add on the statistic a drop list with box that display actions of every account
# TODO: add table to unfollow that counts how many users follow back when i unfollow them **created table, just need to display **
window = ThemedTk(theme='equilux')
window.iconbitmap('insta_bot.ico')
window.attributes('-fullscreen', True)
Layout(window)

window.mainloop()