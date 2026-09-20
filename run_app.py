from pathlib import Path
import sys


def main() -> int:
    import streamlit.web.cli as stcli

    app_path = Path(__file__).with_name("app.py").resolve()
    sys.argv = ["streamlit", "run", str(app_path)]
    return stcli.main()


if __name__ == "__main__":
    raise SystemExit(main())
