# SimpleCloud
A cloud solution that only requires a SSH/SFTP server and client-side bash, rsync, sshfs and inotify-tools

Moving to Rust:

> Use the rsnotify filesystem watcher for Rust, which is cross-platform and uses the best implementation for each OS (https://github.com/passcod/rsnotify)

> Mount directories through Rust-FUSE in Linux (https://github.com/zargony/rust-fuse/)

There doesn't seem to exist an implementation of SMB in Rust which is a big dealbreaker for Windows
