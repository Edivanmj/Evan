# Ponto de entrada único do EVAN OS
import argparse

from modes import MODES


def main() -> None:
    parser = argparse.ArgumentParser(description="EVAN OS")
    parser.add_argument(
        "--modo",
        choices=sorted(MODES),
        default="texto",
        help="texto (padrão), voz, voz-continua ou visual",
    )
    args = parser.parse_args()
    MODES[args.modo]()


if __name__ == "__main__":
    main()
