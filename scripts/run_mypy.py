import subprocess
import sys


def main() -> None:
    args = ['mypy', '.']
    ignore_paths = {
        'tests/',
    }
    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    result_lines = result.stdout.decode().strip().split('\n')
    error_lines = [
        line for line in result_lines
        if not any(line.startswith(path) for path in ignore_paths)
    ]
    print('\n'.join(error_lines))  # noqa
    sys.exit(int(bool(error_lines)))


if __name__ == '__main__':
    main()
