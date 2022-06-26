import sys
from src.core import Core


def start(_core: Core):
    try:
        _core.start()
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    print("Running Cyclocomputer project")
    core = Core()
    start(core)
    core.close()

    print("Exiting")
    sys.exit(0)
