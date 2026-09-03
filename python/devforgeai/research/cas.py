"""Linux filesystem primitives used by Research CAS custody.

These helpers deliberately expose only no-follow, no-overwrite operations.  A
caller must treat an unavailable primitive as a hard failure; there is no
copy/unlink or overwrite fallback for content-addressed objects.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import stat
from pathlib import Path


RENAME_NOREPLACE = 1


def nofollow_flag() -> int:
    """Return ``O_NOFOLLOW`` or fail closed on unsupported platforms."""

    flag = getattr(os, "O_NOFOLLOW", None)
    if flag is None:
        raise OSError(errno.ENOTSUP, "O_NOFOLLOW is unavailable")
    return flag


def _open_parent_directory(path: Path) -> int:
    """Open and identity-check the final parent directory without following it."""

    before = path.parent.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise OSError(errno.ENOTDIR, "expected nonsymlink parent directory", path.parent)
    descriptor = os.open(
        path.parent,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | nofollow_flag(),
    )
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise OSError(
                errno.ESTALE, "parent directory changed while opening", path.parent
            )
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def rename_noreplace(source: Path, target: Path) -> None:
    """Atomically rename ``source`` to an absent ``target``.

    Linux ``renameat2(RENAME_NOREPLACE)`` is the only admitted implementation.
    In particular, this function never emulates the operation with copy/unlink
    or a racy exists check followed by ordinary rename.
    """

    try:
        libc = ctypes.CDLL(None, use_errno=True)
        operation = libc.renameat2
    except (OSError, AttributeError) as exc:
        raise OSError(errno.ENOSYS, "renameat2(RENAME_NOREPLACE) unavailable") from exc
    operation.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    operation.restype = ctypes.c_int
    source_parent = target_parent = -1
    try:
        source_parent = _open_parent_directory(source)
        target_parent = _open_parent_directory(target)
        result = operation(
            source_parent,
            os.fsencode(source.name),
            target_parent,
            os.fsencode(target.name),
            RENAME_NOREPLACE,
        )
        if result != 0:
            number = ctypes.get_errno()
            raise OSError(number, os.strerror(number), target)
    finally:
        for descriptor in (target_parent, source_parent):
            if descriptor >= 0:
                os.close(descriptor)


def write_exclusive(path: Path, content: bytes, mode: int = 0o600) -> None:
    """Create, flush, and close a nonsymlink regular file without overwrite."""

    parent = _open_parent_directory(path)
    descriptor = -1
    try:
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow_flag(),
            mode,
            dir_fd=parent,
        )
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(errno.EINVAL, "exclusive target is not a regular file", path)
        remaining = memoryview(content)
        while remaining:
            count = os.write(descriptor, remaining)
            if count <= 0:
                raise OSError(errno.EIO, "short exclusive write", path)
            remaining = remaining[count:]
        os.fsync(descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def read_regular_nofollow(path: Path) -> bytes:
    """Read a stable regular file through a no-follow descriptor."""

    parent = _open_parent_directory(path)
    descriptor = -1
    try:
        before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise OSError(errno.EINVAL, "expected nonsymlink regular file", path)
        descriptor = os.open(
            path.name, os.O_RDONLY | nofollow_flag(), dir_fd=parent
        )
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise OSError(errno.ESTALE, "file changed while opening", path)
        chunks: list[bytes] = []
        while block := os.read(descriptor, 1024 * 1024):
            chunks.append(block)
        after = os.fstat(descriptor)
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise OSError(errno.ESTALE, "file changed while reading", path)
        return b"".join(chunks)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def hash_regular_nofollow(path: Path) -> tuple[str, int]:
    """Hash a stable regular file through a no-follow descriptor."""

    parent = _open_parent_directory(path)
    descriptor = -1
    try:
        before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise OSError(errno.EINVAL, "expected nonsymlink regular file", path)
        descriptor = os.open(
            path.name, os.O_RDONLY | nofollow_flag(), dir_fd=parent
        )
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise OSError(errno.ESTALE, "file changed while opening", path)
        digest = hashlib.sha256()
        size = 0
        while block := os.read(descriptor, 1024 * 1024):
            digest.update(block)
            size += len(block)
        after = os.fstat(descriptor)
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise OSError(errno.ESTALE, "file changed while hashing", path)
        return digest.hexdigest(), size
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def fsync_regular_nofollow(path: Path) -> None:
    """Flush a regular file without following a final-component symlink."""

    parent = _open_parent_directory(path)
    descriptor = -1
    try:
        descriptor = os.open(
            path.name, os.O_RDONLY | nofollow_flag(), dir_fd=parent
        )
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(errno.EINVAL, "expected regular file for fsync", path)
        os.fsync(descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)
