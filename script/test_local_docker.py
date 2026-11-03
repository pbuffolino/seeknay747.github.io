"""Synthetic boundary tests. No Docker daemon, network or private files are used."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("local_docker_gate", Path(__file__).with_name("check-local-docker.py"))
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class GateBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="jekyll-gate-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, name, kind=tarfile.REGTYPE):
        archive = self.root / "source.tar"
        with tarfile.open(archive, "w") as tar:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.linkname = "/outside"
            if kind == tarfile.REGTYPE:
                member.size = 4
                tar.addfile(member, io.BytesIO(b"text"))
            else:
                tar.addfile(member)
        return archive

    def test_archive_rejects_escape_links_and_special_files(self):
        for name, kind in [("../escape", tarfile.REGTYPE), ("/escape", tarfile.REGTYPE), ("link", tarfile.SYMTYPE), ("hard", tarfile.LNKTYPE), ("device", tarfile.CHRTYPE)]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(RuntimeError, "Unsafe"):
                    GATE.extract_source(self.archive(name, kind), self.root / "input")

    def test_archive_size_is_bounded(self):
        with patch.object(GATE, "MAX_SOURCE", 3):
            with self.assertRaisesRegex(RuntimeError, "bounded"):
                GATE.extract_source(self.archive("file"), self.root / "input")

    def test_git_archive_excludes_ignored_material_and_dirty_source_blocks(self):
        checkout = self.root / "repo"
        checkout.mkdir()
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        (checkout / ".gitignore").write_text("ignored.txt\n")
        (checkout / "public.txt").write_text("public synthetic source")
        (checkout / "ignored.txt").write_text("synthetic untracked sentinel")
        subprocess.run(["git", "-C", str(checkout), "add", ".gitignore", "public.txt"], check=True)
        subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture"], check=True)
        head = GATE.clean_head(checkout)
        archive = self.root / "git.tar"
        subprocess.run(["git", "-C", str(checkout), "archive", "--output", str(archive), head], check=True)
        GATE.extract_source(archive, self.root / "input")
        self.assertTrue((self.root / "input/public.txt").is_file())
        self.assertFalse((self.root / "input/ignored.txt").exists())
        self.assertFalse((self.root / "input/.git").exists())
        (checkout / "public.txt").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "Commit intended"):
            GATE.clean_head(checkout)

    def test_container_has_only_two_bounded_mounts_and_no_privilege(self):
        args = GATE.container_args("owned", "nonce", self.root / "input", self.root / "work", 1000, 1000)
        mounts = [args[i + 1] for i, value in enumerate(args) if value == "--mount"]
        self.assertEqual(len(mounts), 2)
        self.assertTrue(mounts[0].endswith("target=/input,readonly"))
        self.assertTrue(mounts[1].endswith("target=/work"))
        self.assertIn("--read-only", args)
        self.assertIn("no-new-privileges", args)
        self.assertEqual(args[args.index("--network") + 1], "bridge")
        self.assertEqual(args[args.index("--memory") + 1], "2g")
        self.assertEqual(args[args.index("--cpus") + 1], "2")
        self.assertFalse(any("docker.sock" in value for value in args))
        self.assertNotIn("--privileged", args)
        self.assertNotIn("--publish", args)
        self.assertEqual(args[args.index(GATE.IMAGE) + 1:args.index(GATE.IMAGE) + 4], ["nice", "-n", "10"])
        with self.assertRaisesRegex(RuntimeError, "nonroot"):
            GATE.container_args("owned", "nonce", self.root, self.root, 0, 0)

    def test_remote_docker_and_escaping_artifacts_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "local Unix"):
            GATE.require_local_docker("tcp://remote:2376")
        with self.assertRaisesRegex(RuntimeError, "local Unix"):
            GATE.require_local_docker("unix:///local.sock", "tcp://override:2376")
        work = self.root / "work"
        work.mkdir()
        outside = self.root / "outside"
        outside.write_text("synthetic")
        (work / "lock").symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, "escaping"):
            GATE.copy_artifact(work / "lock", self.root / "receipt", work)

    def test_cleanup_never_removes_a_different_owner(self):
        response = subprocess.CompletedProcess([], 0, json.dumps({GATE.LABEL: "someone-else"}), "")
        with patch.object(GATE.subprocess, "run", return_value=response), patch.object(GATE, "call") as mutate:
            with self.assertRaisesRegex(RuntimeError, "ownership"):
                GATE.cleanup_owned("container", "this-run")
            mutate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
