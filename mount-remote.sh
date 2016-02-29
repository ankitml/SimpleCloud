#!/bin/bash
REMOTE_USERNAME="francisco"
LOCAL_ROOT="/home/francisco/"
SYNC_ROOT="/home/francisco/.Simplecloud/"
#REMOTE_ADDRESS="192.168.1.91"
REMOTE_ADDRESS="95.95.67.48"
REMOTE_CONTAINER="/mnt/things/"
DIRECT_DIRECTORIES=("Music" "Pictures" "Torrents" "Videos")
SYNC_DIRECTORIES=("Documents")
#SYNC_DIRECTORIES=("Torrents")
RSYNC_OPTIONS="-rltuv --progress --exclude=\".Trash*\""
SSHFS_OPTIONS="-o password_stdin -o allow_other -o reconnect -o ServerAliveInterval=60"
EXCLUDE_FROM_SYNC="( *.goutputstream-* | *.swp | *\~ )"

function mount-direct-dirs {
	for directory in "${DIRECT_DIRECTORIES[@]}"
	do
		echo "Mounting $directory in /home/francisco/$directory"
		echo $REMOTE_PASSWORD | sshfs "$REMOTE_USERNAME"@"$REMOTE_ADDRESS":"$REMOTE_CONTAINER""$directory" /home/francisco/"$directory" $SSHFS_OPTIONS
	done
}

function mount-sync-dirs {
	for directory in "${SYNC_DIRECTORIES[@]}"
	do
		echo "Mounting $directory in /home/francisco/."$directory"-remote"
		if [ ! -d "$SYNC_ROOT""$directory" ]
		then
			mkdir "$SYNC_ROOT""$directory"
		fi
		echo $REMOTE_PASSWORD | sshfs "$REMOTE_USERNAME"@"$REMOTE_ADDRESS":"$REMOTE_CONTAINER""$directory" "$SYNC_ROOT""$directory" $SSHFS_OPTIONS
		MOUNTSTATUS=${PIPESTATUS[1]}
		if [ "$MOUNTSTATUS" -ne 0 ]
		then
			echo "Unsuccessful mount"
			#exit 1
		fi
	done
}

function initial-sync {
	:
}

function sync-sleep {
	while [ "$MOUNTSTATUS" -eq 0 ]
	do
		for directory in "${SYNC_DIRECTORES[@]}"
		do
			#pull
			rsync $RSYNC_OPTIONS /home/francisco/."$directory"-remote/ /home/francisco/"$directory"/
			#push
			rsync $RSYNC_OPTIONS --delete /home/francisco/"$directory"/ /home/francisco/."$directory"-remote/
			echo "Sleeping 10"
			sleep 10
		done
	done
}

function sync-watch {
	# Start a cycle that reads each filesystem notification
	inotifywait -m -r -e create,delete,modify,attrib,move  --format "%T %e %w%f" --timefmt "%d/%m/%y %T" --exclude "$EXCLUDE_FROM_SYNC" $LOCAL_ROOT${SYNC_DIRECTORIES[*]} $SYNC_ROOT${SYNC_DIRECTORIES[*]} | while read NOTIFICATION
	do
		# For each filesystem notification extract its timestamp,
		# event string, path to the file/dir that caused the notification
		# and get the equivalent file/dir for syncing
		NOTIFICATION_LIST=($NOTIFICATION)
		TIME=${NOTIFICATION_LIST[0]}" "${NOTIFICATION_LIST[1]}
		EVENT=${NOTIFICATION_LIST[2]}
		SOURCE=$(echo "$NOTIFICATION" | sed "s#\($EVENT\|$TIME\)##g" | sed "s#^[[:space:]]*##g")
		if [[ -d $SOURCE ]]
		then
			SOURCE="$SOURCE""/"
		fi
		DESTINATION=$(get-destination "$SOURCE")
		echo -e "Time: $TIME \nEvent: $EVENT\nFile: $SOURCE\nDestination: $DESTINATION"
		
		case $EVENT in
		# The file/dir was either moved deleted from a watched directory
		MOVED_FROM* | DELETE*)
			# Remove the file on the destination
			echo "I would now do $ rm $DESTINATION &"
			rm "$DESTINATION" &
			;;
		MOVED_TO* | CREATE* | ATTRIB* | MODIFY*)
			# Sync the new file/dir from the source to the destination
			# !! It is very important the the rsync call is done asynchronously
			# to avoid a case where new filesystem notifications aren't treated
			# because the script is still waiting for the call to return
			# Problems caused by this (disconnection might cause syncing to an empty mountpoint)
			# are far outweighted by benefits
			echo "I would now do \$ rsync $RSYNC_OPTIONS ""$SOURCE" "$DESTINATION"" &"
			rsync $RSYNC_OPTIONS "$SOURCE" "$DESTINATION" &
			;;
		*)
			:
			;;
		esac
		echo ""
	done
}

function unmount {
	for directory in "${DIRECT_DIRECTORIES[@]}"
	do
		echo "Unmounting $directory"
		fusermount -uz "$LOCAL_ROOT$directory"
	done
	for directory in "${SYNC_DIRECTORIES[@]}"
	do
		echo "Unmounting $directory"
		fusermount -uz "$SYNC_ROOT$directory"
	done
}

function get-destination {
	SOURCE=$1
	if [[ $SOURCE == $SYNC_ROOT* ]]
	then
		echo $SOURCE | sed "s#$SYNC_ROOT#$LOCAL_ROOT#g"
	elif [[ $SOURCE == $LOCAL_ROOT* ]]
	then
		echo $SOURCE | sed "s#$LOCAL_ROOT#$SYNC_ROOT#g"
	fi
}

trap "unmount; exit" SIGHUP SIGINT SIGTERM SIGKILL
read -s -p "Insert $REMOTE_USERNAME's password: " REMOTE_PASSWORD
echo ""
#mount-direct-dirs
#mount-sync-dirs
initial-sync
sync-watch
unmount

exit 0
