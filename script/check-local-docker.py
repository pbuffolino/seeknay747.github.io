#!/usr/bin/env python3
"""Explicit, bounded local Linux validation. No host policy or deployment changes."""
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import tarfile
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ruby@sha256:32ca6f94a3ffe387eb1b9d34edc4be8e9308da1c80a3dce8b7b8310d84949240"
PLATFORM = "linux/amd64"
TIMEOUT = 1200
MAX_WORK = 2 * 1024**3
MAX_SOURCE = 128 * 1024**2
LABEL = "com.seeknay.jekyll-local-gate"
DOCKER_ENDPOINT = None
PROXY_VARIABLES = tuple(value for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "FTP_PROXY", "NO_PROXY")
                        for value in (name, name.lower()))
COMMAND = r'''set -euo pipefail
mkdir -p /work/source /work/tmp /work/home /work/bootstrap
cp -R /input/. /work/source/
cd /work/source
ruby -e 'abort "Unexpected runtime" unless RUBY_VERSION == "3.3.13" && RUBY_PLATFORM.include?("linux")'
ruby -e 'names=%w[HTTP_PROXY HTTPS_PROXY ALL_PROXY FTP_PROXY NO_PROXY http_proxy https_proxy all_proxy ftp_proxy no_proxy]; abort "Ambient proxy environment refused" if names.any? { |name| ENV[name] && !ENV[name].empty? }'
ruby --version
bundle --version
bundle install --jobs 2 --retry 1
bundle list > /work/resolved-gems.txt
bash script/check-local.sh native
'''


def docker_args(args):
    if DOCKER_ENDPOINT is None:
        if args[1] != "context":
            raise RuntimeError("Validate a local Docker endpoint before operations")
        return args
    return ["docker", "--host", DOCKER_ENDPOINT, *args[1:]]


def docker_environment():
    if DOCKER_ENDPOINT is None:
        return dict(os.environ)  # Discovery only, never an engine operation.
    selectors = {"DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH", "BUILDX_BUILDER", "BUILDKIT_HOST", "DOCKER_BUILDKIT"}
    return {key: value for key, value in os.environ.items() if key not in selectors}


def docker_run(args, **kwargs):
    return subprocess.run(docker_args(args), env=docker_environment(), **kwargs)


def call(args, **kwargs):
    invoke = docker_run if args[0] == "docker" else subprocess.run
    return invoke(args, check=True, text=True, capture_output=True, timeout=60, **kwargs).stdout.strip()


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return call(["git", "-C", str(root), *args], env=env)


def clean_head(root):
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != Path(root).resolve():
        raise RuntimeError("Run from this repository's own Git checkout")
    if git(root, "status", "--porcelain", "--untracked-files=normal"):
        raise RuntimeError("Commit intended source and preserve unrelated changes before validation")
    return git(root, "rev-parse", "HEAD")


def require_local_docker(endpoint, override=None):
    if not endpoint.startswith("unix://") or (override and not override.startswith("unix://")):
        raise RuntimeError("This gate permits only a local Unix-socket Docker daemon")


def extract_source(archive, destination):
    """Reject links/special files and escapes; never project ignored host files."""
    total = 0
    with tarfile.open(archive) as tar:
        for member in tar:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts or not (member.isdir() or member.isfile()):
                raise RuntimeError("Unsafe Git archive member")
            total += member.size
            if total > MAX_SOURCE:
                raise RuntimeError("Source archive exceeds the bounded input size")
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o755)


def disk_bytes(root):
    total = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
        for name in files:
            try:
                total += (Path(directory) / name).lstat().st_size
            except FileNotFoundError:
                pass  # The package installer may retire its own temporary files.

    return total


def copy_artifact(source, target, work, required=False):
    if source.is_symlink():
        raise RuntimeError("Refusing an escaping or nonregular output artifact")
    if required and not source.exists():
        raise RuntimeError("Required dependency evidence is missing")
    if source.exists():
        if source.is_symlink() or not source.resolve().is_relative_to(work.resolve()) or not stat.S_ISREG(source.stat().st_mode) or source.stat().st_size > 8 * 1024**2:
            raise RuntimeError("Refusing an escaping or nonregular output artifact")
        shutil.copyfile(source, target)


