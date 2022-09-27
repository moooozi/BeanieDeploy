import globals as GV
import functions as fn
from init import app
import page_check

#   INIT CODE   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
if __name__ == '__main__':

    fn.log('%s v%s' % (GV.APP.SW_NAME, GV.APP.SW_VERSION), mode='w')
    fn.log('################################################################\n'
           'IMPORTANT: DO NOT CLOSE THIS CONSOLE WINDOW WHILE APP IS RUNNING\n'
           '################################################################\n\n')

    page_check.run(False)
    app.mainloop()
