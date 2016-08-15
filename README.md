# SimpleCloud

<img src = "./assets/cloud-computing.png"/>

Cloud storage made simple.

## Features:
* No databases: the user registry is implemented through the server's UNIX users, along with their established permissions
* Stateless: no databases means no state. No state means no timeline inconsistencies.
* No re-invented protocols: SimpleCloud uses well-developed protocols to ensure connection, filesystem watching and syncing.
* Sync and stream: the user chooses, for each directory, how he wants to access it. SimpleCloud allows both syncing files from a client to a server or direct access to the server's storage.
* Minimal server dependencies: all of the work is done on the client. The server is only expected to posess a user system and the ability to create a filesystem connection through either SMB or SSH.

## Current state:

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

`$ git clone https://github.com/bachp/Unison.git`
* Install all dependencies:

`# dnf install ocaml ctags ctags-etag redhat-rpm-config`
* Build:

`$ make`<br />
`sudo cp src/unison* /usr/local/bin/`
* If you get the following error:

`Fatal error: exception Scanf.Scan_failure("scanf: bad input at char number 4: 'looking for ':', found '$''")`
Edit src/mkProjectInfo.ml from `let revisionString = "$Rev$";;` to `let revisionString = "$Rev: 388$";;`

[Source](http://lists.seas.upenn.edu/pipermail/unison-hackers/2010-January/001219.html)

## Preparing and encrypting the storage
Sources and further reading:<br />
   https://wiki.archlinux.org/index.php/Dm-crypt/Device_encryption
   https://www.digitalocean.com/community/tutorials/how-to-use-dm-crypt-to-create-an-encrypted-volume-on-an-ubuntu-vps

On this guide we're assuming the server's system and the storage are physically separate. On our case the system is on a 60GB SSD while all the data is on a 1TB HDD. If you're using a brand new disk for storage it should be empty, but it's always good practice to clean it.
### Finding the storage device
Either log in locally or by SSH onto your server, then find out which disk is which through lshw

`# dnf install lshw`<br />
`# lshw -class disk`

This will list all the storage devices attached to your system, including model, manufacturer, capacity. You can compliment this with 

`$ lsblk`

Which will list partitions and mountpoints from each device. Note down which is your storage disk. On our case it's sda.

### Clean the device
Understand that any contents you currently have on the storage disk will be unretrievable after this step. I like to use shred, since it's made to actually shred files and devices.

`shred -vzn 0 /dev/sda`

You can also use dd:

`# dd if=/dev/zero of=/dev/sda bs=10M status=progress`<br />
`2621440000 bytes (2.6 GB, 2.4 GiB) copied, 11.0281 s, 238 MB/s` => this line gets updated<br />
`95387+0 records in`
`95386+0 records out`<br />
`1000204886016 bytes (1.0 TB, 932 GiB) copied, 6244.26 s, 160 MB/s`

This will read a stream of bytes containing only 0's into the storage drive. Again, please make sure to use the correct drive path. This process takes a long time for a 1TB drive (in our case 6244 seconds, which is about 1h 45m). The bs=10M specifies that it should read 10 Megabyte blocks at a time and write them to the drive, which speeds things up at the expense of RAM. If you're serious about your security you can use of=/dev/urandom or even /dev/random instead, which read pseudo-random bytes instead of just zeros, but in turn it takes quite a while longer.

### Encrypt the storage
(If you want, you can use this steps without root permissions by using the command `chown <your username> /dev/sda`)

By now the storage device, which in our case was /dev/sda, should contain only 0's. Many guides work on the assumption that we want to create one file inside a partition to use as an encrypted container, or to encrypt a partition. In this case we chose to have an entire hard drive dedicated to storage and encrypted, so we'll skip a few steps that you'd have to do in those instances. If you're working with a single storage device, you'll probably want your encrypted storage sitting on an already-existing partition, in that case check out the very well-written Digital Ocean guide below. We can easily encrypt it with cryptsetup.

`# cryptsetup -yv luksFormat /dev/sda`

This step takes a few seconds. it will prompt you for a password (twice, since we used the -y flag). When it's done, the hard drive has been formatted as a LUKS filesystem, which means files introduced will automatically be encrypted, and files read will be decrypted. Confirm this with another crypsetup command:

`$ cryptsetup luksDump /dev/sda`<br />
`Version:       	1`<br />
`Cipher name:   	aes`<br />
`Cipher mode:   	xts-plain64`<br />
`Hash spec:     	sha256`<br />
`Payload offset:	4096`


LUKS surrounds an existing filesystem device with encryption, you essentially open a LUKE device to reveal a filesystem inside it. So we'll need to create one. For that, let's start by opening our container:

`# crypsetup luksOpen /dev/sda things`

The decrypted device /dev/mapper/things will be created. This isn't an actual physical device, that was the /dev/sda disk, it's just the contents of the LUKS filesystem, which so far contain nothing. Let's create an ext4 filesystem inside.

`# mkfs -t ext4 /dev/mapper/things`

Finally, an optional step: Linux filesystems are by default created with about 5% space reserved. This made sense in the 90's for system drives where your space was very limited since filling up a drive entirely might render the system unusable, but for a 1TB drive that only serves as backup, it's irrelevant. So we can set the reserved space to 0:

`tune2fs -m 0 /dev/mapper/things`

### Opening and closing the encrypted device
Crytpsetup containers can sometimes freeze doing I/O, and you won't be able to close them while a process is accessing them.

`# cryptsetup close things`<br />
`device-mapper: remove ioctl on things failed: Device or resource busy` => this line gets repeated a lot<br />
`Device things is still in use.`

To do this you need to find the PID for that process and kill it.

`# dmsetup ls`

This returns something like 

`things	(253:0)`

Next find the process responsible:

`# lsof | grep 253,0`

The second column contains the PID. Just kill it with the aptly-named command kill:

`# kill -9 <PID>`

And now you sould be able to close the container:

`# cryptsetup close things`