def container_args(name, nonce, source, work, uid, gid):
    if uid <= 0:
        raise RuntimeError("The container must run as a nonroot user")
    if any("," in str(p) or "\n" in str(p) for p in (source, work)):
        raise RuntimeError("Mount paths cannot contain comma/newline separators")
    args = ["docker", "create", "--name", name, "--platform", PLATFORM,
            "--label", f"{LABEL}={nonce}", "--user", f"{uid}:{gid}",
            "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--cpus", "2", "--memory", "2g", "--memory-swap", "2g", "--pids-limit", "128",
            "--network", "bridge", "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--mount", f"type=bind,source={source},target=/input,readonly",
            "--mount", f"type=bind,source={work},target=/work", "--workdir", "/work"]
    for item in ["HOME=/work/home", "TMPDIR=/work/tmp", "GEM_HOME=/work/bootstrap",
                 "GEM_PATH=/work/bootstrap:/usr/local/lib/ruby/gems/3.3.0:/usr/local/bundle",
                 "BUNDLE_PATH=/work/gems", "BUNDLE_USER_HOME=/work/bundle-user",
                 "BUNDLE_APP_CONFIG=/work/bundle-config", "BUNDLE_IGNORE_CONFIG=true",
                 "BUNDLE_JOBS=2", "BUNDLE_RETRY=1", "BUNDLE_TIMEOUT=20", "MAKEFLAGS=-j2"]:
        args.extend(["--env", item])
    for variable in PROXY_VARIABLES:
        args.extend(["--env", variable + "="])
    return args + [IMAGE, "nice", "-n", "10", "bash", "-c", COMMAND]


def cleanup_owned(identifier, nonce):
    result = docker_run(["docker", "inspect", "--format", '{{json .Config.Labels}}', identifier],
                        capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        if json.loads(result.stdout).get(LABEL) != nonce:
            raise RuntimeError("Refusing to remove a container without this run's ownership label")
        call(["docker", "rm", "--force", identifier])
    # A successful removal acknowledgement alone is not final absence evidence.
    absent = docker_run(["docker", "ps", "-aq", "--no-trunc", "--filter", f"label={LABEL}={nonce}"],
                        capture_output=True, text=True, timeout=15)
    if absent.returncode or absent.stdout.strip():
        raise RuntimeError("Cannot establish owned-container cleanup")


def evidence_base(root):
    root = root.resolve()
    vendor, base = root / "vendor", root / "vendor/local-checks"
    if vendor.is_symlink() or base.is_symlink() or not base.resolve().is_relative_to(root):
        raise RuntimeError("Evidence root must remain inside the owning checkout without symlink indirection")
    return base


def check_bounds(work, log, started, now=None):
    elapsed = (time.monotonic() if now is None else now) - started
    if elapsed > TIMEOUT:
        raise RuntimeError("Local container gate exceeded its time bound")
    if disk_bytes(work) > MAX_WORK or log.stat().st_size > 32 * 1024**2:
        raise RuntimeError("Local gate exceeded its owned scratch/log size bound")


def validate_terminal_state(state):
    if (state.get("Status") != "exited" or state.get("Running") is not False
            or state.get("OOMKilled") is not False or state.get("Dead") is not False
            or state.get("Error") not in (None, "")
            or type(state.get("ExitCode")) is not int or state["ExitCode"] != 0):
        raise RuntimeError("Container did not reach a clean exited state")


def retire_inputs(run, source, archive, container_absent):
    if not container_absent:
        return False  # Retain every mounted input for exact-handle recovery.
    if source.parent != run or archive.parent != run or source.is_symlink():
        raise RuntimeError("Refusing staging cleanup outside this run")
    shutil.rmtree(source)
    archive.unlink(missing_ok=True)
    return True


def reap_client(process):
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)


