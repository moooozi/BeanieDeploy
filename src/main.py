import globals as GV
from init import app, logging
import page_check

#   INIT CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
if __name__ == '__main__':

    logging.info('APP STARTING: %s v%s' % (GV.APP_SW_NAME, GV.APP_SW_VERSION))
    print('################################################################\n'
           'IMPORTANT: DO NOT CLOSE THIS CONSOLE WINDOW WHILE APP IS RUNNING\n'
           '################################################################\n\n')

    page_check.run()
    app.mainloop()
