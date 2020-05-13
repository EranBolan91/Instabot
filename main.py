from ttkthemes import ThemedTk
from view.layout import Layout
from database import db
#TODO: use threading timer
#TODO: check this https://pypi.org/project/python-crontab/
#TODO: how to pass data between classes for the accounts when you add new one. it doesn't update the list
window = ThemedTk(theme='equilux')
window.iconbitmap('insta_bot.ico')
window.attributes('-fullscreen', True)
data = db.Database()
Layout(window)

window.mainloop()