def main():
    global DOCKER_ENDPOINT
    head = clean_head(ROOT)
    context = call(["docker", "context", "show"])
    endpoint = call(["docker", "context", "inspect", context, "--format", '{{.Endpoints.docker.Host}}'])
    override = os.environ.get("DOCKER_HOST")
    require_local_docker(endpoint, override)
    DOCKER_ENDPOINT = endpoint if os.environ.get("DOCKER_CONTEXT") or not override else override
    if shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise RuntimeError("Local validation needs at least 5 GiB available; no cleanup is automatic")
    base = evidence_base(ROOT)
    call(["git", "-C", str(ROOT), "check-ignore", "--quiet", str(base)])
    base.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="gate-", dir=base))
    source, work = run / "input", run / "work"
    source.mkdir(); work.mkdir()
    nonce = uuid.uuid4().hex
    name = "jekyll-local-" + nonce
    receipt = {"source_sha": head, "platform": PLATFORM, "image": IMAGE,
               "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "timeout_seconds": TIMEOUT, "max_work_bytes": MAX_WORK,
               "cpus": 2, "memory": "2g", "source_input": "clean git archive; read-only mount",
               "container_name": name, "local_docker_endpoint": DOCKER_ENDPOINT, "pass": False}
    process = None
    identifier = name
    code = 1
    checks_completed = False
    archive = run / "source.tar"
    try:
        try:
            image = json.loads(call(["docker", "image", "inspect", IMAGE]))[0]
        except subprocess.CalledProcessError:
            with (run / "image-pull.log").open("w") as log:
                docker_run(["docker", "pull", "--platform", PLATFORM, IMAGE], check=True,
                               stdout=log, stderr=subprocess.STDOUT, timeout=300)
            image = json.loads(call(["docker", "image", "inspect", IMAGE]))[0]
        if image["Os"] != "linux" or image["Architecture"] != "amd64" or IMAGE not in image["RepoDigests"]:
            raise RuntimeError("Pinned image identity/platform mismatch")
        receipt["image_config_id"] = image["Id"]
        sizes = git(ROOT, "ls-tree", "-rl", head).splitlines()
        total = sum(int(line.split("\t", 1)[0].split()[-1]) for line in sizes if line.split("\t", 1)[0].split()[-1].isdigit())
        if total > MAX_SOURCE or len(sizes) > 50000:
            raise RuntimeError("Tracked source exceeds the bounded archive input")
        archive = run / "source.tar"
        with archive.open("wb") as output:
            subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", head], check=True,
                           stdout=output, timeout=60)
        if archive.stat().st_size > 2 * MAX_SOURCE:
            raise RuntimeError("Git archive exceeds its input size bound")
        receipt["source_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        extract_source(archive, source)
        args = container_args(name, nonce, source, work, os.getuid(), os.getgid())
        identifier = call(args)
        if not re.fullmatch(r"[a-f0-9]{64}", identifier):
            raise RuntimeError("Invalid created-container identity")
        receipt["container_id"] = identifier
        with (run / "gate.log").open("w") as log:
            process = subprocess.Popen(docker_args(["docker", "start", "--attach", identifier]), stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True, env=docker_environment())
            receipt["client_pid"] = process.pid
            started = time.monotonic()
            while process.poll() is None:
                check_bounds(work, run / "gate.log", started)
                time.sleep(2)
        # Recheck after exit: a process can cross a limit between polling ticks.
        check_bounds(work, run / "gate.log", started)
        if process.returncode:
            raise RuntimeError("Local container gate failed; inspect retained gate.log")
        state = json.loads(call(["docker", "inspect", "--format", '{{json .State}}', identifier]))
        validate_terminal_state(state)
        receipt["terminal_state"] = {key: state[key] for key in ("Status", "Running", "ExitCode", "OOMKilled", "Dead")}
        code = 0
        if clean_head(ROOT) != head:
            raise RuntimeError("Source changed during validation; new-head evidence is required")
        checks_completed = True
    except Exception as error:
        receipt["error"] = str(error)
        code = code or 1
    finally:
        absent = False
        try:
            cleanup_owned(identifier, nonce)
            absent = True
            receipt["owned_container_removed"] = True
        except Exception as error:
            receipt["cleanup_error"] = str(error); code = 1
            receipt["owned_container_removed"] = False
            receipt["retained_recovery_path"] = str(run)
        try:
            reap_client(process)
            receipt["client_reaped"] = True
        except Exception as error:
            receipt["client_reap_error"] = str(error); code = 1; absent = False
            receipt["retained_recovery_path"] = str(run)
        if absent:
            try:
                copy_artifact(work / "source/Gemfile.lock", run / "Gemfile.lock", work, checks_completed)
                copy_artifact(work / "resolved-gems.txt", run / "resolved-gems.txt", work, checks_completed)
                receipt["staging_removed"] = retire_inputs(run, source, archive, True)
            except Exception as error:
                receipt["artifact_or_staging_error"] = str(error); code = 1
        else:
            receipt["staging_removed"] = retire_inputs(run, source, archive, False)
        receipt["pass"] = checks_completed and code == 0 and absent and receipt.get("staging_removed") is True
        receipt["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt["exit_code"] = code
        (run / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Local Linux validation {'PASS' if receipt['pass'] else 'BLOCKED'}: {run / 'receipt.json'}")
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.SubprocessError) as error:
        print(f"Local Docker validation blocked: {error}")
        raise SystemExit(1)
