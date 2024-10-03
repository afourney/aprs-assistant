if [ ! -f repeaters.json ]; then
    echo "Downloading Repeater Data"
    curl -o repeaters.json https://hearham.com/api/repeaters/v1
fi

if [ ! -f repeaters.db ]; then
    echo "Creating sqlite database 'repeaters.db'"
    python create_db.py
    echo "Database 'repeaters.db' created. Copy this to the APRS Assistant ./data directory to enable repeater lookups." 
else
    read -p "repeaters.db already exists. Overwrite? " yn
    if [[ "$yn" =~ "y" ]]; then
    	echo "Backing up 'repeaters.db' to 'repeaters.bak'"
        mv repeaters.db repeaters.db.bak
    	echo "Overwriting sqlite database 'repeaters.db'"
    	python create_db.py
    	echo "Database 'repeaters.db' created. Copy this to the APRS Assistant ./data directory to enable license lookups." 
    fi
fi
