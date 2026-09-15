# Fleet install: shared hosts and virtual desktops

How to deploy ClawMetry silently to multi-session Windows hosts, pooled
virtual desktop images and shared Linux hosts.

Status: verified on GitHub Actions Windows and Ubuntu runners
(`.github/workflows/fleet-install-test.yml`). **It has not been validated on a
real Azure Virtual Desktop or other multi-session host.** Treat the Windows
multi-session behaviour below as designed and CI-verified at registration
level, not field-proven.

## The profile we chose: one collector per user

The collector reads agent files that live in each user's profile
(`~/.claude`, `~/.codex`, ...) and keeps a local store holding that user's
session content. So it runs **as each user**, never as a privileged account:

| | Linux | Windows |
|---|---|---|
| Registration | per-user systemd unit, plus logind linger | one machine-wide logon task for `BUILTIN\Users` (`--all-users`) |
| Runs as | the user | each signed-in user, least privilege, one instance per session |
| After logoff | keeps running (linger) | stops with the session; resumes at next sign-in from data already on disk |
| Data | `~/.clawmetry`, restricted to the user (0700) | `%USERPROFILE%\.clawmetry`, profile ACL |

A single SYSTEM service reading every profile was rejected: it could read every
user's content, and it would attribute all of it to one node.

Check what you actually got on any host:

```
clawmetry service status          # add --json for scripts
```

It reports whether collection survives logoff and why, and whether the data
directory is private. It never reports `survives_logoff: true` on Windows.

## Windows (Intune, image build, GPO)

`intune/Install-ClawMetry.ps1` runs elevated (Intune platform scripts run as
SYSTEM). It creates `C:\Program Files\ClawMetry\venv`, installs the package you
pin, and runs `clawmetry service install --all-users`.

```
powershell.exe -ExecutionPolicy Bypass -NoProfile -File Install-ClawMetry.ps1 -Package "clawmetry==<version>"
```

Exit code 0 means the task is registered; 1 means it is not.

`-PythonExe` must be a machine-wide interpreter every user can read (for
example one installed for all users under `C:\Program Files`). A virtual
environment runs through the interpreter it was created from, so a Python
installed in one user's profile would break every other user's collector; the
script refuses one. The task starts `python.exe`, a console program, so each
user may see a console window at sign-in, and closing it stops collection
until the next sign-in. This has not been checked on a real multi-session
host.

Uninstall:

```
& "$env:ProgramFiles\ClawMetry\venv\Scripts\clawmetry.exe" service uninstall
Remove-Item -Recurse -Force "$env:ProgramFiles\ClawMetry"
```

`clawmetry uninstall` also removes both the per-user and the all-users task
(the all-users one needs an elevated prompt, and says so if it could not).

## Linux (Ansible)

`ansible/clawmetry.yml` creates `/opt/clawmetry-fleet`, installs the pinned
package, enables linger for each listed user and runs `clawmetry service install`
as each of them.

```
ansible-playbook -i inventory deploy/fleet/ansible/clawmetry.yml \
  -e '{"clawmetry_users": ["alice", "bob"]}' -e clawmetry_package=clawmetry==<version>
```

A single user can do the same by hand: `clawmetry service install`. If polkit
refuses linger, the command exits 1 and prints the administrator command
(`sudo loginctl enable-linger <user>`) rather than pretending the collector will
outlive logout.

## Pin, update, rollback

* Pin: pass an exact `clawmetry==<version>` to either recipe.
* Every user's collector runs code from the one shared environment, so both
  recipes make sure no desktop user can write it: the Ansible playbook
  installs under `umask 022` and then enforces root ownership and
  `u=rwX,go=rX`, and the Intune script sets an explicit ACL on the install
  directory (SYSTEM and Administrators full control, Users read and execute).
  If you install some other way, check this yourself: a user who can write the
  environment can run code as every other user on the host.
* Both recipes install into a location only an administrator can write
  (`C:\Program Files\ClawMetry\venv`, `/opt/clawmetry-fleet`). A collector
  running from such a location **never updates itself**: it detects that the
  signed-in user cannot write its install and skips automatic updates, so it
  never exits to retry an upgrade that cannot succeed. `clawmetry service status`
  reports `Auto-update: off` with that reason. You do not need to set
  anything for this.
* Update: re-run the recipe with the new pin. Collectors pick up the new code
  at their next start (Windows: next sign-in; Linux: restart each user's
  `clawmetry-sync` unit or reboot).
* Roll back by re-running the recipe with the previous pin.
* A per-user install the user owns (for example `pip install --user`) keeps
  the normal automatic updates; `CLAWMETRY_AUTO_UPDATE=0` turns them off.

## Enrollment credentials

Neither recipe enrolls hosts with ClawMetry Cloud or accepts a key, and a test
fails if a key-shaped string appears in them. Local-only collection works with
no credential at all.

If you connect to Cloud, run `clawmetry connect --key <key>` **as each user at
sign-in** from a user-context deployment step that reads the key from your
secret store, and never write it into the image, a script file or a
world-readable location. Today's key is account scoped; rotate it by
connecting again with the new key. Scoped, per-host enrollment keys are not
available yet.

## Proxy, custom CA and offline

Reuse what already exists: `HTTPS_PROXY`, `CLAWMETRY_CA_BUNDLE` for a corporate
root CA, and `CLAWMETRY_OFFLINE=1` for no outbound traffic. See
[`docs/EGRESS.md`](../../docs/EGRESS.md).

## Not covered yet

* A collector for users who are not signed in on Windows.
* Guaranteed buffering through long network outages (capped, recoverable queue).
* Scoped, rotatable enrollment keys, and a guaranteed fresh node identity for
  pooled image clones.
* Measured overhead on a real virtual desktop image. The CI workflow records
  idle CPU, memory and disk on the runner in its job summary as a reference
  point only.
