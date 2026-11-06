"""The dataset fetcher must handle multi-source corpora and stay rerunnable.

Regression guard: the previous single-URL layout silently produced zero ham
because the "SpamAssassin tarball" was actually a directory listing page.
"""
from __future__ import annotations

import io
import tarfile
from pathlib import Path

from training import download_datasets


def _tar_bz2(name: str, payload: bytes) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:bz2") as tf:
        info = tarfile.TarInfo(name)
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


def test_multi_source_download_writes_manifest(tmp_path, monkeypatch):
    mbox = b"From: a@example.test\nSubject: hi\n\nbody one\n"
    ham_tar = _tar_bz2("easy_ham/0001.txt", b"From: b@example.test\nSubject: ham\n\nbody two\n")
    monkeypatch.setattr(download_datasets, "DATASETS", {
        "mix": [("https://example.test/a.mbox", "a.mbox"),
                ("https://example.test/ham.tar.bz2", "ham.tar.bz2")],
    })

    fetched: list[str] = []

    def fake_fetch(url: str, dest: Path) -> None:
        fetched.append(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(mbox if url.endswith(".mbox") else ham_tar)

    monkeypatch.setattr(download_datasets, "_fetch", fake_fetch)

    manifest = download_datasets.download_dataset("mix", tmp_path)
    assert len(fetched) == 2
    assert manifest["count"] == 2
    assert (tmp_path / "mix" / "easy_ham" / "0001.txt").exists()

    # Second run is idempotent: existing corpus wins, nothing refetched.
    fetched.clear()
    again = download_datasets.download_dataset("mix", tmp_path)
    assert fetched == []
    assert again["count"] == 2
