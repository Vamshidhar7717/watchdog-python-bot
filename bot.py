import time

#interrupt_countdown = 5
try:
    while True:
        print("Hello from bot")
        """ interrupt_countdown -= 1
        if interrupt_countdown <= 0:
            print("Interrupting bot after 5 iterations.")
            break """
        time.sleep(5)
except KeyboardInterrupt:
    print("Bot was interrupted.")