from ttkthemes import ThemedTk
from view.layout import Layout
# TODO: how to pass data between classes for the accounts when you add new one. it doesn't update the list
window = ThemedTk(theme='equilux')
window.iconbitmap('insta_bot.ico')
window.attributes('-fullscreen', True)
Layout(window)

window.mainloop()