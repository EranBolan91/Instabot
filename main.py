from ttkthemes import ThemedTk
from view.layout import Layout
# TODO: how to pass data between classes for the accounts when you add new one. it doesn't update the list
# TODO: Need to change the date time when i run an action. Get the time before it start to loop, because it ends alot after
window = ThemedTk(theme='equilux')
window.iconbitmap('insta_bot.ico')
window.attributes('-fullscreen', True)
Layout(window)

window.mainloop()