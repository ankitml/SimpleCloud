# SimpleCloud

<img src = "./assets/cloud-computing.png"/>

Cloud storage made simple.

Features:
* No databases: the user registry is implemented through the server's UNIX users, along with their established permissions
* Stateless: no databases means no state. No state means no timeline inconsistencies.
* No re-invented protocols: SimpleCloud uses well-developed protocols to ensure connection, filesystem watching and syncing.
* Sync and stream: the user chooses, for each directory, how he wants to access it. SimpleCloud allows both syncing files from a client to a server or direct access to the server's storage.

Current state:

* The bash version (mount-remote.sh) has the basic functionality and can be used for most usecases. We're hoping to soon reproduce the Bash behaviour in Python and build upon that to solve a few issues and add features (such as a permanent task list).

Python dependencies:

* Watchdog: Filesystem watcher (http://pythonhosted.org/watchdog/)
* Pathtools: Pattern matching and various utilities for file systems paths (https://github.com/gorakhargosh/pathtools)
* Paramiko: SSH toolkit that allows SFTP mounting (http://docs.paramiko.org/en/1.17)/
* PySMB: SMB/CIFS mounting (https://pypi.python.org/pypi/pysmb)
