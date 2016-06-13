#!/bin/bash
REMOTE_USERNAME="francisco"
LOCAL_ROOT="/home/francisco/"
SYNC_ROOT="/home/francisco/.Simplecloud/"
REMOTE_ADDRESS="95.95.67.48"
REMOTE_CONTAINER="/mnt/things/"
DIRECT_DIRECTORIES=("Music" "Pictures" "Torrents" "Videos" "Comics")
SYNC_DIRECTORIES=("Documents")
RSYNC_OPTIONS="-rltuvP --progress --exclude=\".Trash*\""
SSHFS_OPTIONS="-o password_stdin -o allow_other -o reconnect -o ServerAliveInterval=60"
EXCLUDE_FROM_SYNC="( *.goutputstream-* | *.swp | *\~ )"

function mount-dirs {
	read -s -p "Insert $REMOTE_USERNAME's password: " REMOTE_PASSWORD
	echo ""
	
	for directory in "${DIRECT_DIRECTORIES[@]}"
	do
		DIR_PATH="$LOCAL_ROOT$directory"
		echo "Mounting $directory in $DIR_PATH"
		if [ ! -d "$DIR_PATH" ]
		then
			mkdir "$DIR_PATH"
		fi
		echo $REMOTE_PASSWORD | sshfs "$REMOTE_USERNAME"@"$REMOTE_ADDRESS":"$REMOTE_CONTAINER""$directory" "$DIR_PATH" $SSHFS_OPTIONS
		MOUNTSTATUS=${PIPESTATUS[1]}
		if [[ MOUNTSTATUS -ne 0 ]]
		then
			REMOTE_PASSWORD="kek"
			unmount
			exit 1
		fi
	done
	
	for directory in "${SYNC_DIRECTORIES[@]}"
	do
		DIR_PATH="$SYNC_ROOT$directory"
		echo "Mounting $directory in $DIR_PATH"
		if [ ! -d "$DIR_PATH" ]
		then
			mkdir "$DIR_PATH"
		fi
		echo $REMOTE_PASSWORD | sshfs "$REMOTE_USERNAME"@"$REMOTE_ADDRESS":"$REMOTE_CONTAINER""$directory" "$DIR_PATH" $SSHFS_OPTIONS
		MOUNTSTATUS=${PIPESTATUS[1]}
		if [[ MOUNTSTATUS -ne 0 ]]
		then
			REMOTE_PASSWORD="kek"
			unmount
			exit 1
		fi
	done
	REMOTE_PASSWORD="kek"
	echo "Finished mounting"
}

# Performs a two-way sync to make sure the server and
# the client have the same state. Only after this should
# the event syncs be called
# Time taken is heavily dependant on network quality
# Only AFTER this will any changes in sync directories
# be noticed and treated
function initial-sync {
	trap "return" SIGHUP SIGINT SIGTERM SIGKILL
	
	for directory in ${SYNC_DIRECTORIES[@]}
	do
		SOURCE="$SYNC_ROOT$directory/"
		DESTINATION=$(get-destination "$SOURCE")
		echo "I'm about to rsync $RSYNC_OPTIONS $SOURCE $DESTINATION"
		# Pull from server to local
		rsync $RSYNC_OPTIONS "$SOURCE" "$DESTINATION"
		# Push from local to server
		rsync $RSYNC_OPTIONS "$DESTINATION" "$SOURCE"
	done
	echo -e "\nFinished initial sync\n"
}

# Watches all the sync directories and their server
# counterparts. Every time a file is created, modified or
# deleted, it executes the corresponding code (removal or
# rsync)
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
		# Regex substitutions to obtain the complete path
		# of the file that caused the notification
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
			rm -rf "$DESTINATION" &
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

# Unmounts all the remote directories
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

# Swaps the segment of a file path between the
# local root and the sync root
# Ex: /home/user/Documents/test.txt => /home/user/.SimpleCloud/Documents/text.txt
# Where /home/user/ is the local root and /home/user/.SimpleCloud is the sync root
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

trap "REMOTE_PASSWORD="kek"; unmount; exit" SIGHUP SIGINT SIGTERM SIGKILL
mount-dirs
if [[ "$1" != "--no-sync" ]]
then 
	initial-sync
	sync-watch
else
	while true
	do
		sleep infinity &
		wait
	done
fi
unmount

exit 0
