from .healthcheck import healthcheck


def main() -> None:
    print(healthcheck())


if __name__ == "__main__":
    main()
