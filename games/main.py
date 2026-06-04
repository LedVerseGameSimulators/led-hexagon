# uncompyle6 version 3.9.3
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.13.7 (main, Aug 14 2025, 11:12:11) [Clang 17.0.0 (clang-1700.0.13.3)]
# Embedded file name: main.py
import datetime, time, multiprocessing, shelve, sys, traceback
import gui.gui_game_main as gui
from loguru import logger
if __name__ == "__main__":
    program_is_opened_time = time.time()
    program_is_opened_last_time = 0
    f = shelve.open("./setting/program_params")
    try:
        program_is_opened_last_time = f.get("program_is_opened")
    except:
        pass

    f["program_is_opened"] = program_is_opened_time
    f.close()
    if program_is_opened_time - program_is_opened_last_time < 10:
        f = shelve.open("./setting/program_params")
        f["program_is_opened"] = program_is_opened_last_time
        f.close()
        sys.exit(0)
    multiprocessing.freeze_support()
    f = shelve.open("./setting/debug_parameter")
    log = f.get("log")
    f.close()
    current_time = datetime.datetime.now()
    if not log:
        logger.info("led_play.log is close", current_time.strftime("%H:%M:%S"))
        logger.remove()
    else:
        my_log = logger.add("./log/led_play_runtime.log", retention="1 days", rotation="100 MB", level="INFO")
        version = "Ledhexagon play ver: 1.1.5 \n  game_record_rt update "
        logger.info("led_play.log is record {} {}", current_time.strftime("%H:%M:%S"), version)
    try:
        gui.GuiMain()
    except:
        logger.error("{}", traceback.format_exc())

# okay decompiling /Users/apple/parallel-work/decompile_workspace/ledhexagon.exe_extracted/main.pyc
