import logging

from heart import Heart as Jarvis


def main():
    # Initialize our own logger
    logger = logging.getLogger("Jarvis")
    logger.info("Starting Jarvis!")

    # [Operation] Start Jarvis - beep boop
    jarvis = Jarvis(logger=logger)

    # Run the daily routine as a sample
    jarvis.run_daily_routine()


if __name__ == "__main__":
    main()
