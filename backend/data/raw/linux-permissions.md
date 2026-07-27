# Linux File Permissions

## Overview

Linux file permissions control which users and groups can read, write, and execute files and directories. Every file and directory has an owning user and group, along with a permission mode expressed as three triads: owner, group, and others. Understanding permissions is essential for system security, multi-user environments, and correctly configuring applications.

## Details

### Permission Model

Each triad consists of three bits: read (`r`, value 4), write (`w`, value 2), and execute (`x`, value 1). Permissions are commonly represented in octal notation (e.g., `755`), where each digit is the sum of its bits. For directories, the execute bit grants the ability to traverse (enter) the directory, while read grants the ability to list its contents.

### chmod

The `chmod` command changes file permissions. It accepts either octal notation (`chmod 644 file.txt`) or symbolic notation (`chmod u+x file.sh`). Symbolic mode uses `u` (user/owner), `g` (group), `o` (others), and `a` (all), combined with `+`, `-`, or `=` to add, remove, or set permissions. The `-R` flag applies changes recursively.

### chown

The `chown` command changes the owner and/or group of a file. Basic usage: `chown user:group file`. The group can be omitted (`chown user file`) to change only the owner, or the colon can be used alone (`chown :group file`) to change only the group. Recursive changes use `-R`.

### umask

The `umask` command sets the default permission mask for newly created files and directories. It subtracts from the base permissions (666 for files, 777 for directories). A umask of `022` produces files with `644` and directories with `755`. The mask is typically set in shell startup files.

### Special Permissions

Three special permission bits modify behavior: SUID (setuid, octal 4000) runs an executable with the file owner's privileges; SGID (setgid, octal 2000) runs an executable with the group's privileges or, on directories, causes new files to inherit the directory's group; and the sticky bit (octal 1000) on directories restricts file deletion to the file owner, directory owner, or root (commonly used on `/tmp`).

## Examples

```bash
# Octal permission setting
chmod 755 script.sh      # rwxr-xr-x - owner can write, others can read/execute
chmod 644 document.txt   # rw-r--r-- - owner can write, others can only read
chmod 600 private.key    # rw------- - only owner can read/write

# Symbolic permission setting
chmod u+x script.sh      # Add execute for the owner
chmod go-w file.txt      # Remove write for group and others
chmod a+r file.txt       # Add read for everyone

# Changing ownership
sudo chown alice project.log          # Change owner to alice
sudo chown :developers app.jar         # Change group to developers
sudo chown alice:developers app.jar    # Change both
sudo chown -R alice:developers /opt/app  # Recursive change

# umask examples
umask 022   # Default on most systems: files 644, directories 755
umask 077   # Restrictive: files 600, directories 700
umask 002   # Permissive for group collaboration: files 664, directories 775

# Special permissions
chmod 4755 script.sh     # SUID: runs with owner privileges (setuid bit)
chmod 2755 directory/    # SGID: new files inherit group
chmod 1777 /tmp          # Sticky bit: only owners can delete their files
chmod u+s script.sh      # Symbolic SUID
chmod g+s directory/     # Symbolic SGID
chmod +t /tmp            # Symbolic sticky bit

# View permissions with stat or ls
stat -c "%a %A %U:%G %n" file.txt
ls -la
```

The SUID and SGID bits on executables pose security risks if misused — avoid setting them on custom scripts, especially shell scripts, as they are vulnerable to privilege escalation attacks.
