
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from settings import general_specifications
sys.path.append(f'/home') # für pybit ordner

import logging # wenn kein logging dann diese auskommentieren
logging.basicConfig(filename="../logs_and_data/pybit_background.log", level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

from Bybit_Access import bybit_usdt_perp_client
from strategy_execution import strategy, helper_classes
from logs_and_data import file_writer
import super_global_variables as super_globals

import time, traceback
from concurrent.futures import ThreadPoolExecutor

time_frame = general_specifications.time_frame

'''
code funktioniert nicht für 30m candles

Auf manual override achten !!!

1 vCPU - 5 threads
2 vCPU - 6 threads

nicht vergessen kann code immer testen mit künstlichen Angaben für entry,sl,tp
'''





def thread__regular_ws_reboot() -> None:
    try:
        while super_globals.running:
            time.sleep(0.25)
            if super_globals.is_initialization_done == True:
                t = int(time.time())
                if t % (time_frame*30) == 0 and t % (time_frame*60) != 0:
                    file_writer.to_z_file('sma: '+str(helper_classes.sma_object.get_sma()))
                    file_writer.to_z_file('average_iqr: '+str(helper_classes.vola_iqr_avg.get_average_iqr()))
                    file_writer.to_z_file('temp fragment length: '+str(len(helper_classes.vola_iqr_avg.temp_fragment)))
                    file_writer.to_z_file(str(helper_classes.latest_ticker_data.get_all()))
                    file_writer.to_z_file("")
                    time.sleep(2)
    except:
        super_globals.running = False # notwenig damit die anderen threads stoppen
        file_writer.position_manager_queue.put(False)
        file_writer.stop_loss_fill_queue.put(False)
        raise




def thread__strategy() -> None:
    try:
        while super_globals.running:
            strategy.strategy_main()
    except:
        super_globals.running = False # notwenig damit die anderen threads stoppen
        file_writer.position_manager_queue.put(False)
        file_writer.stop_loss_fill_queue.put(False)
        raise







def run_everything() -> None:
    try:

        # erst wenn alle threads terminiert sind macht weiter
        with ThreadPoolExecutor() as executor:

            thread_A = executor.submit(thread__regular_ws_reboot)
            thread_B = executor.submit(thread__strategy)
            thread_C = executor.submit(file_writer._run_position_manager_queue)
            thread_D = executor.submit(file_writer._run_stop_loss_fill_queue)

            if thread_A.exception() != None:
                raise thread_A.exception()
            
            if thread_B.exception() != None:
                raise thread_B.exception()

            if thread_C.exception() != None:
                raise thread_C.exception()

            if thread_D.exception() != None:
                raise thread_D.exception()

    except:
        bybit_usdt_perp_client.terminate_bot()
        # dieser Code wird ausgeführt und sorgt dafür dass Exceptions gezeigt werden
        file_writer.append_to_log_bybit_client('Exception:\n' + traceback.format_exc())
        raise







if __name__ == '__main__':
    start_tp = int(time.time())
    while start_tp % 60 != 0:
        start_tp += 1
    start_tp += 10
    while super_globals.running:
        time.sleep(0.125)
        if int(time.time()) >= start_tp:
            run_everything()
            break