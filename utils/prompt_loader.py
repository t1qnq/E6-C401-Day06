import os
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_PROMPT_DIR = Path(__file__).parents[1] / "nodes" / "prompts"
DEFAULT_EXTENSIONS = (".md", ".txt")


def read_prompt_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def candidate_paths(
    prompt_name: str,
    prompt_dir: Optional[Path] = None,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
) -> list[Path]:
    base_dir = prompt_dir or DEFAULT_PROMPT_DIR
    return [base_dir / f"{prompt_name}{ext}" for ext in extensions]


def load_prompt(
    prompt_name: str,
    default_prompt: str = "",
    env_override_var: Optional[str] = None,
    prompt_dir: Optional[Path] = None,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
) -> str:
    if env_override_var:
        env_path = os.getenv(env_override_var)
        if env_path:
            content = read_prompt_file(Path(env_path))
            if content:
                return content

    for path in candidate_paths(prompt_name, prompt_dir=prompt_dir, extensions=extensions):
        content = read_prompt_file(path)
        if content:
            return content

    return default_prompt
