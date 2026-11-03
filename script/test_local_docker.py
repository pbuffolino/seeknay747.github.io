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
        endpoint = patch.object(GATE, "DOCKER_ENDPOINT", "unix:///fixture.sock")
        endpoint.start()
        self.addCleanup(endpoint.stop)

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
        # Ambient selectors must not redirect the binary archive operation.
        with patch.dict(GATE.os.environ, {"GIT_DIR": str(self.root / "unrelated.git"),
                                         "GIT_WORK_TREE": str(self.root / "unrelated-tree")}):
            self.assertEqual(GATE.clean_head(checkout), head)
            GATE.archive_source(checkout, head, archive)
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

    def test_final_bounds_reject_finished_over_budget_work(self):
        work = self.root / "work"
        work.mkdir()
        log = self.root / "gate.log"
        log.write_text("")
        with self.assertRaisesRegex(RuntimeError, "time bound"):
            GATE.check_bounds(work, log, 0, GATE.TIMEOUT + 1)
        (work / "large").write_bytes(b"data")
        with patch.object(GATE, "MAX_WORK", 3):
            with self.assertRaisesRegex(RuntimeError, "size bound"):
                GATE.check_bounds(work, log, 0, 1)
        with log.open("wb") as stream:
            stream.truncate(32 * 1024**2 + 1)
        with self.assertRaisesRegex(RuntimeError, "size bound"):
            GATE.check_bounds(work, log, 0, 1)

    def test_evidence_root_refuses_symlink_escape_before_creation(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (checkout / "vendor").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "Evidence root"):
            GATE.evidence_base(checkout)
        self.assertFalse((outside / "local-checks").exists())

    def test_uncertain_cleanup_retains_every_mounted_input(self):
        source = self.root / "input"
        source.mkdir()
        (source / "source.txt").write_text("synthetic")
        archive = self.root / "source.tar"
        archive.write_bytes(b"synthetic archive")
        self.assertFalse(GATE.retire_inputs(self.root, source, archive, False))
        self.assertTrue((source / "source.txt").is_file())
        self.assertTrue(archive.is_file())

    def test_zero_exit_code_without_terminal_clean_state_never_passes(self):
        good = {"Status": "exited", "Running": False, "OOMKilled": False, "Dead": False, "Error": "", "ExitCode": 0}
        GATE.validate_terminal_state(good)
        for different in [{"Status": "running", "Running": True}, {"Status": "created"}, {"OOMKilled": True}, {"Error": "runtime failure"}, {"ExitCode": 1}, {"ExitCode": False}]:
            with self.subTest(different=different):
                with self.assertRaisesRegex(RuntimeError, "clean exited"):
                    GATE.validate_terminal_state({**good, **different})

    def test_every_docker_operation_pins_daemon_and_strips_selectors(self):
        with patch.dict(GATE.os.environ, {"DOCKER_CONTEXT": "remote", "DOCKER_HOST": "tcp://remote:2376", "DOCKER_CERT_PATH": "/not-mounted"}):
            self.assertEqual(GATE.docker_args(["docker", "image", "inspect", "fixture"])[:3], ["docker", "--host", "unix:///fixture.sock"])
            self.assertNotIn("DOCKER_CONTEXT", GATE.docker_environment())
            self.assertNotIn("DOCKER_HOST", GATE.docker_environment())
            self.assertNotIn("DOCKER_CERT_PATH", GATE.docker_environment())
        with self.assertRaisesRegex(RuntimeError, "local Unix"):
            GATE.require_local_docker("tcp://context:2376", "unix:///host.sock")

    def test_required_dependency_receipt_cannot_silently_disappear(self):
        with self.assertRaisesRegex(RuntimeError, "evidence is missing"):
            GATE.copy_artifact(self.root / "missing", self.root / "receipt", self.root, True)

    def test_client_proxy_configuration_cannot_enter_container(self):
        args = GATE.container_args("owned", "nonce", self.root / "input", self.root / "work", 1000, 1000)
        values = [args[i + 1] for i, item in enumerate(args) if item == "--env"]
        for variable in GATE.PROXY_VARIABLES:
            self.assertIn(variable + "=", values)
        self.assertIn("Ambient proxy environment refused", GATE.COMMAND)

    def test_actual_failure_receipt_is_durable_before_docker_create(self):
        receipt_file = self.root / "receipt.json"
        record = GATE.OwnedReceipt(receipt_file)
        report = {"pass": False, "exit_code": 1, "container_name": "owned",
                  "ownership_nonce": "nonce", "local_docker_endpoint": "unix:///fixture.sock",
                  "source_sha": "synthetic-head", "staging_path": str(self.root)}
        def create(args):
            self.assertEqual(args, ["docker", "create", "fixture"])
            self.assertEqual(json.loads(receipt_file.read_text()), report)
            self.assertEqual(receipt_file.stat().st_mode & 0o777, 0o600)
            return "fixture-id"
        with patch.object(GATE, "call", side_effect=create), patch.object(GATE.os, "fsync", wraps=GATE.os.fsync) as sync:
            self.assertEqual(GATE.create_container(["docker", "create", "fixture"], record, report), "fixture-id")
            sync.assert_called_once()
        record.finalize({**report, "pass": True, "exit_code": 0})
        self.assertTrue(json.loads(receipt_file.read_text())["pass"])

    def test_unknown_receipt_replacement_edit_or_symlink_is_not_overwritten(self):
        for mutation in ("replacement", "edit", "symlink"):
            with self.subTest(mutation=mutation):
                receipt_file = self.root / (mutation + ".json")
                record = GATE.OwnedReceipt(receipt_file)
                record.prepare({"pass": False})
                other = self.root / (mutation + ".other")
                other.write_text("unrelated evidence")
                if mutation == "replacement":
                    other.replace(receipt_file)
                elif mutation == "edit":
                    receipt_file.write_text("unrelated evidence")
                else:
                    receipt_file.unlink()
                    receipt_file.symlink_to(other)
                with self.assertRaises((RuntimeError, OSError)):
                    record.finalize({"pass": True})
                self.assertEqual(receipt_file.read_text(), "unrelated evidence")


if __name__ == "__main__":
    unittest.main()
