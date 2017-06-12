# SimpleCloud

<img src = "./assets/cloud-computing.png"/>

Cloud storage made simple.

## Current state:
* SimpleCloud is on a development hiatus. I develop it alone and currently have very little free time.
* The current codebase is not working yet.
* The Registry is currently the most work-demanding component. We're going with Paramiko and the selectors module to asynchronously monitor each channel. ~~We're trying to adapt an async mechanism (async-ssh) for it for maximum efficiency, but it's proving to be very demanding, and there's almost nothing to base it on. It's also a very language-specific implementation. If this drags on, a one-thread-per-client Registry will be developed as a temporary solution using Paramiko. **Also the latest testing showed that async-ssh is unable to notice when a SSH channel has been improperly closed, which would be a dealbreaker to its use**~~

## Features:
We aim to create a simple cloud storage solution that doesn't reinvent the wheel. Almost all cloud storage systems run on an operating system with user lists, permissions and filesystems built into it and then add their own users, their own permissions and their own filesystems. This not only makes room for inconsistencies that have to be fixed manually, but it also generates useless overhead that affects performance. SimpleCloud exists to fix this.
* **Server-side alterations:** unlike almost every other cloud storage, SimpleCloud allows the server itself to add and alter files and have those changes propagated to clients. You can have files downloading and transfered to a user folder when they're done, knowing they'll be available on the client.
* **No databases:** there are no SimpleCloud users, only system users. There are no SimpleCloud directories, only system directories. There are no redundant records.
* **Stateless:** no databases means no permanent state which means no inconsistencies. Everytime you start SimpleCloud it starts fresh, regardless of what changed since you shut it down.
* **No new protocols:** SimpleCloud uses the stable, industry leading protocol SSH to ensure security and stability in connections, made by people much smarter and experient at cryptography than us. You can choose what sort of authentication to use, and you can re-use your existing public key.
* **Sync and stream:** the user chooses, for each directory, how he wants to access it. SimpleCloud allows both syncing files from a client to a server or directly accessing the server's storage from the client.
* **Minimal server dependencies:** all of the work is done on the client. The server is only expected to posess a user system and the ability to create a network filesystem connection (FUSE) through either SMB or SSH.

## Python dependencies:
* Watchdog: Filesystem watcher (http://pythonhosted.org/watchdog/)
* Pathtools: Pattern matching and various utilities for file systems paths (https://github.com/gorakhargosh/pathtools)
* Paramiko: SSH toolkit that allows SFTP mounting (http://docs.paramiko.org/en/1.17)/
   * To install Paramiko on Red Hat systems you'll need the packages openssl-devel, python-devel and libffi-devel, and pip install paramiko will need to be ran with root permissions
* async-ssh: asynchronous SSH toolkit, currently replacing Paramiko+threads

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
