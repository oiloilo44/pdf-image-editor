import os

# Poppler 실행 파일 경로
POPPLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../resources/poppler/Library/bin")
)

# Backward-compatible alias for older imports.
POPLER_PATH = POPPLER_PATH
