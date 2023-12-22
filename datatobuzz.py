if __name__ == "__main__":
    import logging
    from src.sonify import SonifyWorkflow
    _logger = logging.getLogger(__name__)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="input file path") 
    parser.add_argument("output_file", help="output file path")
    parser.add_argument("-f", "--frequency", type=int, default=32000, help="frequency")
    parser.add_argument("-r", "--frame-rate", type=int, default=192000, help="frame rate")  
    parser.add_argument("-c", "--chunk-size", type=int, default=1, help="chunk size in KB")
    parser.add_argument("-l", "--log-level", default="INFO", help="logging level")

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file 
    frequency = args.frequency
    frame_rate = args.frame_rate
    chunk_size = args.chunk_size
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
    _logger.info(f"Frequency: {frequency}")
    _logger.info(f"Frame rate: {frame_rate}")
    _logger.info(f"Chunk size: {chunk_size}")
    _logger.info(f"Version: {SonifyWorkflow.VERSION}")
    _logger.info(f"Log level: {log_level}")

    wf = SonifyWorkflow(frequency, frame_rate, chunk_size)
    wf.execute(input_file, output_file)
    _logger.info("All Done!")
