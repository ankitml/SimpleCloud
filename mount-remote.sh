#!/bin/bash
REMOTE_USERNAME="francisco"
LOCAL_ROOT="/home/francisco/"
SYNC_ROOT="/home/francisco/.Simplecloud/"
#REMOTE_ADDRESS="192.168.1.91"
REMOTE_ADDRESS="95.95.67.48"
REMOTE_CONTAINER="/mnt/things/"
DIRECT_DIRECTORIES=("Music" "Pictures" "Torrents" "Videos")
#SYNC_DIRECTORIES=("Documents" "Torrents")
SYNC_DIRECTORIES=("Torrents")
RSYNC_OPTIONS="-rltuv --progress --exclude=\".Trash*\""
SSHFS_OPTIONS="-o password_stdin -o allow_other -o reconnect -o ServerAliveInterval=60"
EXCLUDE_FROM_SYNC="( *.goutputstream-* | *.swp | *\~ )"

read -s -p "Insert $REMOTE_USERNAME's password: " REMOTE_PASSWORD
echo ""

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
	inotifywait -m -r -e create,delete,modify,attrib,move  --format "%T %e %w%f" --timefmt "%d/%m/%y %T" --exclude "$EXCLUDE_FROM_SYNC" $LOCAL_ROOT${SYNC_DIRECTORIES[*]} $SYNC_ROOT${SYNC_DIRECTORIES[*]} | while read FILE
	do
		#trap 'echo ola' INT
		output=($FILE)
		echo -e "Time: ${output[0]} ${output[1]}\nEvent: ${output[2]}\nFile: ${output[3]}"
		case ${output[2]} in
		MOVED_FROM* | DELETE*)
			SOURCE="${output[3]}"
			DESTINATION=$(get-destination $SOURCE)
			echo "I would now do $ rm $DESTINATION"
			;;
		MOVED_TO* | CREATE* | ATTRIB* | MODIFY*)
			#MOVED_TO2=${MOVED_TO##( "$LOCAL_ROOT" | "$SYNC_ROOT" )}
			#FILE=/home/user/src/prog.c
			#echo "/home/user/src/prog.c" | sed -e 's#\(/user\|/user/src\)#/root#g'
			#echo $MOVED_TO | sed "s#\($LOCAL_ROOT\|$SYNC_ROOT\)##g"
			#echo $MOVED_TO | sed "s#\($LOCAL_ROOT\|$SYNC_ROOT\)##g"
			SOURCE=${output[3]}
			DESTINATION=$(get-destination $SOURCE)
			echo "I would now do \$ rsync $RSYNC_OPTIONS $SOURCE $DESTINATION"
			;;
		*)
			:
			;;
		esac
		echo ""
	done
}

function unmount {
	for directory in "${DIRECT_DIRECTORES[@]}"
	do
		echo "Unmounting $directory"
		fusermount -uz /home/francisco/$directory
	done
	for directory in "${SYNC_DIRECTORES[@]}"
	do
		echo "Unmounting $directory-remote"
		fusermount -uz /home/francisco/."$directory"-remote
	done
}

function get-destination {
	SOURCE=$1
	if [[ $SOURCE == $LOCAL_ROOT* ]]
	then
		echo $SOURCE | sed "s#$LOCAL_ROOT#$SYNC_ROOT#g"
	elif [[ $MOVED_TO == $SYNC_ROOT* ]]
	then
		echo $SOURCE | sed "s#$SYNC_ROOT#$LOCAL_ROOT#g"
	fi
}

#mount-direct-dirs
#mount-sync-dirs
#sync-sleep
sync-watch
unmount
	
exit 0
