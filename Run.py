import logging
import traceback
import sys

def setup_logging_to_file(filename):
    logging.basicConfig(filename=filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')


def extract_function_name():
    tb = sys.exc_info()[-1]
    stk = traceback.extract_tb(tb, 1)
    fname = stk[0][3]
    return fname


def log_exception(e):
    trace_back = sys.exc_info()[2]
    logging.error(
        "Function {function_name} raised {exception_class} ({exception_docstring}): {exception_message} ----- Exception on line ({line})".format(
            function_name=extract_function_name(),  # this is optional
            exception_class=e.__class__,
            exception_docstring=e.__doc__,
            exception_message=e,
            line=trace_back.tb_lineno))

setup_logging_to_file('Run.log')
def main():
    try:
        print('WATCHDOG ------- STARTED BOT')
        import StormBot
    except Exception as e:
        print('WATCHDOG ------- BOT CRASHED')
        log_exception(str(e))
        main()
        print('WATCHDOG ------- RESTARTING BOT')
main()