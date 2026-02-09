"""Repository scanner - traverses and reads files from a codebase."""

from dataclasses import dataclass, field
from pathlib import Path

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".tox",
    ".nox",
    "htmlcov",
    ".coverage",
    "eggs",
    "*.egg-info",
    ".idea",
    ".vscode",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".class",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".sqlite", ".db",
}

CODE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
}


@dataclass
class FileInfo:
    """Information about a single file."""
    path: Path
    relative_path: Path
    extension: str
    size_bytes: int
    content: str | None = None
    line_count: int = 0
    is_binary: bool = False
    read_error: str | None = None


@dataclass
class DirectoryInfo:
    """Information about a directory."""
    path: Path
    relative_path: Path
    file_count: int = 0
    subdir_count: int = 0


@dataclass
class RepoStructure:
    """Complete structure of a scanned repository."""
    root_path: Path
    files: list[FileInfo] = field(default_factory=list)
    directories: list[DirectoryInfo] = field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0
    languages_detected: dict[str, int] = field(default_factory=dict)

    def get_top_level_items(self) -> tuple[list[DirectoryInfo], list[FileInfo]]:
        """Get directories and files at the root level."""
        root_dirs = [d for d in self.directories if len(d.relative_path.parts) == 1]
        root_files = [f for f in self.files if len(f.relative_path.parts) == 1]
        return root_dirs, root_files

    def get_files_by_extension(self, ext: str) -> list[FileInfo]:
        """Get all files with a specific extension."""
        return [f for f in self.files if f.extension == ext]

    def find_file(self, name: str) -> FileInfo | None:
        """Find a file by name (not path)."""
        for f in self.files:
            if f.relative_path.name == name:
                return f
        return None


class RepoScanner:
    """Scans a repository and builds an internal representation."""

    def __init__(
        self,
        repo_path: Path,
        *,
        max_file_size_bytes: int | None = 2_000_000,
        respect_gitignore: bool = True,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.max_file_size_bytes = max_file_size_bytes
        self.respect_gitignore = respect_gitignore
        self._gitignore_spec = self._load_gitignore() if respect_gitignore else None

    def _should_ignore(self, path: Path, *, is_dir: bool) -> bool:
        """Check if a path should be ignored."""
        parts = path.parts
        for part in parts:
            if part in IGNORED_DIRS:
                return True
            if part.endswith(".egg-info"):
                return True
        if self._gitignore_spec:
            path_str = path.as_posix()
            if is_dir and not path_str.endswith("/"):
                path_str = f"{path_str}/"
            if self._gitignore_spec.match_file(path_str):
                return True
        return False

    def _load_gitignore(self) -> PathSpec | None:
        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            return None
        try:
            lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return None
        return PathSpec.from_lines(GitWildMatchPattern, lines)

    def _is_binary(self, path: Path) -> bool:
        """Check if a file is binary based on extension."""
        return path.suffix.lower() in BINARY_EXTENSIONS

    def _detect_language(self, ext: str) -> str | None:
        """Detect language from file extension."""
        return CODE_EXTENSIONS.get(ext.lower())

    def _read_file_content(self, path: Path) -> tuple[str | None, int, str | None]:
        """Read file content safely. Returns (content, line_count, error)."""
        try:
            content = path.read_text(encoding="utf-8")
            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            return content, line_count, None
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="latin-1")
                line_count = content.count("\n") + 1
                return content, line_count, None
            except Exception as e:
                return None, 0, str(e)
        except Exception as e:
            return None, 0, str(e)

    def scan(self, read_content: bool = True) -> RepoStructure:
        """Scan the repository and build the internal representation."""
        structure = RepoStructure(root_path=self.repo_path)
        languages: dict[str, int] = {}

        for path in sorted(self.repo_path.rglob("*")):
            relative_path = path.relative_to(self.repo_path)

            if self._should_ignore(relative_path, is_dir=path.is_dir()):
                continue

            if path.is_dir():
                file_count = sum(1 for _ in path.iterdir() if _.is_file())
                subdir_count = sum(1 for _ in path.iterdir() if _.is_dir())
                structure.directories.append(
                    DirectoryInfo(
                        path=path,
                        relative_path=relative_path,
                        file_count=file_count,
                        subdir_count=subdir_count,
                    )
                )
            elif path.is_file():
                ext = path.suffix.lower()
                is_binary = self._is_binary(path)
                size = path.stat().st_size

                content = None
                line_count = 0
                read_error = None

                if self.max_file_size_bytes is not None and size > self.max_file_size_bytes:
                    read_error = f"Skipped: file size {size} exceeds limit {self.max_file_size_bytes}"
                elif read_content and not is_binary:
                    content, line_count, read_error = self._read_file_content(path)

                file_info = FileInfo(
                    path=path,
                    relative_path=relative_path,
                    extension=ext,
                    size_bytes=size,
                    content=content,
                    line_count=line_count,
                    is_binary=is_binary,
                    read_error=read_error,
                )
                structure.files.append(file_info)
                structure.total_lines += line_count

                lang = self._detect_language(ext)
                if lang:
                    languages[lang] = languages.get(lang, 0) + line_count

        structure.total_files = len(structure.files)
        structure.languages_detected = dict(sorted(languages.items(), key=lambda x: -x[1]))

        return structure
