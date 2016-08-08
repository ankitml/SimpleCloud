# SimpleCloud

<img src = "./assets/cloud-computing.png"/>

Cloud storage made simple.

# Features:
* No databases: the user registry is implemented through the server's UNIX users, along with their established permissions
* Stateless: no databases means no state. No state means no timeline inconsistencies.
* No re-invented protocols: SimpleCloud uses well-developed protocols to ensure connection, filesystem watching and syncing.
* Sync and stream: the user chooses, for each directory, how he wants to access it. SimpleCloud allows both syncing files from a client to a server or direct access to the server's storage.
* Minimal server dependencies: all of the work is done on the client. The server is only expected to posess a user system and the ability to create a filesystem connection through either SMB or SSH.

# Current state:

* The bash version (mount-remote.sh) has the basic functionality and can be used for most usecases. We're hoping to soon reproduce the Bash behaviour in Python and build upon that to solve a few issues and add features (such as a permanent task list).
* We're moving to Unison as a main file synchronizer and filesystem watcher!

## Python dependencies:

* Watchdog: Filesystem watcher (http://pythonhosted.org/watchdog/)
* Pathtools: Pattern matching and various utilities for file systems paths (https://github.com/gorakhargosh/pathtools)
* Paramiko: SSH toolkit that allows SFTP mounting (http://docs.paramiko.org/en/1.17)/
* PySMB: SMB/CIFS mounting (https://pypi.python.org/pypi/pysmb)

## Unison:
Unison will be the core of SimpleCloud. Since the last version (2.48) made large improvements on overall functionality, especially the filewatcher, and since it's rarely available on default repositories, here are the instructions for compiling from source:
* Clone the source code:

`git clone https://github.com/bachp/Unison.git`
* Install all dependencies:

`sudo dnf ocaml ctags ctags-etag redhat-rpm-config`
* Build:

`make`
`sudo cp src/unison* /usr/local/bin/`
* If you get the following error:

`Fatal error: exception Scanf.Scan_failure("scanf: bad input at char number 4: 'looking for ':', found '$''")`
Edit src/mkProjectInfo.ml from `let revisionString = "$Rev$";;` to `let revisionString = "$Rev: 388$";;`
[Source](http://lists.seas.upenn.edu/pipermail/unison-hackers/2010-January/001219.html)
