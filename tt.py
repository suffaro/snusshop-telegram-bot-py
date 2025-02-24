import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification

app = ttk.Window()
import time

toast = ToastNotification(
    title="ttkbootstrap toast message",
    message="This is a toast message",
    duration=3000,
    alert=True
)
time.sleep(10)
toast.show_toast()

app.mainloop()