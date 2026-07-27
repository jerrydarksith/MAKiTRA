from personal_bot.bootstrap import run_application


if __name__ == "__main__":
    try:
        run_application()
    except ValueError as error:
        print(error)
