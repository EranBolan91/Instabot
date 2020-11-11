from ttkthemes import ThemedTk
from view.layout import Layout
# TODO: how to pass data between classes for the accounts when you add new one. it doesn't update the list
# TODO: need to fix when the account follow after a user he wants to access to his followers list. It returns -1 buttons
# TODO: need to change the logic of unfollow only users who are not following back.
#  need to get first the names, close it and again open new window and start unfollow
window = ThemedTk(theme='equilux')
window.iconbitmap('insta_bot.ico')
window.attributes('-fullscreen', True)
Layout(window)

window.mainloop()