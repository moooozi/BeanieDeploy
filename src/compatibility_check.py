import argparse
import functions as fn

checks = ['arch', 'uefi', 'ram', 'space', 'resizable']

def parse_arguments():
    parser = argparse.ArgumentParser()
    for check in checks:
        parser.add_argument(f"--skip_{check}",)
    args = parser.parse_args()
    return args

class CompatibilityResult:
    def __init__(self):
        self.uefi = None
        self.ram = None
        self.space = None
        self.resizable = None
        self.arch = None

    def compatibility_test(self, check_order=None, queue=None):
        check_results = {}   
        if check_order is None:
            check_order = self.checks
        for check_type in check_order:
            if check_type == 'resizable' and not fn.is_admin():
                args = []
                for done_check in check_results.keys():
                    args.append(f'--skip_{done_check}')
                fn.get_admin(' '.join(args))
                return
            print(check_type)
            check_function = getattr(fn, f'check_{check_type}')
            check = check_function()
            if check.returncode != 0:
                result = -1
            else:
                result = check.result
            setattr(self, f'{check_type}', result)
            print(["compatibility_result",check_type, result])
            check_results[check_type] = result

if __name__ == "__main__":

    from sys import argv
    args = parse_arguments()
    
    skipped_checks = []
    for check in checks:
        if args.__getattribute__(f'skip_{check}'):
            skipped_checks.append(check)
    check = CompatibilityResult()
    check.compatibility_test([x for x in checks if x not in skipped_checks])