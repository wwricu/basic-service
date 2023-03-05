import inspect


def method():
    name = inspect.getframeinfo(inspect.currentframe().f_back)[2]
    frame = inspect.getframeinfo(inspect.currentframe().f_back).function
    print(inspect.getframeinfo(inspect.currentframe().f_back).function)


def main():
    method()


if __name__ == '__main__':
    main()
