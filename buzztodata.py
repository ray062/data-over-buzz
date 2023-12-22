# demodulation
# User Notes : Do remember to turn off all sound enhancement features on your device : Equalizer, Dolby effect etc.
# User Notes : Do turn the output devise to 80% volume
# User Notes : Set the receiver the frame rate to 192000. The heigher the better. mono or 2 channel, 2 bytes (16bits) sample width is good enough. 
# User Notes : If the frame rate cannot be set to 192000 or higher, the sound frequency must be set lower. It should not be more than 1/6 of frame rate. For example, for 44100 fram rate, the max frequency is 44100/6=7350

# Attention, the real frequency could be very near to the nominal one but still a little bit different. 
# With a long duration audio, the cumulated shift and float error could be large enough to break the demodulation. 
# The way used here to avoid this is split the data into chunks inside one audio. At each chunk, the 1st cycle position is recalculated

# Attention, with High freq (32khz), the 1st "1" bit cycle after some "0" bit cycles tends to be less loud than then expected.
# By consequence, the 1st "1" bit could be truncated as it's not consedered as the 1st cycle 
# To handle this, it's necessary to lower the max_volume threshold (reduced from 0.9 to 0.8) and put the signal "1" bits longer (changed from 20 to 100)
# Or, dynamically calculate the length of a header/chunk as the first "1"s' length is not fix. Here, the dynamic method is used

# Note : 32khz seems to be the limit. As some unreliabilities emerged beginning with this frequency and to handle these unreliabilities, the code is much more complexe than before to handle these issues.
# Note : At 32khz, the transfer rate would be : 32000/8 = 4000B/sec


import logging
from src.demod import DemodWorkflow

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="input file path") 
    parser.add_argument("output_file", help="output file path")
    parser.add_argument("-s", "--start-at", type=int, default=2, help="start at sec")
    parser.add_argument("-l", "--log-level", default="INFO", help="logging level")

    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    start_at = args.start_at
    log_level = args.log_level

    logging_levels = {
        logging.getLevelName(logging.DEBUG): logging.DEBUG,
        logging.getLevelName(logging.INFO): logging.INFO, 
        logging.getLevelName(logging.WARNING): logging.WARNING,
        logging.getLevelName(logging.ERROR): logging.ERROR,
        logging.getLevelName(logging.CRITICAL): logging.CRITICAL
    }

    logging.basicConfig(level=logging_levels[log_level], format='[%(levelname)s] %(asctime)s - %(message)s')
    _logger.info(f"Input file: {input_file}")
    _logger.info(f"Output file: {output_file}")
    _logger.info(f"Start at: {start_at}")
    _logger.info(f"Log level: {log_level}")
    DemodWorkflow().execute(args.input_file, args.output_file, args.start_at)
    _logger.info("All Done!")
