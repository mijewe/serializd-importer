from netflix_to_serializd.serializd_adapter import create_client


def main() -> None:
    client = create_client()
    show = client.get_show(114472)
    print(show.name)


if __name__ == "__main__":
    main()
